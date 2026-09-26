"""Vercel KV (Upstash REST) + in-memory fallback. NO Fly, NO files."""
import os as _os

try:
    import requests as _rq
except Exception:
    _rq = None

_URL = (_os.environ.get("KV_REST_API_URL")
        or _os.environ.get("UPSTASH_REDIS_REST_URL") or "").rstrip("/")
_TOK = (_os.environ.get("KV_REST_API_TOKEN")
        or _os.environ.get("UPSTASH_REDIS_REST_TOKEN") or "")
_MEM = {}
_WARNED = [False]


def _warn():
    if not _WARNED[0]:
        _WARNED[0] = True
        print("[KV] no KV_REST env — memory fallback (data dies with instance)", flush=True)


def use_rest():
    return bool(_URL and _TOK and _rq)


def _pipe(*cmds):
    r = _rq.post(_URL + "/pipeline", headers={"Authorization": "Bearer " + _TOK},
                 json=[list(c) for c in cmds], timeout=(8, 25))
    r.raise_for_status()
    return r.json() or []


def kv_get(key, default=None):
    if use_rest():
        try:
            res = _pipe(["GET", key])
            v = res[0].get("result") if res else None
            return v if v is not None else default
        except Exception:
            pass
    else:
        if use_gist():
            try:
                v = gist_get(key)
                if v is not None:
                    return v
            except Exception:
                pass
        else:
            _warn()
    return _MEM.get(key, default)


def kv_set(key, value, ex=None):
    if use_rest():
        try:
            cmd = ["SET", key, value] + (["EX", int(ex)] if ex else [])
            _pipe(cmd)
            return True
        except Exception:
            pass
    else:
        if use_gist():
            try:
                gist_set(key, value)
            except Exception:
                pass
        else:
            _warn()
    _MEM[key] = value
    return True


def kv_delete(key):
    if use_rest():
        try:
            _pipe(["DEL", key])
        except Exception:
            pass
    if not use_rest() and use_gist():
        try:
            gist_delete(key)
        except Exception:
            pass
    _MEM.pop(key, None)
    return True


def kv_jget(key, default=None):
    import json as _j
    v = kv_get(key)
    if v is None:
        return default
    try:
        return _j.loads(v)
    except Exception:
        return default


def kv_jset(key, obj, ex=None):
    import json as _j
    return kv_set(key, _j.dumps(obj, ensure_ascii=False), ex)


def kv_lpush(key, *values):
    if use_rest():
        try:
            _pipe(["LPUSH", key] + list(values))
            return True
        except Exception:
            pass
    else:
        _warn()
    lst = _MEM.get(key) or []
    _MEM[key] = list(values) + lst
    return True


def kv_lrange(key, start=0, stop=-1):
    if use_rest():
        try:
            res = _pipe(["LRANGE", key, start, stop])
            return res[0].get("result") or [] if res else []
        except Exception:
            pass
    else:
        _warn()
    lst = _MEM.get(key) or []
    return lst[start:None if stop == -1 else stop + 1]


def kv_ltrim(key, start=0, stop=-1):
    if use_rest():
        try:
            _pipe(["LTRIM", key, start, stop])
            return True
        except Exception:
            pass
    else:
        _warn()
    lst = _MEM.get(key) or []
    _MEM[key] = lst[start:None if stop == -1 else stop + 1]
    return True


def kv_lrem(key, value, count=0):
    if use_rest():
        try:
            _pipe(["LREM", key, count, value])
            return True
        except Exception:
            pass
    else:
        _warn()
    _MEM[key] = [x for x in (_MEM.get(key) or []) if x != value]
    return True


def kv_incr(key):
    if use_rest():
        try:
            res = _pipe(["INCR", key])
            return int(res[0].get("result") or 0) if res else 0
        except Exception:
            pass
    else:
        _warn()
    _MEM[key] = int(_MEM.get(key) or 0) + 1
    return _MEM[key]


# ---- GitHub Gist KV backend (free persistence, zero signup) ----
_GIST = _os.environ.get("GH_KV_GIST") or ""
_GHTOK = _os.environ.get("GH_TOKEN") or ""
_G_MEM = {}
_G_DIRTY = {}
_G_FLUSH_T = [0.0]
_G_FILES = [{}, 0.0]
_G_TTL = 60
_G_BACKOFF = [0.0]  # V10.4: skip flushes while GitHub secondary-bans us


def use_gist():
    return bool(_GIST and _GHTOK and _rq)


