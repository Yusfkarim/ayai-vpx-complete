"""Self-tracked Vercel Hobby usage guard (invocations + bytes).

Vercel's usage API is Pro-only, so we count every function invocation
ourselves. Gist backend: each serverless instance owns one tiny file
(per-month), cron sums them — no write races. Alerts at 70% (warn) and
90% (urgent) of the conservative Hobby limits. Never raises.
"""
import os
import secrets
import time

import kv

INV_LIMIT = 100000
BYTE_LIMIT = 100 * 1024 * 1024 * 1024

_INST = "%d-%s" % (os.getpid(), secrets.token_hex(4))
_MEM = {"m": "", "n": 0, "b": 0, "saved_n": 0}


def month():
    return time.strftime("%Y-%m")


def _key(m=None):
    return "vpx-usage-%s-%s" % (m or month(), _INST)


def hit(nbytes=0):
    """Count one invocation. Called from every endpoint. Never raises."""
    try:
        m = month()
        if _MEM["m"] != m:
            if _MEM["m"]:
                try:
                    kv.kv_jset(_key(_MEM["m"]), {"n": _MEM["n"], "b": _MEM["b"], "t": time.time()})
                except Exception:
                    pass
            _MEM.update(m=m, n=0, b=0, saved_n=0)
        _MEM["n"] += 1
        try:
            _MEM["b"] += max(0, int(nbytes or 0))
        except Exception:
            pass
        if kv.use_rest():
            try:
                kv._pipe(["INCR", "vpx-usage-%s-n" % m],
                         ["INCRBY", "vpx-usage-%s-b" % m, int(nbytes or 0)])
            except Exception:
                pass
            return
        now = time.time()
        if (_MEM["n"] - _MEM["saved_n"] >= 10
                or (now - _MEM.get("saved_t", 0) > 60
                    and _MEM["n"] > _MEM["saved_n"])):
            kv.kv_jset(_key(m), {"n": _MEM["n"], "b": _MEM["b"], "t": now})
            _MEM["saved_n"] = _MEM["n"]
            _MEM["saved_t"] = now
    except Exception:
        pass


def _rest_total(m):
    try:
        res = kv._pipe(["GET", "vpx-usage-%s-n" % m], ["GET", "vpx-usage-%s-b" % m])
        n = int((res[0].get("result") or 0)) if res else 0
        b = int((res[1].get("result") or 0)) if len(res) > 1 else 0
        return n, b
    except Exception:
        return 0, 0


def month_total():
    """(invocations, bytes) for the current month across all instances."""
    m = month()
    try:
        if kv.use_rest():
            return _rest_total(m)
        if kv.use_gist():
            try:
                kv.kv_jset(_key(m), {"n": _MEM["n"], "b": _MEM["b"], "t": time.time()})
                _MEM["saved_n"] = _MEM["n"]
                # NOTE: never force-flush here — GitHub secondary rate limits
                # (403) punish PATCH storms; throttled flush lands it in <=25s.
            except Exception:
                pass
            import json as _j
            pfx = "vpx-usage-%s-" % m
            n = b = 0
            try:
                files = kv._g_files()
            except Exception:
                files = {}
            for fn, f in (files or {}).items():
                if not fn.startswith(pfx) or not fn.endswith(".json"):
                    continue
                try:
                    d = _j.loads((f or {}).get("content") or "{}")
                    n += int(d.get("n") or 0)
                    b += int(d.get("b") or 0)
                except Exception:
                    pass
            return n, b
        return int(_MEM.get("n") or 0), int(_MEM.get("b") or 0)
    except Exception:
        return 0, 0


def get_status():
    """Small dict for api_status/dashboard. Never raises, ~0-1 HTTP."""
    try:
        n, b = month_total()
        return {"month": month(), "inv": n,
                "inv_pct": round(100.0 * n / INV_LIMIT, 1),
                "gb": round(b / (1024.0 ** 3), 3),
                "gb_pct": round(100.0 * b / BYTE_LIMIT, 1)}
    except Exception:
        return {}


def _cleanup_old(m):
    try:
        pfx = "vpx-usage-"
        y, mo = int(m[:4]), int(m[5:7])
        pm = "%04d-%02d" % (y if mo > 1 else y - 1, mo - 1 if mo > 1 else 12)
        for fn in list((kv._g_files() or {})):
            if fn.startswith(pfx) and fn.endswith(".json"):
                mm = fn[len(pfx):len(pfx) + 7]
                # only per-instance month files (vpx-usage-YYYY-MM-*);
                # never touch alert flags (vpx-usage-alert70/90-*)
                if len(mm) != 7 or mm[4] != "-" or not mm[:4].isdigit() or not mm[5:7].isdigit():
                    continue
                if mm != m and mm != pm:
                    try:
                        kv.gist_delete(fn[:-5])
                    except Exception:
                        pass
    except Exception:
        pass


def check_and_alert():
    """Called from cron: sum usage, TG-alert at 70%/90%. Never raises."""
    try:
        m = month()
        n, b = month_total()
        pi, pb = n / float(INV_LIMIT), b / float(BYTE_LIMIT)
        p = max(pi, pb)
        import providers
        if p >= 0.9 and not kv.kv_jget("vpx-usage-alert90-" + m):
            kv.kv_jset("vpx-usage-alert90-" + m, {"t": time.time()})
            providers._vpx_sec_alert(
                "🚨 VPX usage 90%% (inv %d, %.2fGB) — site may 503 soon! Switch clients to MIRROR backend now." % (n, b / 1024.0 ** 3))
        elif p >= 0.7 and not kv.kv_jget("vpx-usage-alert70-" + m):
            kv.kv_jset("vpx-usage-alert70-" + m, {"t": time.time()})
            providers._vpx_sec_alert(
                "⚠️ VPX usage 70%% (inv %d, %.2fGB) — prepare mirror backend, %d invocations left." % (n, b / 1024.0 ** 3, INV_LIMIT - n))
        _cleanup_old(m)
    except Exception:
        pass
