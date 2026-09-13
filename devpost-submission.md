# Title

TinyVerdicts: Bounded Authority for Strands Agents

## One-line Summary

TinyVerdicts is a Strands-compatible work agent primitive that acts inside standing authority,
stops at consequential boundaries and gives every proposed effect a signed
replayable Tiny Verdict: `PASS`, `FAIL` or `UNKNOWN`.

## Problem

Enterprise professionals spend hundreds of hours manually verifying AI agent outputs against regulatory frameworks (ISO/IEC 42001, EU AI Act, SOC 2, HIPAA) and customer contracts. While autonomous agents can rapidly ingest standards and draft filings, durable external actions—such as committing a regulatory filing, dispatching sensitive reports, or entering commercial commitments—must never execute solely on model discretion without human review and cryptographic auditability.

## Solution: Professional Compliance Agent on TinyVerdicts

We built an end-to-end **Professional Compliance Agent** powered by TinyVerdicts's deterministic safety boundary:
1. **Framework Ingestion**: Ingests enterprise contracts and regulatory standards (e.g., ISO/IEC 42001 & EU AI Act).
2. **Obligation Extraction**: Automatically parses discrete, testable obligations and evidentiary invariants (e.g., `OBL-42001-01` Container Provenance, `OBL-42001-02` Consequential Boundaries).
3. **Evidence Cross-Examination**: Cross-references internal workspace evidence (SHA-256 digests, test receipts, nociceptive logs) against each obligation.
4. **Gap Identification (Thorns)**: Isolates unverified claims as explicit `EVIDENCE_GAP` items requiring remediation rather than hallucinating compliance.
5. **Dossier Preparation**: Compiles an evidence-backed formal compliance dossier.
6. **TinyVerdicts Consequential Boundary**: When the agent attempts `COMMIT_COMPLIANCE_FILING`, TinyVerdicts's zero-write standing envelope halts execution with `REQUIRES_HUMAN`.
7. **Human Principal Ratification**: A human compliance officer reviews the dossier digest, verified evidence, and gap report, then clicks `APPROVE` or `DENY`.
8. **Ed25519 Signed Audit Trail**: On commitment, emits an immutable, SHA-256-linked Tiny Verdict receipt (`aevion.receipt.v1`) that replays and verifies independently.

TinyVerdicts is the foundational evidence and safety mechanism underneath a professional workflow that saves enterprise teams dozens of hours per audit. (VetProof, a separate veteran-benefits vertical, represents one eventual consumer of this primitive.)

## Why This Matters

The agent still removes the repetitive work, while the person keeps authority
over the moment that has a consequential effect. This is useful for consultants,
operators, makers, and small teams that need automated preparation without
unreviewed commitments.

## How We Used AI

The project uses the Strands Agents SDK dependency and a Strands agent path with
bounded `read_brief` and `request_commit` tools. The authority gate is
deterministic code: a model can propose work but cannot enlarge its own envelope
or commit beyond the effect ceiling. `AFH-P3-BEDROCK-002` now proves the live
path with Strands Agents 1.54.0 and Amazon Nova Micro through Bedrock in
`us-east-1`. The model proposed the work, the deterministic gate stopped at
`HUMAN_DECISION_REQUIRED`, the human denied the write and replay verified the
signed receipt.

## How We Used Codex

Codex helped implement the authority-envelope demo, adversarial acceptance
tests, canonical Tiny Verdict contract, receipt replay, judge-facing UI,
Competition Twin read-model, architecture, video plan, and this submission
packet. Every product claim in this draft is tied to a locally runnable path or
is explicitly labeled as pending.

## Key Features

- Standing authority envelope with zero unattended durable writes.
- Monotonic delegation: a child cannot acquire effects or ceilings absent from
  its parent.
- Tiny Verdict primitive with parent/delegated authority, proposed effect,
  observed-state hash, evidence references, policy identity, verdict, and human
  decision.
- `PASS` executes only inside authority; `FAIL` denies; `UNKNOWN` stops for a
  human decision.
- Ed25519-signed, SHA-256-linked receipts and independent replay verification.
- Empirical boundary evaluation (`TINY-VERDICTS-EVAL-001`): 70 deterministic execution cases across 10 behavioral categories, evaluated under direct and TinyVerdicts-gated conditions, plus 14 receipt-integrity checks covering tamper and chain-break detection. Under TinyVerdicts, the measured unauthorized-effect execution rate was 0.0 (0/42 unauthorized effects committed vs. 42/42 under direct access), boundary decision accuracy was 1.0, authorized completion rate was 1.0, human escalation precision was 1.0, false block rate was 0.0, tamper detection was 1.0, and replay verification was 1.0 with 100% Ed25519-signed receipt coverage.
- Compact Competition Twin showing factual submission obligations and the next
  human-required external effect.