def _g_file(key):
    s = "".join(c if (c.isalnum() or c in "-_.") else "_" for c in str(key))
    return (s[:80] or "k") + ".json"


def _g_headers():
    return {"Authorization": "Bearer " + _GHTOK, "Accept": "application/vnd.github+json"}


def _g_files():
    import time as _t
    now = _t.time()
    if now - _G_FILES[1] < _G_TTL and _G_FILES[0]:
        return _G_FILES[0]
    try:
        r = _rq.get("https://api.github.com/gists/" + _GIST, headers=_g_headers(), timeout=(8, 25))
        if r.status_code == 200:
            _G_FILES[0] = (r.json() or {}).get("files") or {}
            _G_FILES[1] = now
    except Exception:
        pass
    return _G_FILES[0]


_RL_MEM = {}


def gist_get(key):
    import time as _t
    if str(key).startswith("vpx:rl:"):
        return _RL_MEM.get(str(key))
    fn = _g_file(key)
    now = _t.time()
    hit = _G_MEM.get(fn)
    if hit is not None and now - hit[1] < _G_TTL:
        return hit[0]
    f = _g_files().get(fn)
    if not f:
        return None
    try:
        if f.get("truncated") and f.get("raw_url"):
            rr = _rq.get(f["raw_url"], headers=_g_headers(), timeout=(8, 30))
            content = rr.text if rr.status_code == 200 else None
        else:
            content = f.get("content")
    except Exception:
        content = None
    if content is not None:
        _G_MEM[fn] = [content, now]
    return content


def gist_set(key, value):
    import time as _t
    if str(key).startswith("vpx:rl:"):
        _RL_MEM[str(key)] = value
        if len(_RL_MEM) > 2000:
            for _k in list(_RL_MEM)[:1000]:
                _RL_MEM.pop(_k, None)
        return
    fn = _g_file(key)
    _G_MEM[fn] = [value, _t.time()]
    _G_DIRTY[fn] = value
    gist_flush(force=str(key).startswith("vpx:sec:"))


def gist_delete(key):
    fn = _g_file(key)
    _G_MEM.pop(fn, None)
    _G_DIRTY[fn] = None
    gist_flush()


def gist_flush(force=False):
    import time as _t
    now = _t.time()
    if not _G_DIRTY:
        return True
    # #134: 25s→120s+jitter — dozens of serverless instances cold-starting and
    # PATCHing one gist at once = GitHub secondary-ban (403 on EVERY write,
    # pools+proxies never persist). Rare flushes let the ban lift for good.
    if not force and now - _G_FLUSH_T[0] < 120 + (now * 7 + _os.getpid()) % 60:
        return True
    if now < _G_BACKOFF[0]:
        return False
    # #136: ONE FILE per PATCH, smallest-first. Multi-file / MB-sized batches
    # trip GitHub's secondary ("scraping") 403 and NOTHING lands; solo small
    # PATCHes pass (proven by live gist versions). A 403 on one file must not
    # poison the rest — small files (locks/counters/px) land first.
    _G_FLUSH_T[0] = now
    try:
        items = sorted(list(_G_DIRTY.items()),
                       key=lambda kv: len(kv[1]) if isinstance(kv[1], str) else 0)
    except Exception:
        items = list(_G_DIRTY.items())
    if not force:
        items = items[:1]
    else:
        items = items[:10]
    _ok = True
    for fn, v in items:
        if _t.time() < _G_BACKOFF[0]:
            _ok = False
            break
        try:
            one = {fn: None if v is None else {"content": v if isinstance(v, str) else str(v)}}
            r = _rq.patch("https://api.github.com/gists/" + _GIST, headers=_g_headers(),
                          json={"files": one}, timeout=(10, 60))
        except Exception:
            _ok = False
            continue
        if r.status_code in (200, 201):
            _G_DIRTY.pop(fn, None)
            _G_FLUSH_T[0] = _t.time()
            try:
                _G_FILES[0] = (r.json() or {}).get("files") or _G_FILES[0]
                _G_FILES[1] = _t.time()
            except Exception:
                pass
        elif r.status_code == 403:
            _G_BACKOFF[0] = _t.time() + 600  # retries EXTEND the ban — go quiet
            _ok = False
            break
        elif r.status_code == 422:
            # solo null-delete of a missing file (or bad payload) — drop it,
            # keep going (fresh saves re-dirty the key anyway → self-heals)
            _G_DIRTY.pop(fn, None)
        else:
            _ok = False
    return _ok and not _G_DIRTY
