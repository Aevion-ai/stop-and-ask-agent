"""A compact operational view of the competition's real submission gates."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parent.parent
SKELETON = ROOT / "SUBMISSION_SKELETON.md"
EXTERNAL_EVIDENCE = ROOT / "eval" / "external-gates.json"
PUBLIC_REPOSITORY_URL = "https://github.com/S-Leishman/stop-and-ask-agent"
PUBLIC_VIDEO_URL = "https://youtu.be/1OWtgAbUzJY"
SHA256_RX = re.compile(r"^[0-9a-f]{64}$")


def _gate(identifier: str, verdict: str, detail: str, evidence: str) -> dict:
    return {"id": identifier, "verdict": verdict, "detail": detail, "evidence": evidence}


def evaluate_external_gate(
    identifier: str,
    record: dict | None,
    detail: str,
    evidence: str,
    *,
    now: datetime | None = None,
    max_age: timedelta = timedelta(days=30),
) -> dict:
    """Evaluate a bounded attestation; absence or invalid evidence never passes."""
    current = datetime.now(timezone.utc) if now is None else now
    unknown = lambda reason: _gate(identifier, "UNKNOWN", reason, evidence)
    if not isinstance(record, dict):
        return unknown("no external attestation supplied")
    if record.get("verified") is not True:
        return unknown("attestation is not independently verified")
    verdict = record.get("verdict")
    if verdict not in {"PASS", "FAIL"}:
        return unknown("attestation has no decisive verdict")
    evidence_hash = record.get("evidence_sha256")
    artifact_hash = record.get("artifact_sha256")
    if not isinstance(evidence_hash, str) or not SHA256_RX.fullmatch(evidence_hash):
        return unknown("evidence hash is missing or malformed")
    if not isinstance(artifact_hash, str) or not SHA256_RX.fullmatch(artifact_hash):
        return unknown("artifact hash is missing or malformed")
    if evidence_hash != artifact_hash:
        return _gate(identifier, "FAIL", "evidence and artifact hashes disagree", evidence)
    try:
        attested_at = datetime.fromisoformat(record["attested_at"].replace("Z", "+00:00"))
    except (KeyError, TypeError, ValueError):
        return unknown("attestation timestamp is missing or malformed")
    if attested_at.tzinfo is None:
        return unknown("attestation timestamp lacks a timezone")
    attested_at = attested_at.astimezone(timezone.utc)
    if attested_at > current:
        return _gate(identifier, "FAIL", "attestation timestamp is in the future", evidence)
    if current - attested_at > max_age:
        return unknown("attestation is stale")
    return _gate(identifier, verdict, detail, evidence)


def _external_records() -> dict:
    try:
        records = json.loads(EXTERNAL_EVIDENCE.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return records if isinstance(records, dict) else {}


def competition_twin() -> dict:
    """Return operational submission truth; external claims fail closed to UNKNOWN."""
    records = _external_records()
    return {
        "schema": "aevion.competition-twin/v1",
        "competition": "Agents for Humans 2026",
        "deadline": "2026-09-14T17:00:00-07:00",
        "gates": [
            _gate(
                "SUBMISSION_SKELETON",
                "PASS" if SKELETON.is_file() else "FAIL",
                "submission contract is locally present" if SKELETON.is_file() else "submission contract missing",
                str(SKELETON),
            ),
            _gate(
                "ARCHITECTURE",
                "PASS" if (ROOT / "ARCHITECTURE.md").is_file() else "FAIL",
                "renderable architecture exists" if (ROOT / "ARCHITECTURE.md").is_file() else "architecture missing",
                "ARCHITECTURE.md",
            ),
            evaluate_external_gate(
                "PUBLIC_REPOSITORY", records.get("PUBLIC_REPOSITORY"),
                PUBLIC_REPOSITORY_URL, "eval/external-gates.json#PUBLIC_REPOSITORY",
            ),
            evaluate_external_gate(
                "LIVE_BEDROCK_EXECUTION", records.get("LIVE_BEDROCK_EXECUTION"),
                "externally attested Bedrock execution and receipt replay",
                "eval/evidence/AFH-P3-BEDROCK-002.result.json",
            ),
            evaluate_external_gate(
                "VIDEO_RECORDING", records.get("VIDEO_RECORDING"),
                "public video availability externally attested",
                "eval/external-gates.json#VIDEO_RECORDING",
            ),
            _gate(
                "DEVPOST_SHELL",
                "PASS" if (ROOT / "DEVPOST_ENTRY.md").is_file() else "FAIL",
                "local Devpost fields are drafted" if (ROOT / "DEVPOST_ENTRY.md").is_file() else "Devpost shell missing",
                "DEVPOST_ENTRY.md",
            ),
        ],
        "next_required_effect": {
            "effect": "ATTACH_ARCHITECTURE_TO_DEVPOST",
            "verdict": "UNKNOWN",
            "human_required": True,
            "reason": "the architecture asset exists and must be attached to the required Devpost field",
        },
    }