## Architecture

The authority decision is deterministic code, separate from the effect layer:

```text
PROPOSE → TINY VERDICT → AUTHORIZE → EFFECT COMMIT → SIGNED RECEIPT → REPLAY
```

The detailed diagram is in `ARCHITECTURE.md` and `docs/architecture.svg`.

## Testing Instructions

```bash
python3 -m venv .venv
./.venv/bin/pip install -r requirements.txt
./.venv/bin/python -m pytest -q tests
./.venv/bin/python -m eval.tv_eval --output-dir eval/evidence
./.venv/bin/python demo.py --decision deny --state-dir /tmp/vetproof-demo
./.venv/bin/python server.py 8474
```

The test suite currently has 20 passing acceptance tests across authority gates, receipt chains, serverless entrypoints, and the end-to-end Professional Compliance Agent workflow (`tests/test_compliance_agent.py`). The evaluation command executes the 70-case benchmark and 14 integrity checks with signed receipts. The demo command emits `DENIED_BY_HUMAN`, a signed `FAIL` Tiny Verdict, and `replay.ok: true`. The local UI is at `http://127.0.0.1:8474` and exposes the Competition Twin at `/api/competition-twin`.

## Public Demo Link

TODO — no deployed judge-accessible URL has been evidenced. The local runnable
path above is available now.

## Public Repository Link

https://github.com/S-Leishman/stop-and-ask-agent

Verified publicly at commit `c7d6f1ac4b4e1c137ef6a6fa7a2a1106ffa00d97` on
2026-09-05 (first verified public at `d90674a0b815ab6a12bbfda9acf42881f3429bc7`,
2026-09-04).

## Demo Video

A 92-second demo and pitch is public at
https://youtu.be/1OWtgAbUzJY. The local source is
`demo_assets/TinyVerdicts_Agents_for_Humans_demo.mp4`; its SHA-256 is recorded in
`demo_assets/VIDEO_README.md`. The complete run-of-show is in `VIDEO_SKELETON.md` and
covers the problem, audience, working authority flow, human decision, signed
receipt, replay, and Competition Twin.

## Screenshot Shot List

1. TinyVerdicts UI at `HUMAN_DECISION_REQUIRED`, with proposed effect and Tiny
   Verdict `UNKNOWN` visible.
2. DENY result with signed receipt and replay verification.
3. Competition Twin showing local `PASS`, `FAIL`, and `UNKNOWN` submission
   gates plus `ATTACH_ARCHITECTURE_TO_DEVPOST` as the next human-required effect.
4. Architecture diagram showing authority and effect separation.

## Submission Readiness Notes

- Proposed track: **Professional Agents**.
- The project uses Strands Agents and is Apache-2.0 licensed locally.
- Required architecture file is prepared locally; Devpost accepts PNG/JPG/PDF/
  PPT/PPTX, so `docs/architecture.png` must be attached when the project is
  created.
- The public video URL is synchronized to the live Devpost project. Required
  submission answers still include country of residence, AWS Builder ID and
  the architecture attachment.
- The live Bedrock-backed run is proven. A public live demo remains optional.

## Known Limitations

- The offline demonstration remains the zero-cost reproduction path. The live
  Bedrock evidence is frozen under `eval/evidence/AFH-P3-BEDROCK-002.*`.
- Receipt signing uses an ephemeral Ed25519 key; it is not yet bound to a
  YubiKey/PIV identity.
- The current local UI is loopback-only and single-user.

## TODO Official Form Fields

| Devpost field | Value/status |
| --- | --- |
| Submitter Type (27729) | Individual — proposed; confirm before submission |
| Country of Residence (27730) | TODO: user-provided exact selection required |
| Organization (27731) | Leave blank unless entering on behalf of an organization |
| Track (27732) | Professional Agents — proposed |
| Public code repo (27733) | https://github.com/S-Leishman/stop-and-ask-agent |
| Architecture diagram (27734) | Attach `docs/architecture.png` when project exists |
| AWS Builder ID (27735) | scott.e.leishman@gmail.com |
| Live demo (27736) | Optional; TODO |
| Testing instructions (28191) | Use this document's Testing Instructions section |
| Builder.aws bonus post (27737) | Optional; TODO: publish `BUILDER_AWS_ARTICLE_DRAFT.md` |
