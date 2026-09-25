"""#122: Firebase door (6th API) — adapter routing to the same Vercel api/* handlers.

Layout mirrors vercel/ (api/ + lib/) so the handler modules' own
sys.path bootstrap (../lib) keeps working unchanged.
Secrets come from functions/.env (created at deploy time, NEVER committed).
"""
import importlib
import io
import os
import sys
import types
import types

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from firebase_functions import https_fn, options  # noqa: E402

# path -> "api.<module>" (same routes as vercel.json rewrites + direct /api/*)
_ROUTES = {
    "/api/chat": "api.chat",
    "/v1/chat/completions": "api.chat",
    "/chat/completions": "api.chat",
    "/api/models": "api.models",
    "/v1/models": "api.models",
    "/v1": "api.models",
    "/v1/": "api.models",
    "/models": "api.models",
    "/api/status": "api.status",
    "/api/cron": "api.cron",
    "/api/dash": "api.dash",
    "/": "api.dash",
    "/api/playground": "api.playground",
    "/playground": "api.playground",
    "/api/play": "api.play",
    "/api/refresh": "api.refresh",
}

_MOD_CACHE = {}


def _get_handler_cls(modname):
    cls = _MOD_CACHE.get(modname)
    if cls is None:
        mod = importlib.import_module(modname)
        cls = mod.handler
        _MOD_CACHE[modname] = cls
    return cls


class _Shim:
    """Minimal BaseHTTPRequestHandler surface backed by a Flask request."""

    def __init__(self, req):
        qs = req.query_string.decode("utf-8", "replace") if req.query_string else ""
        self.command = (req.method or "GET").upper()
        self.path = req.path + ("?" + qs if qs else "")
        self.headers = req.headers
        try:
            body = req.get_data() or b""
        except Exception:
            body = b""
        self.rfile = io.BytesIO(body)
        self.wfile = io.BytesIO()
        try:
            self.client_address = (req.remote_addr or "?", 0)
        except Exception:
            self.client_address = ("?", 0)
        self._code = 200
        self._hdrs = {}

    def send_response(self, code):
        try:
            self._code = int(code)
        except Exception:
            self._code = 200

    def send_header(self, key, value):
        self._hdrs[str(key)] = str(value)

    def end_headers(self):
        pass


@https_fn.on_request(
    region="us-central1",
    memory=options.MemoryOption.MB_512,
    timeout_sec=300,
    max_instances=10,
)
def api(req: https_fn.Request) -> https_fn.Response:
    try:
        path = (req.path or "/").rstrip("/") or "/"
        if req.path in ("/v1/",):
            path = "/v1/"
        modname = _ROUTES.get(path) or _ROUTES.get(req.path)
        if not modname:
            return https_fn.Response(
                '{"error":{"message":"not found","type":"not_found"}}',
                status=404,
                content_type="application/json",
            )
        cls = _get_handler_cls(modname)
        inst = cls.__new__(cls)
        shim = _Shim(req)
        inst.__dict__.update(shim.__dict__)
        # bind shim transport methods onto the instance (else BaseHTTPRequestHandler's
        # send_response runs and needs requestline/request_version)
        for _m in ("send_response", "send_header", "end_headers"):
            setattr(inst, _m, types.MethodType(getattr(_Shim, _m), inst))
        inst.requestline = "%s %s HTTP/1.1" % (shim.command, shim.path)
        inst.request_version = "HTTP/1.1"
        inst.protocol_version = "HTTP/1.1"
        meth = getattr(cls, "do_" + shim.command, None)
        if meth is None:
            meth = getattr(cls, "do_OPTIONS", None)
        if meth is None:
            return https_fn.Response(
                '{"error":{"message":"method not allowed","type":"method"}}',
                status=405,
                content_type="application/json",
            )
        meth(inst)
        body = inst.wfile.getvalue()
        headers = dict(inst._hdrs)
        headers.setdefault("Access-Control-Allow-Origin", "*")
        return https_fn.Response(body, status=inst._code, headers=headers)
    except Exception as ex:
        return https_fn.Response(
            '{"error":{"message":"%s","type":"adapter"}}' % str(ex)[:200].replace('"', "'"),
            status=500,
            content_type="application/json",
        )
