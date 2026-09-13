"""Submission command acceptance: a judge can run a complete deny flow."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_demo_command_denies_then_verifies_replay(tmp_path):
    """Removing human denial or replay verification must make this fail."""
    result = subprocess.run(
        [
            sys.executable,
            "demo.py",
            "--decision",
            "deny",
            "--state-dir",
            str(tmp_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    evidence = json.loads(result.stdout)
    assert evidence["stage"] == "DENIED_BY_HUMAN"
    assert evidence["receipt"]["outcome"] == "DENIED_BY_HUMAN"
    assert evidence["receipt"]["tiny_verdict"]["verdict"] == "FAIL"
    assert evidence["replay"]["ok"] is True


def test_demo_command_creates_requested_evidence_directory(tmp_path):
    """Removing state-directory creation must make an otherwise valid run fail."""
    state_dir = tmp_path / "new" / "receipt-chain"
    result = subprocess.run(
        [sys.executable, "demo.py", "--decision", "deny", "--state-dir", str(state_dir)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=True,
    )

    assert json.loads(result.stdout)["replay"]["ok"] is True
    assert (state_dir / "strands_spike_001_receipts.jsonl").is_file()


def test_approved_flow_can_isolate_its_committed_artifact(tmp_path):
    """A caller-supplied output directory prevents a demo from touching repo output."""
    from app.agent import StopAndAskFlow

    state_dir = tmp_path / "receipts"
    output_dir = tmp_path / "generated-output"
    flow = StopAndAskFlow(state_dir=state_dir, output_dir=output_dir)
    flow.human_decision = "APPROVE"
    flow.decision_event.set()

    result = flow.run()
    assert result["stage"] == "RECEIPT_VERIFIED"
    assert (output_dir / "status.md").is_file()
