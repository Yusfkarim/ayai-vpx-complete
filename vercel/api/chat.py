"""POST /v1/chat/completions — OpenAI-compatible chat. NO Fly."""
import json
import os
import random
import sys
import time
from http.server import BaseHTTPRequestHandler

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import providers
import usage
import kb
import manhaj


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

    def _auth(self):
        want = providers.API_KEY
        if not want:
            return True
        got = (self.headers.get("Authorization") or "").strip()
        return got == "Bearer " + want

    def do_POST(self):
        try:
            providers.cron_slice()
        except Exception:
            pass
        _ip = providers._sec_ip(self)
        if providers._ip_blocked(_ip):
            return self._send(429, {"error": {"message": "blocked", "type": "blocked"}})
        if not self._auth():
            providers._note_badkey(_ip)
            return self._send(401, {"error": {"message": "invalid API key", "type": "auth"}})
        try:
            ln = int(self.headers.get("Content-Length") or 0)
        except Exception:
            ln = 0
        try:
            data = json.loads(self.rfile.read(ln) or b"{}")
        except Exception:
            return self._send(400, {"error": {"message": "bad json", "type": "invalid_request"}})
        _stream = bool(data.get("stream"))
        _ip = (self.headers.get("X-Forwarded-For") or "?").split(",")[0].strip()[:40]
        if not providers.rl_check("chat:" + _ip, 30, 60):
            return self._send(429, {"error": {"message": "rate limited (30/min)", "type": "rate"}})
        model = data.get("model") or "pol-openai"
        messages = data.get("messages") or []
        if not messages:
            return self._send(400, {"error": {"message": "messages required", "type": "invalid_request"}})
        _tools = data.get("tools") or []
        _tc = data.get("tool_choice", "auto")
        _use_tools = bool(_tools) and _tc != "none"
        try:
            messages = providers.tools_sanitize_messages(messages)
        except Exception:
            pass
        if not messages:
            return self._send(400, {"error": {"message": "messages required", "type": "invalid_request"}})
        if _use_tools:
            try:
                _instr = providers.tools_instruction(_tools)
                if isinstance(_tc, dict) and (_tc.get("function") or {}).get("name"):
                    _instr += "\nYou MUST call %s now." % (_tc["function"]["name"])
                _sys = [m for m in messages if m.get("role") == "system"]
                if _sys:
                    _sys[0]["content"] = (_sys[0]["content"] + "\n\n" + _instr)
                else:
                    messages = [{"role": "system", "content": _instr}] + messages
            except Exception:
                pass
        try:
            _hist = [m for m in messages if m.get("role") in ("user", "assistant")][-3:]
            _qtext = " ".join(str(m.get("content") or "") for m in _hist)
            _hits = kb.search(_qtext) if kb.detect(_qtext) else []
            if _hits:
                messages = [{"role": "system", "content": kb.prompt(_hits)}] + messages
        except Exception:
            pass
        try:
            _mh = [m for m in messages if isinstance(m, dict) and m.get("role") in ("user", "assistant")][-3:]
            _mtext = " ".join(str(m.get("content") or "") for m in _mh)
            messages = [{"role": "system", "content": manhaj.prompt(_mtext)}] + messages
        except Exception:
            pass
        t0 = time.time()
        try:
            text, used = providers.chat(model, messages, timeout=240)
        except Exception as e:
            return self._send(502, {"error": {"message": str(e)[:200], "type": "all_failed"}})
        _calls = []
        if _use_tools:
            try:
                _names = [((t.get("function") or {}).get("name") if t.get("type") == "function" else t.get("name")) for t in _tools if isinstance(t, dict)]
                text, _parsed = providers.tools_parse(text, _names)
                for _i, (_nm, _ag) in enumerate(_parsed):
                    _calls.append({
                        "id": "call_vpx%d%d%d" % (int(t0) % 100000, _i, random.randint(100, 999)),
                        "type": "function",
                        "function": {"name": _nm, "arguments": json.dumps(_ag, ensure_ascii=False)}})
            except Exception:
                pass
        _finish = "tool_calls" if _calls else "stop"
        dt = time.time() - t0
        try:
            providers.kv.gist_flush()
        except Exception:
            pass
        _cid = "chatcmpl-vpx%d%d" % (int(t0), random.randint(100, 999))
        if _stream:
            _es = " ".join(str(text).split())
            _half = len(_es) // 2
            _chunks = [
                {"id": _cid, "object": "chat.completion.chunk", "created": int(t0),
                 "model": used, "choices": [{"index": 0, "delta": {"role": "assistant", "content": _es[:_half]},
                                             "finish_reason": None}]},
                {"id": _cid, "object": "chat.completion.chunk", "created": int(t0),
                 "model": used, "choices": [{"index": 0, "delta": {"content": _es[_half:]},
                                             "finish_reason": None}]},
            ]
            if _calls:
                _chunks.append(
                    {"id": _cid, "object": "chat.completion.chunk", "created": int(t0),
                     "model": used, "choices": [{"index": 0,
                         "delta": {"tool_calls": [
                             {"index": _i, "id": _c["id"], "type": "function",
                              "function": {"name": _c["function"]["name"],
                                           "arguments": _c["function"]["arguments"]}}
                             for _i, _c in enumerate(_calls)]},
                         "finish_reason": None}]})
            _chunks.append(
                {"id": _cid, "object": "chat.completion.chunk", "created": int(t0),
                 "model": used, "choices": [{"index": 0, "delta": {}, "finish_reason": _finish}]})
            _body = "".join("data: " + json.dumps(c, ensure_ascii=False) + "\n\n" for c in _chunks)
            _body += "data: [DONE]\n\n"
            _bb = _body.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Content-Length", str(len(_bb)))
            self._cors()
            self.end_headers()
            return self.wfile.write(_bb)
        _msg = {"role": "assistant", "content": text or ""}
        if _calls:
            _msg["tool_calls"] = _calls
        return self._send(200, {
            "id": _cid,
            "object": "chat.completion", "created": int(t0), "model": used,
            "choices": [{"index": 0, "message": _msg,
                         "finish_reason": _finish}],
            "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0,
                      "seconds": round(dt, 1)}})

    def do_GET(self):
        return self._send(200, {"ok": True, "service": "vpx-chat",
                                "usage": "POST /v1/chat/completions {model, messages}"})

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()
