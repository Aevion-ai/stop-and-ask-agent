"""One-screen authorization surface: the agent's entire authority transition is
VISIBLE — never buried in logs. Run: python server.py [port]"""
from __future__ import annotations

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from app.agent import StopAndAskFlow
from app.compliance_agent import ProfessionalComplianceFlow
from app.competition_twin import competition_twin
from app.receipts import ReceiptChain

ROOT = Path(__file__).resolve().parent
flow: StopAndAskFlow | None = None
compliance_flow: ProfessionalComplianceFlow | None = None
chain = ReceiptChain(ROOT / "data" / "strands_spike_001_receipts.jsonl")


class Handler(BaseHTTPRequestHandler):
    def _send(self, code: int, body: bytes, ctype: str = "application/json"):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self._send(200, (ROOT / "ui" / "index.html").read_bytes(), "text/html")
        elif self.path == "/state":
            snap = flow.snapshot() if flow else {"stage": "IDLE"}
            self._send(200, json.dumps(snap).encode())
        elif self.path == "/api/replay":
            active_chain = flow.chain if flow else chain
            ok, why = active_chain.verify()
            self._send(200, json.dumps({"ok": ok, "why": why}).encode())
        elif self.path == "/api/compliance/state":
            snap = compliance_flow.snapshot() if compliance_flow else {"stage": "IDLE"}
            self._send(200, json.dumps(snap).encode())
        elif self.path == "/api/compliance/replay":
            if compliance_flow and compliance_flow.chain:
                ok, why = compliance_flow.chain.verify()
            else:
                c = ReceiptChain(ROOT / "data" / "compliance_audit_receipts.jsonl")
                ok, why = c.verify()
            self._send(200, json.dumps({"ok": ok, "why": why}).encode())
        elif self.path == "/api/competition-twin":
            self._send(200, json.dumps(competition_twin()).encode())
        else:
            self._send(404, b'{"error":"not found"}')

    def do_POST(self):
        global flow, chain, compliance_flow
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length else b"{}"
        if self.path == "/start":
            flow = StopAndAskFlow()
            chain = flow.chain
            threading.Thread(target=flow.run, daemon=True).start()
            self._send(200, json.dumps({"started": True}).encode())
        elif self.path in ("/approve", "/deny") and flow:
            flow.human_decision = "APPROVE" if self.path == "/approve" else "DENY"
            flow.decision_event.set()
            self._send(200, json.dumps({"decision": flow.human_decision}).encode())
        elif self.path == "/api/compliance/start":
            compliance_flow = ProfessionalComplianceFlow()
            threading.Thread(target=compliance_flow.run, daemon=True).start()
            self._send(200, json.dumps({"started": True, "stage": "INGESTING_REQUIREMENTS"}).encode())
        elif self.path in ("/api/compliance/approve", "/api/compliance/deny") and compliance_flow:
            compliance_flow.human_decision = "APPROVE" if self.path == "/api/compliance/approve" else "DENY"
            compliance_flow.decision_event.set()
            self._send(200, json.dumps({"decision": compliance_flow.human_decision}).encode())
        else:
            self._send(404, b'{"error":"not found"}')

    def log_message(self, *a):  # quiet
        pass


if __name__ == "__main__":
    import sys
    import os
    port = int(os.environ.get("PORT", sys.argv[1] if len(sys.argv) > 1 else 8474))
    host = os.environ.get("HOST", "127.0.0.1")
    print(f"stop-and-ask agent on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
