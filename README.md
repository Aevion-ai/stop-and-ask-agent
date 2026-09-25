# TinyVerdicts: Bounded Authority for Strands Agents

## Stop-and-Ask Agent: Autonomous Until Authority Matters

[📄 Systems Paper (PDF)](paper/stop-and-ask-agents.pdf) | [📦 arXiv Source Package](paper/arxiv_submission.zip) | [📊 Evaluation (TINY-VERDICTS-EVAL-001)](eval/evidence/) | [🛡️ Receipt Verifier Action](https://github.com/Aevion-ai/receipt-verifier)

**The problem.** AI agents that do real work make real changes to real systems.
The dangerous moment is not the work. It is the write that nobody explicitly
authorized. Most demos hide that moment in a log line. So this leads us to ask
how an agent can keep working while authority remains visible and controlled.

**Who it is for.** Professionals who need an agent to keep working while they
are not watching and who need proof of what the agent was allowed to do, what it
did and which human decided the parts that mattered.

**What it does.** The agent runs inside a standing authority envelope that
carries **zero** unattended durable writes. It reads its brief, drafts the work
and when it reaches the effect ceiling it stops. The screen shows the proposed
action, the authority check, the ceiling and the decision. A human selects
APPROVE or DENY. Every decision lands in an Ed25519-signed, sha256-linked
append-only receipt chain. Change one byte and verification fails.

```
PROPOSED ACTION → POLICY / AUTHORITY CHECK → EFFECT CEILING
      → HUMAN DECISION REQUIRED → (APPROVE) → EFFECT COMMITTED
      → SIGNED RECEIPT → REPLAY VERIFIED        (or) → DENIED BY HUMAN
```

**Architecture.**

The renderable architecture diagram is in [ARCHITECTURE.md](ARCHITECTURE.md).

```text
human principal (you)
      │  grants standing envelope (frozen contract, zero unattended writes)
      ▼
child agent envelope  ── monotonic narrowing: child ⊆ parent, ceilings only shrink
      │
Strands agent (tools: read_brief, request_commit)
      │  in-envelope work runs autonomously
      ▼
AuthorityGate (deterministic code, not the model)
      │  effect ceiling reached → REQUIRES_HUMAN
      ▼
one-screen decision (APPROVE / DENY)
      ▼
receipt chain (Ed25519-signed, sha256-linked) ── replay verification
```

The authority decision is deterministic code. The model proposes, regardless of
which model is used, but it never grants itself permission.

## An aviation and ATC analogy

The design uses a familiar operational question. In air traffic control a
request is not the same thing as a clearance and a clearance is not the same
thing as an observed result. The same separation is useful for an AI agent:

```text
request → authority check → clearance → execution → observation → readback
```

This is an analogy to control procedures, not a claim that TinyVerdicts is an FAA
system. The existing Aviation Membranes work provides a useful SHELL-style way
to classify failures. A software or model mismatch is different from a human
communication problem and both are different from an environmental state
change. The receipt records which surface failed so a reviewer can correct the
right part of the workflow.

The aviation framing helps explain why a Tiny Verdict is more than a risk
score. It is the recorded answer to a narrow operational question: may this
principal perform this exact effect against this state now?

## Tiny Verdict

A Tiny Verdict is the inspectable decision object emitted at one consequential
boundary: subject, authority envelope, exact proposed effect, observed state,
policy version, verdict (`PASS`, `FAIL`, or `UNKNOWN`), and whether a human
decision is required. It is stored inside the signed receipt rather than hidden
in a dashboard aggregate.

The canonical object also carries parent and delegated authority, a hash of the
observed state, evidence references, policy identity, and the final human
decision. The signed receipt envelope supplies the signer, receipt hash,
previous-receipt hash, timestamp, and replay result; keeping the receipt hash
outside its own signed body avoids a circular claim.

## Competition Twin

The same local UI includes a compact Competition Twin: actual submission gates,
their `PASS` / `FAIL` / `UNKNOWN` states, and the next required external
effect. It is a read-model of local evidence, not a claimed public deployment.
The read-only payload is available at `/api/competition-twin`.

## Run it

```bash
python3 -m venv .venv && ./.venv/bin/pip install -r requirements.txt
./.venv/bin/python server.py 8474
# open http://127.0.0.1:8474 and click RUN AGENT
```

Tests (no keys, no network):

```bash
./.venv/bin/python -m pytest tests -q
```

Deterministic evaluation and benchmark (no keys, no network):

```bash
./.venv/bin/python -m eval.tv_eval --output-dir eval/evidence
# TINY-VERDICTS-EVAL-001 contains 70 deterministic execution cases across 10 behavioral categories, evaluated under direct and TinyVerdicts-gated conditions, plus 14 receipt-integrity checks covering tamper and chain-break detection.
# Full empirical comparison and signed receipt chains in eval/evidence/.
```

One-command evidence run (no keys, no network):

```bash
./.venv/bin/python demo.py --decision deny --state-dir /tmp/tinyverdicts-demo
# emits a FAIL Tiny Verdict, Ed25519-signed receipt, and replay: {"ok": true}
```

Use `--decision approve` to demonstrate the explicit-approval branch. That
branch creates `output/status.md`; run it in a disposable working copy when
recording a demo.

Optional LLM mode (AWS credentials with Bedrock access required):

```bash
AEVION_MODEL=bedrock ./.venv/bin/python server.py
```

## Known limitations (honest list)

- Receipts are signed with an ephemeral Ed25519 key and embed its public key
  for independent replay. They are not yet bound to a persistent PIV/YubiKey
  identity, so the demo does not claim cryptographic non-repudiation of the
  human's identity.
- The demo task is deliberately small (one read, one draft, one bounded write).
- LLM mode requires AWS credentials; scripted mode runs the identical
  authority/receipt path offline.
- Single-user, loopback only. No multi-tenant anything.

## Cloudflare Container deployment

The repository includes a Cloudflare Container wrapper under `cloudflare/`.
It runs the unchanged Python service on port 8080 and routes the Worker to one
container instance. From this directory, after Docker and Wrangler access are
available:

```bash
npx wrangler@4.129.0 login
npx wrangler@4.129.0 deploy --config cloudflare/wrangler.jsonc
```

Wrangler builds the image from `Dockerfile`; the container requires a Linux
`amd64` build. Local scripted mode remains the credential-free fallback.

## License

Apache-2.0
