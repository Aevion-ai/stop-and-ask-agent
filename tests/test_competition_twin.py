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
    """Local artifacts pass; unverified external claims fail closed to UNKNOWN."""
    twin = app.competition_twin()

    assert twin["schema"] == "aevion.competition-twin/v1"
    assert twin["competition"] == "Agents for Humans 2026"
    gates = {gate["id"]: gate for gate in twin["gates"]}
    assert gates["SUBMISSION_SKELETON"]["verdict"] == "PASS"
    assert gates["ARCHITECTURE"]["verdict"] == "PASS"
    assert gates["PUBLIC_REPOSITORY"]["verdict"] == "UNKNOWN"
    assert gates["PUBLIC_REPOSITORY"]["detail"] == "https://github.com/S-Leishman/stop-and-ask-agent"
    assert gates["LIVE_BEDROCK_EXECUTION"]["verdict"] == "UNKNOWN"
    assert gates["LIVE_BEDROCK_EXECUTION"]["evidence"] == "eval/evidence/AFH-P3-BEDROCK-002.result.json"
    assert gates["VIDEO_RECORDING"]["verdict"] == "UNKNOWN"
    assert gates["VIDEO_RECORDING"]["evidence"] == "eval/external-gates.json#VIDEO_RECORDING"
    assert twin["next_required_effect"]["effect"] == "ATTACH_ARCHITECTURE_TO_DEVPOST"
    assert twin["next_required_effect"]["human_required"] is True


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
