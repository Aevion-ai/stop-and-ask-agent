from datetime import datetime, timedelta, timezone

from app.competition_twin import evaluate_external_gate

NOW = datetime(2026, 10, 24, tzinfo=timezone.utc)
HASH = "a" * 64


def valid_record():
    return {
        "verified": True,
        "verdict": "PASS",
        "evidence_sha256": HASH,
        "artifact_sha256": HASH,
        "attested_at": "2026-10-23T00:00:00Z",
    }


def evaluate(record):
    return evaluate_external_gate("TEST", record, "detail", "evidence", now=NOW)


def test_missing_evidence_is_unknown():
    assert evaluate(None)["verdict"] == "UNKNOWN"


def test_field_presence_does_not_pass():
    assert evaluate({"verdict": "PASS"})["verdict"] == "UNKNOWN"


def test_stale_attestation_is_unknown():
    record = valid_record()
    record["attested_at"] = (NOW - timedelta(days=31)).isoformat()
    assert evaluate(record)["verdict"] == "UNKNOWN"


def test_hash_mismatch_fails():
    record = valid_record()
    record["artifact_sha256"] = "b" * 64
    assert evaluate(record)["verdict"] == "FAIL"


def test_valid_attestation_can_pass():
    assert evaluate(valid_record())["verdict"] == "PASS"


def test_verified_failure_remains_failure():
    record = valid_record()
    record["verdict"] = "FAIL"
    assert evaluate(record)["verdict"] == "FAIL"
