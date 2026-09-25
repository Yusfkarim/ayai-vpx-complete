"""GET /v1/models — OpenAI-compatible model list. NO Fly."""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import providers
import usage

_CACHE = {"t": 0.0, "obj": None}

_CACHE = {"t": 0.0, "obj": None}


class handler(BaseHTTPRequestHandler):
    def _cors(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")

    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        try:
            usage.hit(len(body))
        except Exception:
            pass
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._cors()
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        now = time.time()
        if _CACHE["obj"] is not None and now - _CACHE["t"] < 60:
            return self._send(200, _CACHE["obj"])
        try:
            providers.cron_slice()
        except Exception:
            pass
        try:
            cat = providers.full_catalog()
        except Exception:
            cat = []
        if not cat:
            if _CACHE["obj"] is not None:
                return self._send(200, _CACHE["obj"])
            cat = [{"id": "pol-openai"}, {"id": "lr-nano"}]
        data = [{"id": it["id"], "object": "model", "owned_by": "vpx",
                 "name": it.get("name") or it["id"]} for it in cat]
        obj = {"object": "list", "data": data}
        if len(data) > 2:
            _CACHE.update(t=now, obj=obj)
        return self._send(200, obj)

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()
