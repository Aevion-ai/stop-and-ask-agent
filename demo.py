"""One-command, offline evidence run for the Stop-and-Ask submission."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.agent import StopAndAskFlow


def main() -> None:
    parser = argparse.ArgumentParser(description="Run one Tiny Verdict demo flow.")
    parser.add_argument("--decision", choices=("approve", "deny"), required=True)
    parser.add_argument("--state-dir", type=Path, default=Path("data/demo-run"))
    args = parser.parse_args()

    args.state_dir.mkdir(parents=True, exist_ok=True)
    flow = StopAndAskFlow(state_dir=args.state_dir, output_dir=args.state_dir / "output")
    flow.human_decision = args.decision.upper()
    flow.decision_event.set()
    evidence = flow.run()
    ok, why = flow.chain.verify()
    evidence["replay"] = {"ok": ok, "why": why}
    print(json.dumps(evidence, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
