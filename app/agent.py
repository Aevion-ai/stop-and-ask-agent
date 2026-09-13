"""The Stop-and-Ask agent: does bounded work autonomously, stops at the effect
ceiling, asks the human, commits only on approval, receipts everything.

Strands SDK is used when a model provider is configured (AEVION_MODEL=bedrock +
AWS creds). Without credentials the same tool flow runs in scripted mode so the
demo needs no keys; the authority path, receipts, and replay are identical.
"""
from __future__ import annotations

import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from .authority import AuthorityContract, AuthorityGate, Decision
from .receipts import ReceiptChain, canonical, sha

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "output"


def runtime_state_root() -> Path:
    """Return the writable root for a deployed demo, preserving local defaults."""
    if os.environ.get("VERCEL"):
        return Path(os.environ.get("AEVION_STATE_DIR", "/tmp/vetproof"))
    return ROOT


class StopAndAskFlow:
    """One demo run: six visible stages, blocking at the human boundary."""

    def __init__(self, state_dir: Path | None = None, output_dir: Path | None = None):
        runtime_root = runtime_state_root()
        default_receipts = runtime_root / "receipts" if os.environ.get("VERCEL") else ROOT / "data"
        self.state_dir = state_dir or default_receipts
        self.output_dir = Path(output_dir) if output_dir is not None else runtime_root / "output"
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.chain = ReceiptChain(self.state_dir / "strands_spike_001_receipts.jsonl")
        self.parent = AuthorityContract(
            principal="human:scott",
            allowed_effects=frozenset({"READ_WORKSPACE", "DRAFT_OUTPUT", "COMMIT_OUTPUT"}),
            max_writes=0,          # standing envelope: ZERO unattended durable writes
            spend_ceiling=0.0,
            delegation_rights=False,
        )
        self.child = self.parent.derive_child(frozenset({"READ_WORKSPACE", "DRAFT_OUTPUT"}))  # agent holds a NARROWER envelope: no write right at all
        self.gate = AuthorityGate(self.child)
        self.stage = "IDLE"
        self.detail: dict = {}
        self.decision_event = threading.Event()
        self.human_decision: str | None = None
        self.lock = threading.Lock()

    # -- visible state for the one-screen UI --------------------------------
    def snapshot(self) -> dict:
        with self.lock:
            return {"stage": self.stage, **self.detail}

    def _set(self, stage: str, **detail):
        with self.lock:
            self.stage = stage
            self.detail = detail

    @staticmethod
    def _artifact_label(path: Path) -> str:
        """Use a stable label when a caller isolates output outside this checkout."""
        try:
            return str(path.relative_to(ROOT))
        except ValueError:
            return f"caller-output/{path.name}"

    @staticmethod
    def _authority_ref(contract: AuthorityContract) -> dict:
        return {
            "principal": contract.principal,
            "allowed_effects": sorted(contract.allowed_effects),
            "max_writes": contract.max_writes,
            "delegation_rights": contract.delegation_rights,
        }

    def _tiny_verdict(self, proposed: dict, verdict: str, state: str,
                      decision: str = "PENDING") -> dict:
        """One inspectable decision at one consequential boundary."""
        observed_state = {
            "class": state,
            "writes_consumed": self.gate.writes_consumed,
            "effect_ceiling": self.child.max_writes,
        }
        evidence_refs = [{
            "kind": "task_brief",
            "path": "data/task_brief.txt",
            "sha256": sha((DATA / "task_brief.txt").read_bytes()),
        }]
        body = {
            "schema": "aevion.tiny-verdict/v1",
            "subject": self.child.principal,
            "parent_authority": self._authority_ref(self.parent),
            "delegated_authority": self._authority_ref(self.child),
            "proposed_effect": proposed,
            "observed_state": observed_state,
            "observed_state_hash": sha(canonical(observed_state)),
            "evidence_refs": evidence_refs,
            "policy_id": "STRANDS-SPIKE-001/authority-gate",
            "policy_version": "STRANDS-SPIKE-001/authority-gate-v1",
            "verdict": verdict,
            "human_required": verdict == "UNKNOWN",
            "human_authority_requirement": verdict == "UNKNOWN",
            "decision": decision,
        }
        return {"tiny_verdict_id": f"tv_{sha(canonical(body))[:16]}", **body}

    # -- the flow ------------------------------------------------------------
    def run(self) -> dict:
        try:
            self._run()
        except Exception as exc:  # surface any failure into the visible state
            self._set("ERROR", error=repr(exc))
            raise
        return self.snapshot()

    def _run(self):
        brief_path = DATA / "task_brief.txt"

        # 1. PROPOSED ACTION — the agent reads its brief (inside envelope).
        self._set("PROPOSED_ACTION", action=f"read brief and draft weekly status output ({brief_path.name})",
                  principal=self.child.principal)
        brief = brief_path.read_text(encoding="utf-8")
        decision = self.gate.check("READ_WORKSPACE")
        assert decision is Decision.ALLOWED

        # 2. POLICY / AUTHORITY CHECK — drafting happens autonomously.
        self._set("POLICY_CHECKED", check="READ_WORKSPACE inside standing envelope -> ALLOWED",
                  draft_len=len(brief) + 64)
        draft = f"# Status Output\n\nsource: {brief_path.name} (sha256 {sha(brief.encode())[:16]}...)\n\n{brief.strip()}\n"
        decision = self.gate.check("DRAFT_OUTPUT")
        assert decision is Decision.ALLOWED

        # 3. EFFECT CEILING — the consequential boundary: durable write.
        proposed = {"effect": "COMMIT_OUTPUT", "path": "output/status.md", "bytes": len(draft.encode())}
        decision = self.gate.check("COMMIT_OUTPUT")
        if decision is not Decision.ALLOWED:
            tiny_verdict = self._tiny_verdict(proposed, "UNKNOWN", "EFFECT_CEILING_REACHED")
            self._set("EFFECT_CEILING_REACHED", proposed=proposed,
                      ceiling=f"max_writes={self.child.max_writes} (agent envelope carries no write right)",
                      gate_decision=decision.value, tiny_verdict=tiny_verdict)

            # 4. HUMAN DECISION REQUIRED — stop and ask.
            self._set("HUMAN_DECISION_REQUIRED", proposed=proposed,
                      ask="Commit the drafted output? This is outside the agent's standing envelope.",
                      tiny_verdict=tiny_verdict)
            self.decision_event.wait()
            if self.human_decision != "APPROVE":
                receipt = self.chain.append({
                    "action": "COMMIT_OUTPUT", "outcome": "DENIED_BY_HUMAN",
                    "proposed_by": "agent:stop-and-ask", "decided_by": "human:scott",
                    "proposed": proposed, "decision": self.human_decision,
                    "tiny_verdict": self._tiny_verdict(
                        proposed, "FAIL", "DENIED_BY_HUMAN", self.human_decision or "DENY"),
                    "ts": datetime.now(timezone.utc).isoformat()})
                self._set("DENIED_BY_HUMAN", receipt=receipt)
                return receipt

        # 5. EFFECT COMMITTED — only after explicit human authorization.
        self.output_dir.mkdir(parents=True, exist_ok=True)
        out_path = self.output_dir / "status.md"
        out_path.write_text(draft, encoding="utf-8")
        self._set("EFFECT_COMMITTED", wrote=self._artifact_label(out_path),
                  bytes=len(draft.encode()))

        # 6. RECEIPT SIGNED + REPLAY VERIFIED.
        receipt = self.chain.append({
            "action": "COMMIT_OUTPUT", "outcome": "COMMITTED_AFTER_HUMAN_APPROVAL",
            "proposed_by": "agent:stop-and-ask", "decided_by": "human:scott",
            "artifact": self._artifact_label(out_path), "artifact_sha256": sha(out_path.read_bytes()),
            "tiny_verdict": self._tiny_verdict(
                proposed, "PASS", "COMMITTED_AFTER_HUMAN_APPROVAL", "APPROVE"),
            "ts": datetime.now(timezone.utc).isoformat()})
        ok, why = self.chain.verify()
        self._set("RECEIPT_VERIFIED", receipt=receipt, replay={"ok": ok, "why": why})
        return self.snapshot()


