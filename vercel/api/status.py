"""GET /api/status — public dashboard data (counts only, NO secrets). NO Fly."""
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
    def _send(self, code, obj):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        try:
            usage.hit(len(body))
        except Exception:
            pass
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        now = time.time()
        if _CACHE["obj"] is not None and now - _CACHE["t"] < 30:
            return self._send(200, _CACHE["obj"])
        try:
            providers.cron_slice()
        except Exception:
            pass
        try:
            obj = providers.api_status()
        except Exception as e:
            if _CACHE["obj"] is not None:
                return self._send(200, _CACHE["obj"])
            return self._send(500, {"ok": False, "error": str(e)[:120]})
        _CACHE.update(t=now, obj=obj)
        return self._send(200, obj)

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()
