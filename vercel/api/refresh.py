"""POST /api/refresh — fetch newest models (sync + cache clear). Key protected. NO Fly."""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import providers
import usage


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

    def do_POST(self):
        if providers._ip_blocked(providers._sec_ip(self)):
            return self._send(429, {'error': 'blocked'})
        try:
            ln = int(self.headers.get("Content-Length") or 0)
        except Exception:
            ln = 0
        try:
            data = json.loads(self.rfile.read(min(ln, 2000)) or b"{}")
        except Exception:
            data = {}
        _k = data.get("key") or ""
        _vip = bool(providers.API_KEY and _k and _k == providers.API_KEY)
        if _k and not _vip:
            try:
                providers._note_badkey((self.headers.get("X-Forwarded-For") or "?").split(",")[0].strip()[:40])
            except Exception:
                pass
            return self._send(401, {"error": "bad api key"})
        ip = (self.headers.get("X-Forwarded-For") or "?").split(",")[0].strip()[:40]
        if _vip:
            if not providers.rl_check("refresh:" + ip, 3, 300):
                return self._send(429, {"error": "rate limited (3 per 5min)"})
        else:
            if not providers.rl_check("refreshfree:" + ip, 1, 600):
                return self._send(429, {"error": "rate limited (1 per 10min free)"})
        t0 = time.time()
        try:
            sync = providers.sync_all(budget_s=150)
        except Exception as e:
            return self._send(502, {"error": str(e)[:150]})
        try:
            n = len(providers.full_catalog())
        except Exception:
            n = 0
        try:
            providers.kv.gist_flush(force=True)
        except Exception:
            pass
        ok = sum(1 for v in sync.values() if (v or {}).get("ok"))
        return self._send(200, {"ok": True, "sync_ok": ok, "sync_total": len(sync),
                                "models": n, "seconds": round(time.time() - t0, 1),
                                "detail": sync})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()