# --- Strands SDK wiring ------------------------------------------------------
def strands_agent_flow(flow: StopAndAskFlow) -> dict:
    """LLM mode: same tools exposed through a strands.Agent.

    Requires AWS credentials (Bedrock). Falls back to the deterministic flow
    when unset so the demo never hard-fails on a missing key.
    """
    if os.environ.get("AEVION_MODEL") != "bedrock":
        return flow.run()
    try:
        from strands import Agent, tool  # noqa: F401  (strands-agents package)
        from strands.models import BedrockModel
    except ImportError:
        return flow.run()

    @tool
    def read_brief() -> str:
        "Read the task brief (inside the standing envelope)."
        return (DATA / "task_brief.txt").read_text(encoding="utf-8")

    @tool
    def request_commit(summary: str) -> str:
        "Request human authorization to commit the drafted output (outside the envelope)."
        flow._set("HUMAN_DECISION_REQUIRED", proposed={"effect": "COMMIT_OUTPUT"},
                  ask=summary)
        flow.decision_event.wait()
        return flow.human_decision or "NO_DECISION"

    model = BedrockModel(model_id="amazon.nova-micro-v1:0")
    agent = Agent(model=model, tools=[read_brief, request_commit],
                  system_prompt="You are a bounded agent. Do the in-envelope work. "
                                "When the work needs a durable write, you MUST call "
                                "request_commit and wait for the human.")
    agent(str("Read the brief with read_brief, draft the weekly status, then call "
              "request_commit to ask the human before anything is written."))
    return flow.snapshot()
