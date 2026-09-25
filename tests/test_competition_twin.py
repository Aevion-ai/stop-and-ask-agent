"""Competition Twin acceptance: expose shipping obligations, not a risk score."""
from __future__ import annotations

import json
import sys
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path
from urllib.request import urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app
from server import Handler


def test_competition_twin_exposes_real_submission_gates():
    """Removing an obligation or its authority boundary must fail this operational view."""
    twin = app.competition_twin()

    assert twin["schema"] == "aevion.competition-twin/v1"
    assert twin["competition"] == "Agents for Humans 2026"
    gates = {gate["id"]: gate for gate in twin["gates"]}
    assert gates["LOCAL_SUBMISSION_MATERIALS"]["verdict"] == "PASS"
    assert gates["ARCHITECTURE"]["verdict"] == "PASS"
    assert gates["PUBLIC_REPOSITORY"]["verdict"] == "PASS"
    assert gates["PUBLIC_REPOSITORY"]["detail"] == "https://github.com/S-Leishman/stop-and-ask-agent"
    assert gates["LIVE_BEDROCK_EXECUTION"]["verdict"] == "PASS"
    assert gates["LIVE_BEDROCK_EXECUTION"]["evidence"] == "eval/evidence/AFH-P3-BEDROCK-002.result.json"
    assert gates["VIDEO_RECORDING"]["verdict"] == "PASS"
    assert gates["VIDEO_RECORDING"]["evidence"] == "https://youtu.be/1OWtgAbUzJY"
    assert gates["DEVPOST_SUBMISSION"]["verdict"] == "UNKNOWN"
    assert twin["next_required_effect"]["effect"] == "VERIFY_DEVPOST_SUBMISSION"
    assert twin["next_required_effect"]["human_required"] is False


def test_ui_identifies_tinyverdicts_without_collapsing_vetproof():
    """Generic agent-control UI must not present VetProof as the product."""
    html = Path(__file__).resolve().parents[1].joinpath("ui", "index.html").read_text(encoding="utf-8")

    assert "TinyVerdicts — Bounded Authority" in html
    assert "VetProof is a separate veteran-specific vertical" in html
    assert "VetProof, powered by Tiny Verdicts" not in html


def test_competition_twin_is_available_as_a_read_only_api():
    """Removing the UI-facing endpoint must fail the observable product contract."""
    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        with urlopen(f"http://127.0.0.1:{httpd.server_port}/api/competition-twin") as response:
            twin = json.loads(response.read())
        assert twin["schema"] == "aevion.competition-twin/v1"
    finally:
        httpd.shutdown()
        thread.join()
