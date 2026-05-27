#!/usr/bin/env python3
"""Tiny local HTTP service: POST /kanban/create → hermes kanban create.
Listens on 127.0.0.1:9120 only (not LAN-accessible)."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json, subprocess, os, sys

HERMES = os.path.expanduser("~/.local/bin/hermes")

class Handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(length)) if length else {}
            title     = body.get("title", "SpaceShipIO Error")
            task_body = body.get("body", "")
            idem_key  = body.get("idempotencyKey", "")

            args = [HERMES, "kanban", "create", title,
                    "--body", task_body,
                    "--assignee", "default",
                    "--workspace", "scratch",
                    "--json"]
            if idem_key:
                args += ["--idempotency-key", idem_key]

            r = subprocess.run(args, capture_output=True, text=True, timeout=30)
            result = r.stdout.strip() or r.stderr.strip()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(result.encode())
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def log_message(self, fmt, *args):
        pass  # silent

if __name__ == "__main__":
    server = HTTPServer(("127.0.0.1", 9120), Handler)
    print("Kanban service listening on 127.0.0.1:9120", flush=True)
    server.serve_forever()
