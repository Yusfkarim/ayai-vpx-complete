"""POST /api/play — playground chat proxy (key + rate limited). NO Fly."""
import json
import os
import sys
import time
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import providers
import usage
import kb
import manhaj


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
        try:
            providers.cron_slice()
        except Exception:
            pass
        if providers._ip_blocked(providers._sec_ip(self)):
            return self._send(429, {"error": "blocked"})
        try:
            ln = int(self.headers.get("Content-Length") or 0)
        except Exception:
            ln = 0
        if ln > 60000:
            return self._send(413, {"error": "payload too large"})
        try:
            data = json.loads(self.rfile.read(ln) or b"{}")
        except Exception:
            return self._send(400, {"error": "bad json"})
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
            if not providers.rl_check("play:" + ip, 30, 60):
                return self._send(429, {"error": "rate limited (30/min)"})
        else:
            if not providers.rl_check("playfree:" + ip, 6, 60):
                return self._send(429, {"error": "rate limited - add API key for more (6/min free)"})
        model = str(data.get("model") or "pol-openai")[:80]
        messages = data.get("messages") or []
        if not messages or len(messages) > 20:
            return self._send(400, {"error": "messages 1..20 required"})
        if not _vip and len(messages) > 6:
            return self._send(400, {"error": "free tier: max 6 messages (add API key for more)"})
        clean = []
        for m in messages[-20:]:
            if not isinstance(m, dict):
                continue
            r = str(m.get("role") or "user")[:20]
            c = str(m.get("content") or "")[:6000]
            if c:
                clean.append({"role": r, "content": c})
        if not clean:
            return self._send(400, {"error": "empty messages"})
        _GEMINI_RAW = "gemini" in model.lower()  # #129: playground gemini = user's prompt ONLY (no kb/manhaj merge); API unchanged
        if not _GEMINI_RAW:
            try:
                _hist = [m for m in clean if m.get("role") in ("user", "assistant")][-3:]
                _qtext = " ".join(str(m.get("content") or "") for m in _hist)
                _hits = kb.search(_qtext) if kb.detect(_qtext) else []
                if _hits:
                    clean = [{"role": "system", "content": kb.prompt(_hits)}] + clean
            except Exception:
                pass
            try:
                _mh = [m for m in clean if isinstance(m, dict) and m.get("role") in ("user", "assistant")][-3:]
                _mtext = " ".join(str(m.get("content") or "") for m in _mh)
                clean = [{"role": "system", "content": manhaj.prompt(_mtext)}] + clean
            except Exception:
                pass
        t0 = time.time()
        try:
            if data.get("direct"):
                text = providers.chat_once(model, clean, timeout=55)
                used = model
            else:
                text, used = providers.chat(model, clean, timeout=240)
        except Exception as e:
            return self._send(502, {"error": str(e)[:200]})
        return self._send(200, {"text": text, "used": used,
                                "seconds": round(time.time() - t0, 1)})

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", "0")
        self.end_headers()
