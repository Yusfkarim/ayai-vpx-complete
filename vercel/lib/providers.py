"""Vercel providers: ported funcs + KV pools + minters + catalog + chat router. NO Fly."""
import json
import os
import random
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _ported_raw as R
import shim

shim.install(R)
import kv

API_KEY = os.environ.get("VAPI_KEY") or os.environ.get("API_KEY") or ""
FB_KEYS = {
    "ca": os.environ.get("CA_FB_KEY") or "",
    "cb": os.environ.get("CB_FB_KEY") or "",
    "nv": os.environ.get("NV_FB_KEY") or "",
}
CRON_SECRET = os.environ.get("CRON_SECRET") or ""
R.CA_KEY = FB_KEYS["ca"]
R.CB_KEY = FB_KEYS["cb"]
R.NV_KEY = FB_KEYS["nv"]


# ═══════ KV overrides (rebind into R namespace — internal calls resolve here) ═══════
_vpx_file_cache = {}

def _vpx_json_save_locked(path, obj):
    try:
        import hashlib
        k = "vpx:file:" + hashlib.md5(str(path).encode()).hexdigest()
        _vpx_file_cache[str(path)] = obj
        kv.kv_jset(k, obj)
    except Exception:
        pass

def _vpx_json_load_safe(path, default=None):
    try:
        if str(path) in _vpx_file_cache:
            return _vpx_file_cache[str(path)]
        import hashlib
        k = "vpx:file:" + hashlib.md5(str(path).encode()).hexdigest()
        d = kv.kv_jget(k)
        return d if d is not None else default
    except Exception:
        return default

R._json_save_locked = _vpx_json_save_locked
R._json_load_safe = _vpx_json_load_safe


def _seed_file(name):
    try:
        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "pooldata", name + ".json")
        return json.load(open(p))
    except Exception:
        return {}


def _vpx_ach_load():
    d = kv.kv_jget("vpx:ach") or _seed_file("ach") or {}
    R.ACH_ST["accounts"] = d.get("accounts") or []
    R.ACH_ST["idx"] = int(d.get("idx") or 0)
    R.ACH_ST["signups"] = d.get("signups") or {"date": "", "n": 0}


def _vpx_ach_save():
    kv.kv_jset("vpx:ach", {"accounts": (R.ACH_ST.get("accounts") or [])[-10000:],
                           "idx": R.ACH_ST.get("idx") or 0,
                           "signups": R.ACH_ST.get("signups") or {"date": "", "n": 0}})


def _vpx_gz_load():
    if R._GZ_MEM_LD[0]:
        return
    R._GZ_MEM_LD[0] = True
    try:
        d = kv.kv_jget("vpx:gzmem") or {}
        for k, v in (d.get("good") or {}).items():
            R._GZ_GOOD[k] = float(v)
        for k, v in (d.get("wall") or {}).items():
            R._GZ_WALL[k] = float(v)
        for k, v in (d.get("burned") or {}).items():
            p = k.split("\x00")
            if len(p) == 2:
                R._GZ_BURNED[(p[0], p[1])] = float(v)
        if d.get("catalog"):
            R._GZ_SYNC["catalog"] = d["catalog"]
            R._GZ_SYNC["t"] = d.get("cat_t") or 0
    except Exception:
        pass


def _vpx_gz_save():
    try:
        kv.kv_jset("vpx:gzmem", {
            "good": {k: v for k, v in list(R._GZ_GOOD.items())[:2000]},
            "wall": {k: v for k, v in list(R._GZ_WALL.items())[:2000]},
            "burned": {a + "\x00" + b: v for (a, b), v in list(R._GZ_BURNED.items())[:2000]},
            "catalog": R._GZ_SYNC.get("catalog") or {},
            "cat_t": R._GZ_SYNC.get("t") or 0})
    except Exception:
        pass


def _vpx_proxy_get(n=3):
    try:
        pxs = kv.kv_jget("vpx:px") or []
        random.shuffle(pxs)
        return pxs[:max(1, int(n))]
    except Exception:
        return []


def _vpx_proxy_mark_bad(px):
    try:
        st = kv.kv_jget("vpx:pxstrikes") or {}
        st[px] = int(st.get(px, 0)) + 1
        if st[px] >= 3:
            pxs = [p for p in (kv.kv_jget("vpx:px") or []) if p != px]
            kv.kv_jset("vpx:px", pxs)
            st.pop(px, None)
            try:
                (R.PROXY_ST.get("pool") or {}).pop(px, None)
            except Exception:
                pass
        kv.kv_jset("vpx:pxstrikes", {k: v for k, v in list(st.items())[-500:]})
    except Exception:
        pass


R._ach_load = _vpx_ach_load
R._ach_save = _vpx_ach_save
R._gz_mem_load = _vpx_gz_load
R._gz_mem_save = _vpx_gz_save
R._proxy_get = _vpx_proxy_get
R._proxy_mark_bad = _vpx_proxy_mark_bad
try:
    _vpx_ach_load()
except Exception:
    pass
try:
    _vpx_gz_load()
except Exception:
    pass

# ---- pool seeds + save overrides + signup adapters (V2) ----
POOL_SEEDS = ("ca", "cb", "nv", "ac", "al", "alle", "mc", "cbox", "pia", "aiml", "worm")

def _seed_load():
    for name in POOL_SEEDS:
        try:
            st = getattr(R, name.upper() + "_ST")
            d = kv.kv_jget("vpx:poolstate:" + name) or _seed_file(name) or {}
            if d:
                st.clear()
                st.update(d)
            st.setdefault("accounts", [])
            st.setdefault("idx", 0)
        except Exception:
            pass
    try:  # #119: cold instances have empty proxy mem → proxy-first silently degrades to direct
        _pxs = kv.kv_jget("vpx:px") or []
        _pool = R.PROXY_ST.setdefault("pool", {})
        for _p in _pxs[:200]:
            _pool.setdefault(_p, {"t": time.time(), "lat": 9})
    except Exception:
        pass

def _mk_saver(name):
    key = "vpx:poolstate:" + name
    attr = name.upper() + "_ST"
    def _save():
        try:
            st = getattr(R, attr)
            slim = {k: (v[-10000:] if k == "accounts" and isinstance(v, list) else v)
                    for k, v in st.items()}
            kv.kv_jset(key, slim)
        except Exception:
            pass
    return _save

for _pn in POOL_SEEDS:
    setattr(R, "_" + _pn + "_save_acc", _mk_saver(_pn))
for _pn in POOL_SEEDS:
    setattr(R, "_" + _pn + "_load_acc", (lambda: None))

def _mk_fb_signup(name):
    attr = name.upper() + "_ST"
    def _su(mkey=None, force=False):
        try:
            r = mint_fb_pool(name, count=1)
            if r.get("minted"):
                accs = getattr(R, attr).get("accounts") or []
                return accs[-1] if accs else True
        except Exception:
            pass
        return None
    return _su

R._ca_signup_new = _mk_fb_signup("ca")
R._cb_signup_new = _mk_fb_signup("cb")
R._nv_signup_new = _mk_fb_signup("nv")
R._em_signup_new = lambda *a, **k: None  # em needs node (Vercel has none)
_MS_KEYS = ("duck", "ak_ok", "ak_block", "l7_ok", "l7_bad", "ct_ok", "ct_bad",
            "yl_ok", "yl_bad", "hk_ok", "hk_bad", "hf_ok", "hf_bad", "aka_ok",
            "aka_bad", "hb_ok", "hb_bad", "gk_ok", "gk_bad", "gz_ok", "gz_bad",
            "pi_ok", "pi_bad", "cb_ok", "cb_bad", "nv_ok", "nv_bad", "al_ok",
            "al_bad", "aiml_ok", "ac_ok", "ca_ok")


def _msync_load():
    try:
        d = kv.kv_jget("vpx:msync") or _seed_file("model_sync") or {}
        if d:
            R.MS.clear()
            R.MS.update(d)
        for _k in _MS_KEYS:
            R.MS.setdefault(_k, {})
    except Exception:
        pass

try:
    _seed_load()
    _msync_load()
except Exception:
    pass


# ═══════ catalogs ═══════
def _slug(v):
    return re.sub(r"[^a-zA-Z0-9]+", "-", str(v)).strip("-").lower()[:60] or "model"


def pol_models():
    c = kv.kv_jget("vpx:cat:pol") or {}
    if c.get("items") and time.time() - c.get("t", 0) < 21600:
        return c["items"]
    items = []
    try:
        import requests
        r = requests.get("https://text.pollinations.ai/models", timeout=15)
        for m in r.json():
            name = m.get("name")
            if not name:
                continue
            out = m.get("output_types") or m.get("output") or ["text"]
            if isinstance(out, str):
                out = [out]
            if "text" in out or not out:
                items.append({"id": "pol-" + name, "model": name})
        items = items[:12]
    except Exception:
        pass
    if not items:
        items = [{"id": "pol-openai", "model": "openai"}]
    kv.kv_jset("vpx:cat:pol", {"t": time.time(), "items": items})
    return items


def aff_models():
    c = kv.kv_jget("vpx:cat:aff") or {}
    if c.get("items") and time.time() - c.get("t", 0) < 21600:
        return c["items"]
    items = []
    try:
        live = R.fetch_models() or {}
        for mid, info in live.items():
            items.append({"id": "aff-" + str(mid), "model": str(mid),
                          "endpoint": (info or {}).get("endpoint") or ""})
        items = items[:40]
    except Exception:
        pass
    if items:
        kv.kv_jset("vpx:cat:aff", {"t": time.time(), "items": items})
    return items


def lr_models():
    return [{"id": "lr-nano", "model": "openai/gpt-5.4-nano",
             "name": "GPT-5.4 Nano (Lorka)"}]


def gz_models():
    cat = R._GZ_SYNC.get("catalog") or {}
    if not cat or time.time() - R._GZ_SYNC.get("t", 0) > 21600:
        try:
            R.sync_giz_models(force=True)
            cat = R._GZ_SYNC.get("catalog") or {}
            _vpx_gz_save()
        except Exception:
            pass
    return [{"id": "gz-" + _slug(v), "model": v, "name": lbl}
            for v, lbl in sorted(cat.items())][:40]


def ach_models():
    return [{"id": "ach-" + k, "model": k, "name": nm} for k, nm, _ in R.ACH_MODELS]


def _pool_cat(name, builder):
    try:
        c = kv.kv_jget("vpx:cat:" + name) or {}
        if c.get("items") and time.time() - c.get("t", 0) < 21600:
            return c["items"]
        items = []
        for s in builder() or []:
            if not isinstance(s, dict):
                continue
            mid = s.get("model_id") or s.get("mkey") or s.get("id") or ""
            sid = str(s.get("id") or mid or "")
            if not mid:
                continue
            iid = sid if sid.startswith(name + "-") else "%s-%s" % (name, _slug(sid))
            items.append({"id": iid, "model": mid,
                          "name": s.get("name") or mid})
        items = items[:40]
        if items:
            kv.kv_jset("vpx:cat:" + name, {"t": time.time(), "items": items})
        return items
    except Exception:
        return []

def ca_models(): return _pool_cat("ca", R.ca_servers)
def cb_models(): return _pool_cat("cb", R.cb_servers)
def nv_models(): return _pool_cat("nv", R.nv_servers)
def ac_models(): return _pool_cat("ac", R.ac_servers)
def al_models(): return _pool_cat("al", R.al_servers)
def alle_models(): return _pool_cat("alle", R.alle_servers)
def rwd_models(): return _pool_cat("rwd", R.rwd_servers)

def cbc_models():
    return [{"id": "cbc-gpt-5", "model": "gpt-5", "name": "GPT-5 (ChatBotChat)"}]

def g4f_models():
    try:
        c = kv.kv_jget("vpx:cat:g4f") or {}
        if c.get("items") and time.time() - c.get("t", 0) < 21600:
            return c["items"]
        import requests as _rq
        r = _rq.get(R.G4F_BASE + "/v1/models", timeout=20)
        items = [{"id": "g4f-" + _slug(str(m.get("id"))), "model": m.get("id"),
                  "name": str(m.get("id"))} for m in r.json().get("data", [])[:40]
                 if m.get("id")]
        if items:
            kv.kv_jset("vpx:cat:g4f", {"t": time.time(), "items": items})
            return items
    except Exception:
        pass
    return []

def act_models(): return _pool_cat("act", R.act_servers)
def fla_models(): return _pool_cat("fla", R.fla_servers)
def z02_models(): return _pool_cat("z02", R.z02_servers)
def qb_models(): return _pool_cat("qb", R.qb_servers)
def duck_models(): return _pool_cat("duck", R.duck_servers)
def l7_models(): return _pool_cat("l7", R.l7_servers)
def ng_models(): return _pool_cat("ng", R.ng_servers)
def ct_models(): return _pool_cat("ct", R.ct_servers)
def yl_models(): return _pool_cat("yl", R.yl_servers)
def hk_models(): return _pool_cat("hk", R.hk_servers)
def hf_models(): return _pool_cat("hf", R.hf_servers)
def aka_models(): return _pool_cat("aka", R.aka_servers)
def hb_models(): return _pool_cat("hb", R.hb_servers)
def gk_models(): return _pool_cat("gk", R.gk_servers)
def pi_models(): return _pool_cat("pi", R.pi_servers)
def aiml_models(): return _pool_cat("aiml", R.aiml_servers)
def mc_models(): return []  # no-Fly: hih needs browser-minter (Fly keeps mc)
def pia_models(): return _pool_cat("pia", R.pia_servers)
def cbox_models(): return _pool_cat("cbox", R.cbox_servers)
def worm_models(): return _pool_cat("worm", R.worm_servers)  # #123

def full_catalog():
    out, seen = [], set()
    for fn in (pol_models, aff_models, lr_models, gz_models, ach_models,
               ca_models, cb_models, nv_models, ac_models, al_models,
               alle_models, rwd_models, mc_models, pia_models, cbox_models,
               aiml_models, worm_models, duck_models, l7_models, ct_models, yl_models,
               hk_models, hf_models, aka_models, hb_models, gk_models,
               pi_models, act_models, fla_models, z02_models, qb_models,
               ng_models, cbc_models, g4f_models):
        try:
            for it in fn() or []:
                if it.get("id") not in seen and not _is_dead(it.get("id") or ""):
                    seen.add(it["id"])
                    out.append(it)
        except Exception:
            continue
    return out


# ═══════ chat router + fallback ═══════
def _hf_toks():
    try:
        d = kv.kv_jget("vpx:hf_toks") or {}
        toks = [t for t in (d.get("toks") or []) if t]
        if not toks:
            toks = [t for t in [getattr(R, "HF_TOKEN", "")] +
                    (os.environ.get("HF_TOKENS") or "").split(",") if t.strip()]
            toks = list(dict.fromkeys(t.strip() for t in toks))
            if toks:
                kv.kv_jset("vpx:hf_toks", {"toks": toks, "i": 0})
        return toks, int(d.get("i", 0)) % max(1, len(toks))
    except Exception:
        return [getattr(R, "HF_TOKEN", "")], 0


def _hf_rotate():
    try:
        toks, i = _hf_toks()
        if len(toks) < 2:
            return False
        ni = (i + 1) % len(toks)
        R.HF_TOKEN = toks[ni]
        try:
            R.HF_LIMIT["until"] = 0
        except Exception:
            pass
        kv.kv_jset("vpx:hf_toks", {"toks": toks, "i": ni})
        return True
    except Exception:
        return False


def chat_once(model_id, messages, timeout=110):
    if model_id.startswith("pol-"):
        return R.pol_chat(model_id[4:] or "openai", messages, timeout)
    if model_id.startswith("lr-"):
        return R.lr_chat(messages, None, min(timeout, 75))
    if model_id.startswith("gz-"):
        for it in gz_models():
            if it["id"] == model_id:
                return R.gz_chat(messages, it["model"], min(timeout, 90))
        raise RuntimeError("gz model unknown: " + model_id)
    if model_id.startswith("ach-"):
        return R.ach_chat(messages, model_id[4:] or "consensus", min(timeout, 110))
    if model_id.startswith("aff-"):
        slug = model_id[4:]
        ep = ""
        for it in aff_models():
            if it["id"] == model_id:
                ep = it.get("endpoint") or ""
        q = next((str(m.get("content")) for m in reversed(messages)
                  if m.get("role") == "user"), "سڵاو")
        bot = R.AIFreeChat(model=slug, endpoint=ep or None, timeout=min(timeout, 120))
        return bot.chat(q, history=messages)
    if model_id[:3] in ("ca-", "cb-", "nv-", "ac-", "al-"):
        pool = model_id[:2]
        fn = {"ca": R.ca_chat, "cb": R.cb_chat, "nv": R.nv_chat,
              "ac": R.ac_chat, "al": R.al_chat}[pool]
        cats = {"ca": ca_models, "cb": cb_models, "nv": nv_models,
                "ac": ac_models, "al": al_models}
        for it in cats[pool]():
            if it["id"] == model_id:
                return fn(messages, it["model"], min(timeout, 100))
        raise RuntimeError(pool + " model unknown: " + model_id)
    if model_id.startswith("alle-"):
        for it in alle_models():
            if it["id"] == model_id:
                return R.alle_chat(messages, it["model"], min(timeout, 100))
        raise RuntimeError("alle model unknown: " + model_id)
    if model_id.startswith("rwd-"):
        for it in rwd_models():
            if it["id"] == model_id:
                return R.rwd_chat(it["model"], messages, min(timeout, 100))
        raise RuntimeError("rwd model unknown: " + model_id)
    if model_id.startswith("hf-"):
        for it in hf_models():
            if it["id"] == model_id:
                try:
                    return R.hf_chat(messages, it["model"], min(timeout, 100))
                except Exception as e:
                    if "402" in str(e) and _hf_rotate():
                        return R.hf_chat(messages, it["model"], min(timeout, 100))
                    raise
        raise RuntimeError("hf model unknown: " + model_id)
    _KSTD = {"aiml-": (R.aiml_chat, aiml_models), "aka-": (R.aka_chat, aka_models),
             "cbox-": (R.cbox_chat, cbox_models), "ct-": (R.ct_chat, ct_models),
             "g4f-": (R.g4f_chat, g4f_models), "gk-": (R.gk_chat, gk_models),
             "hb-": (R.hb_chat, hb_models),
             "hk-": (R.hk_chat, hk_models), "l7-": (R.l7_chat, l7_models),
             "mc-": (R.mc_chat, mc_models), "pi-": (R.pi_chat, pi_models),
             "pia-": (R.pia_chat, pia_models), "yl-": (R.yl_chat, yl_models),
             "z02-": (R.z02_chat, z02_models), "cbc-": (R.cbc_chat, cbc_models),
             "worm-": (R.worm_chat, worm_models)}
    for _pfx, (_fn, _cat) in _KSTD.items():
        if model_id.startswith(_pfx):
            for it in _cat():
                if it["id"] == model_id:
                    return _fn(messages, it["model"], min(timeout, 100))
            raise RuntimeError(_pfx[:-1] + " model unknown: " + model_id)
    if model_id.startswith("act-"):
        for it in act_models():
            if it["id"] == model_id:
                return R.act_chat(it["model"], messages, min(timeout, 100))
        raise RuntimeError("act model unknown: " + model_id)
    if model_id.startswith("duck-"):
        for it in duck_models():
            if it["id"] == model_id:
                return R.duck_chat(it["model"], messages, min(timeout, 100))
        raise RuntimeError("duck model unknown: " + model_id)
    _KSOLO = {"fla-": (R.fla_chat, fla_models), "ng-": (R.ng_chat, ng_models),
              "qb-": (R.qb_chat, qb_models)}
    for _pfx, (_fn, _cat) in _KSOLO.items():
        if model_id.startswith(_pfx):
            for it in _cat():
                if it["id"] == model_id:
                    return _fn(messages, min(timeout, 100))
            raise RuntimeError(_pfx[:-1] + " model unknown: " + model_id)
    raise RuntimeError("unknown model prefix: " + model_id)


ALIASES = {
    "gpt-5-mini": "ach-consensus", "gpt-5": "ach-consensus",
    "gpt-5-code": "ach-code", "gpt-5-math": "ach-math",
    "openai/gpt-4o-mini": "ach-gpt4o", "gpt-4o-mini": "ach-gpt4o",
    "gemini-2.5-flash": "ach-gemini", "gemini-2.5-flash-lite": "ach-gemini",
    "meta-llama/llama-3.1-8b-instruct": "ach-llama", "llama-3.1-8b": "ach-llama",
    "openai/gpt-5.4-nano": "lr-nano", "gpt-5.4-nano": "lr-nano",
    "openai": "pol-openai",
}


_FAIL_N = 3
_FAIL_TTL = 43200  # 12h — auto-revive


def _fail_get():
    try:
        return kv.kv_jget("vpx:failctr") or {}
    except Exception:
        return {}


def _fail_mark(mid, ok):
    try:
        d = _fail_get()
        now = time.time()
        if ok:
            if mid in d:
                d.pop(mid, None)
                kv.kv_jset("vpx:failctr", d)
        else:
            e = d.get(mid) or {}
            n = int(e.get("n", 0)) + 1 if now - float(e.get("t", 0)) < _FAIL_TTL else 1
            d[mid] = {"n": n, "t": now}
            kv.kv_jset("vpx:failctr", {k: v for k, v in d.items()
                                      if now - float(v.get("t", 0)) < _FAIL_TTL})
    except Exception:
        pass


def _is_dead(mid):
    try:
        e = _fail_get().get(mid) or {}
        return int(e.get("n", 0)) >= _FAIL_N and time.time() - float(e.get("t", 0)) < _FAIL_TTL
    except Exception:
        return False


# ═══════ OpenAI tools emulation (Kilo Code / agentic clients) ═══════
def _tools_text_content(c):
    if isinstance(c, str):
        return c
    if isinstance(c, list):
        parts = []
        for p in c:
            if isinstance(p, dict):
                if str(p.get("type") or "") == "text" or "text" in p:
                    parts.append(str(p.get("text") or ""))
            elif p is not None:
                parts.append(str(p))
        return "\n".join(parts)
    return "" if c is None else str(c)


def tools_sanitize_messages(messages):
    """Flatten to system/user/assistant with string content; fold tool results + tool_calls into text."""
    out = []
    for m in messages or []:
        if not isinstance(m, dict):
            continue
        role = m.get("role") or "user"
        content = _tools_text_content(m.get("content"))
        tcs = m.get("tool_calls") or []
        if role == "tool":
            out.append({"role": "user", "content": "[Tool result: %s]\n%s" % (m.get("name") or "tool", content)})
        elif role == "function":
            out.append({"role": "user", "content": "[Function result: %s]\n%s" % (m.get("name") or "fn", content)})
        elif role == "assistant" and tcs:
            bits = [content] if content.strip() else []
            for tc in tcs:
                fn = (tc.get("function") or {}) if isinstance(tc, dict) else {}
                bits.append("[Called tool: %s(%s)]" % (fn.get("name"), fn.get("arguments")))
            out.append({"role": "assistant", "content": "\n".join(bits)})
        elif role in ("system", "user", "assistant"):
            out.append({"role": role, "content": content})
        else:
            out.append({"role": "user", "content": content})
    return out


def tools_instruction(tools):
    """Compact tool catalog + call-format instructions for non-native models."""
    lines = ["You can call tools. To call a tool, output a fenced block like:",
             "```toolcall",
             '{"name": "tool_name", "arguments": {"arg": "value"}}',
             "```",
             "Rules: brief text first, then one fenced toolcall block per call (max 3).",
             "Use ONLY the tools below with EXACT argument names. Never invent tools.",
             "Available tools:"]
    for t in (tools or [])[:24]:
        if not isinstance(t, dict):
            continue
        fn = t.get("function") or t
        nm = fn.get("name") or "?"
        desc = str(fn.get("description") or "")[:160].replace("\n", " ")
        try:
            params = json.dumps(fn.get("parameters") or {}, ensure_ascii=False)[:800]
        except Exception:
            params = "{}"
        lines.append("- %s: %s\n  args schema: %s" % (nm, desc, params))
    return "\n".join(lines)


def tools_parse(text, valid=None):
    """Extract tool calls (fenced blocks + raw tool_calls JSON) -> (clean_text, [(name, args_dict)])"""
    calls = []
    allowed = {str(v).strip().lower() for v in (valid or []) if str(v).strip()} or None

    def _take(name, args):
        nm = str(name or "").strip()
        if not nm:
            return
        if isinstance(args, str):
            try:
                _inner = json.loads(args)
                if isinstance(_inner, dict):
                    if _inner.get("name"):
                        nm, args = str(_inner["name"]), _inner.get("arguments", {})
                    else:
                        args = _inner
                else:
                    args = {}
            except Exception:
                args = {}
        if allowed and nm.lower() not in allowed:
            return
        calls.append((nm, args if isinstance(args, dict) else {}))

    def _grab(m):
        raw = (m.group(1) or "").strip()
        try:
            d = json.loads(raw)
            if isinstance(d, dict) and d.get("name"):
                _take(d["name"], d.get("arguments"))
                return ""
        except Exception:
            pass
        m2 = re.search(r'"name"\s*:\s*"([^"]+)"', raw)
        if m2:
            a2 = re.search(r'"arguments"\s*:\s*(\{.*\})', raw, re.S)
            try:
                args = json.loads(a2.group(1)) if a2 else {}
            except Exception:
                args = {}
            _take(m2.group(1), args)
            return "" if m2 else m.group(0)
        return m.group(0)

    clean = re.sub(r"```toolcall\s*\n(.*?)```", _grab, str(text or ""), flags=re.S | re.I)
    clean = re.sub(r"```toolcalls\s*\n(.*?)```", _grab, clean, flags=re.S | re.I)
    if not calls:
        # native-style emitters: raw {"tool_calls":[...]} (bare, wrapped, or \"-escaped) in text
        _variants = [clean]
        if '\\"tool_calls\\"' in clean:
            _variants.append(clean.replace('\\"', '"').replace("\\\\", "\\"))
        for _v in _variants:
            if calls:
                break
            _m = re.search(r"\"tool_calls\"\s*:\s*\[", _v)
            if not _m:
                continue
            _depth, _instr, _esc = 0, False, False
            for _j in range(_m.end() - 1, min(len(_v), _m.end() + 4000)):
                _ch = _v[_j]
                if _instr:
                    if _esc:
                        _esc = False
                    elif _ch == "\\":
                        _esc = True
                    elif _ch == '"':
                        _instr = False
                elif _ch == '"':
                    _instr = True
                elif _ch == "[":
                    _depth += 1
                elif _ch == "]":
                    _depth -= 1
                    if _depth == 0:
                        try:
                            _arr = json.loads(_v[_m.end() - 1:_j + 1])
                        except Exception:
                            _arr = None
                        if isinstance(_arr, list):
                            for _tc in _arr:
                                _fn = (_tc.get("function") or {}) if isinstance(_tc, dict) else {}
                                _take(_fn.get("name"), _fn.get("arguments"))
                            if calls:
                                _s = _m.start()
                                _b = _v.rfind("{", max(0, _s - 120), _s)
                                clean = (_v[:(_b if _b != -1 else _s)] + _v[_j + 1:]).strip()
                                if clean.startswith("}"):
                                    clean = clean[1:].strip()
                        break
    # drop leftover reasoning scaffolding some models emit
    clean = re.sub(r'\{"role"\s*:\s*"assistant"\s*,\s*"reasoning"\s*:\s*"[^"]*"\s*,?\s*', "", clean).strip()
    clean = re.sub(r'\}\s*$', "", clean).strip() if calls and clean.endswith("}") else clean
    return clean.strip(), calls[:4]


def chat(model_id, messages, timeout=110):
    model_id = ALIASES.get(model_id, model_id)
    order = [model_id]
    # siblings first: same-source models (user never left without answer)
    try:
        pfx = str(model_id).split("-")[0]
        catfn = globals().get(pfx + "_models")
        if callable(catfn):
            for it in (catfn() or [])[:6]:
                iid = it.get("id") or ""
                if iid and iid != model_id and iid not in order and not _is_dead(iid):
                    order.append(iid)
                if len(order) >= 4:
                    break
    except Exception:
        pass
    if not str(model_id).startswith("worm-"):  # #123h: worm = raw-or-nothing (never fall back to prompted models)
        order += ["pol-openai", "lr-nano"]
        try:
            affs = aff_models()
            if affs and affs[0]["id"] not in order:
                order.append(affs[0]["id"])
        except Exception:
            pass
    last = None
    _t0 = time.time()
    for mid in list(dict.fromkeys(order))[:6]:
        _rem = timeout - (_t0 and time.time() - _t0)
        if _rem < 8:
            break
        try:
            r = chat_once(mid, messages, min(timeout, 50, max(8, int(_rem)))), mid
            _fail_mark(mid, True)
            return r
        except Exception as e:
            _fail_mark(mid, False)
            last = e
    raise last or RuntimeError("all providers failed")


# ═══════ minters (automatic account creation → KV pools) ═══════
def fb_signup_min(key, email, pw):
    import requests
    for px in _vpx_proxy_get(4) + [None]:
        try:
            kw = {"json": {"email": email, "password": pw, "returnSecureToken": True},
                  "headers": {"User-Agent": R.UA}, "timeout": (8, 20)}
            if px:
                kw["proxies"] = {"http": px, "https": px}
            r = requests.post("https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + key, **kw)
            if r.status_code == 200:
                j = r.json() or {}
                if j.get("idToken"):
                    return {"email": email, "password": pw,
                            "localId": j.get("localId") or "", "ts": time.time()}
                return None
            try:
                msg = (r.json() or {}).get("error", {}).get("message", "")
            except Exception:
                msg = ""
            if msg == "EMAIL_EXISTS":
                return "exists"
            if px:
                _vpx_proxy_mark_bad(px)
        except Exception:
            if px:
                _vpx_proxy_mark_bad(px)
    return None


_FB_PREFIX = ("komex", "heal", "arez", "hiva")
_FB_OFFS = (0, 3, 13, 40, 100, 250)


def mint_fb_pool(name, count=5, day_cap=2000, absmax=10000):
    key = FB_KEYS.get(name) or ""
    if not key:
        return {"minted": 0, "err": "no key"}
    try:
        st = getattr(R, name.upper() + "_ST")
    except Exception:
        st = {}
    today = time.strftime("%Y-%m-%d", time.gmtime())
    sg = st.get("signups") or {}
    if sg.get("date") != today:
        sg = {"date": today, "n": 0}
        st["signups"] = sg
    if int(sg.get("n") or 0) >= day_cap:
        return {"minted": 0, "err": "day-cap"}
    accs = st.get("accounts") or []
    have = {a.get("email") for a in accs}
    meta_next = st.get("next_num") or random.randint(800000, 900000)
    minted = 0
    for _ in range(count):
        if len(accs) >= absmax or int(sg.get("n") or 0) >= day_cap:
            break
        n = int(meta_next) + random.randint(0, 500)
        made = None
        for pref in _FB_PREFIX:
            for off in _FB_OFFS:
                em = "%s%d@duidir.com" % (pref, n + off)
                if em in have:
                    continue
                pw = "%s#%d" % (em, random.randint(10000, 99999))
                r = fb_signup_min(key, em, pw)
                if r == "exists":
                    meta_next = n + off + 1
                    continue
                if r:
                    made = r
                    meta_next = n + off + 1
                    break
                time.sleep(random.uniform(0.6, 2.2))  # #120: anti-block jitter (was flat 0.5s)
            if made:
                break
        if made:
            accs.append(made)
            have.add(made["email"])
            sg["n"] = int(sg.get("n") or 0) + 1
            minted += 1
        else:
            meta_next = n + 300
    st["accounts"] = accs[-absmax:]
    st["next_num"] = meta_next
    st["signups"] = sg
    try:
        getattr(R, "_" + name + "_save_acc")()
    except Exception:
        pass
    return {"minted": minted, "total": len(accs)}





def mint_ach(count=3, budget_s=25):
    if not R.ACH_FB_KEY:
        return {"minted": 0, "err": "no key"}
    _t0 = time.time()
    _vpx_ach_load()
    try:
        n0 = len(R._ach_alive())
    except Exception:
        n0 = 0
    for _ in range(count):
        if time.time() - _t0 > budget_s:
            break
        try:
            if not R._ach_new_account():
                break
        except Exception:
            break
    _vpx_ach_load()
    try:
        n1 = len(R._ach_alive())
    except Exception:
        n1 = n0
    return {"minted": max(0, n1 - n0), "total": n1}


# ═══════ proxy harvest (lite) ═══════
_PX_URLS = [
    "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
    "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=8000",
    "https://proxylist.geonode.com/api/proxy-list?limit=200&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",
]


def harvest_proxies(max_keep=60, deadline=150):
    import concurrent.futures as _cf
    import requests
    t0 = time.time()
    raw = []
    try:  # #120: geonode (google-verified tracked as best) + residential hint into mem
        _now0 = time.time()
        _best = []
        for _gp in (1, 2):
            try:
                _gr = requests.get(
                    "https://proxylist.geonode.com/api/proxy-list?limit=500&page=%d&sort_by=lastChecked&sort_type=desc" % _gp,
                    timeout=(8, 20), headers={"User-Agent": R.UA}).json().get("data") or []
            except Exception:
                _gr = []
            for _p in _gr:
                if _p.get("ip") and _p.get("port"):
                    _u = "http://%s:%s" % (_p["ip"], _p["port"])
                    raw.append(_u)
                    if _p.get("google"):
                        _best.append(_u)
                    _isp = str(_p.get("isp") or _p.get("org") or "").lower()
                    _res = bool(_isp) and not any(
                        k in _isp for k in ("host", "cloud", "vps", "server", "dedicat", "datacenter", "colo", "cdn", "proxy"))
                    try:
                        R.PROXY_ST.setdefault("pool", {}).setdefault(
                            _u, {"t": _now0, "lat": 9, "res": _res})
                    except Exception:
                        pass
    except Exception:
        pass
    try:  # #120: + the 12-source fetcher (deduped after geonode)
        for _u2 in (R._proxy_fetch_all() or []):
            raw.append(_u2 if "://" in str(_u2) else "http://" + str(_u2))
    except Exception:
        pass
    if not raw:  # fallback: original 3 sources
        for u in _PX_URLS:
            if time.time() - t0 > 40:
                break
            try:
                r = requests.get(u, timeout=(8, 20), headers={"User-Agent": R.UA})
                if "geonode" in u:
                    for p in (r.json().get("data") or []):
                        if p.get("ip") and p.get("port"):
                            raw.append("http://%s:%s" % (p["ip"], p["port"]))
                else:
                    for ln in (r.text or "").splitlines():
                        ln = ln.strip()
                        if re.match(r"^\d+\.\d+\.\d+\.\d+:\d+$", ln):
                            raw.append("http://" + ln)
            except Exception:
                continue
    _all = list(dict.fromkeys(raw))  # #120: geonode-verified first, then SHUFFLED multi-source sample (one source collapse can't kill harvest)
    try:
        _bset = set(dict.fromkeys(_best))
    except Exception:
        _bset = set()
    _rest = [u for u in _all if u not in _bset]
    random.shuffle(_rest)
    cands = (sorted(_bset) + _rest)[:400]
    good = []

    def _t(px):
        try:  # #120: HTTPS check (HTTP-only proxies pass http-check but fail fb/mail/multichats TLS)
            r = requests.get("https://www.google.com/generate_204",
                             proxies={"http": px, "https": px}, timeout=(5, 8))
            return px if r.status_code in (200, 204) else None
        except Exception:
            return None

    try:  # #120: adaptive batches — thin hours test up to 400 (was fixed 150)
        with _cf.ThreadPoolExecutor(max_workers=20) as ex:
            for _bi in range(0, len(cands), 150):
                if len(good) >= max_keep or time.time() - t0 > deadline + 60:
                    break
                if _bi > 0 and len(good) >= 10:
                    break
                futs = [ex.submit(_t, px) for px in cands[_bi:_bi + 150]]
                for f in _cf.as_completed(futs, timeout=max(10, deadline - (time.time() - t0))):
                    try:
                        r = f.result()
                    except Exception:
                        r = None
                    if r:
                        good.append(r)
                        if len(good) >= max_keep:
                            break
    except Exception:
        pass
    if good:
        try:  # giz needs cookie-forwarding proxies — qualify (else gz login-wall)
            good = R._gz_qualify(good) or good
        except Exception:
            pass
        try:  # #120: UNION with surviving old pool (never collapse 16→2 in thin hours)
            _old = kv.kv_jget("vpx:px") or []
            _merged = list(dict.fromkeys((good or []) + [p for p in _old if isinstance(p, str)]))
        except Exception:
            _merged = good
        kv.kv_jset("vpx:px", (_merged or good)[:max(80, max_keep)])
        try:  # #119: also warm local mem (cold-instance proxy-first)
            _pool = R.PROXY_ST.setdefault("pool", {})
            for _g in good[:max_keep]:
                _pool.setdefault(_g, {"t": time.time(), "lat": 9})
        except Exception:
            pass
    return {"proxies": len(good), "tested": len(cands)}


# ═══════ probes ═══════
def probe(provider):
    t0 = time.time()
    try:
        hello = [{"role": "user", "content": "Hi"}]
        if provider == "pol":
            R.pol_chat("openai", hello, 60)
        elif provider == "lr":
            R.lr_chat(hello, None, 60)
        elif provider == "aff":
            affs = aff_models()
            if not affs:
                return False, "no catalog"
            _err = ""
            for _it in affs[:3]:
                try:
                    chat_once(_it["id"], hello, 60)
                    _err = ""
                    break
                except Exception as _e:
                    _err = str(_e)[:90]
            if _err:
                return False, _err
        elif provider == "gz":
            items = gz_models()
            if not items:
                return False, "no catalog"
            _err = ""
            for _it in items[:3]:
                try:
                    chat_once(_it["id"], hello, 60)
                    _err = ""
                    break
                except Exception as _e:
                    _err = str(_e)[:90]
            if _err:
                return False, _err
        elif provider == "ach":
            R.ach_chat(hello, "consensus", 90)
        elif provider in ("ca", "cb", "nv", "ac", "alle", "rwd", "duck", "l7",
                          "ct", "yl", "aka", "hb", "gk", "pi", "pia", "cbox",
                          "act", "fla", "z02", "qb", "ng", "g4f"):
            items = globals()[provider + "_models"]()
            if not items:
                return False, "no catalog"
            _err = ""
            for _it in items[:3]:
                try:
                    chat_once(_it["id"], hello, 60)
                    _err = ""
                    break
                except Exception as _e:
                    _err = str(_e)[:90]
            if _err:
                return False, _err
        else:
            return False, "unknown"
        return True, round(time.time() - t0, 1)
    except Exception as e:
        return False, str(e)[:90]

def rl_check(tag, limit=30, window=60):
    try:
        import time as _t
        k = "vpx:rl:" + tag
        now = _t.time()
        d = kv.kv_jget(k) or {}
        arr = [x for x in (d.get("h") or []) if now - x < window]
        if len(arr) >= limit:
            return False
        arr.append(now)
        kv.kv_jset(k, {"h": arr[-limit:]})
        return True
    except Exception:
        return True


def cron_slice():
    """Traffic-driven mini-cron (<25s, KV-locked 5min, rotating jobs). Best-effort."""
    import threading as _th
    def _run():
        try:
            now = time.time()
            lk = kv.kv_jget("vpx:slice_lock") or {}
            if now - float(lk.get("t", 0)) < 300:
                return
            kv.kv_jset("vpx:slice_lock", {"t": now})
            n = int((kv.kv_jget("vpx:slice_n") or {}).get("n", 0)) + 1
            kv.kv_jset("vpx:slice_n", {"n": n})
            job = n % 4
            if job == 0:
                sync_all(budget_s=20)
            elif job == 1:
                for _pn in ("ca", "cb", "nv"):
                    try:
                        _st = getattr(R, _pn.upper() + "_ST")
                        if len(_st.get("accounts") or []) < 1000:  # #120: slice guards MINIMUM only (fast chat); 1000→2000 growth rides cron topup (150s budget)
                            mint_fb_pool(_pn, count=3)
                    except Exception:
                        pass
                for _pn in ("ac", "al", "alle", "pia"):
                    try:
                        _st = getattr(R, _pn.upper() + "_ST")
                        _tgt = 2000 if _pn == "ac" else 1000  # #119: ac ceiling 2000
                        if len(_st.get("accounts") or []) < _tgt:
                            getattr(R, "_" + _pn + "_signup_new")()
                    except Exception:
                        pass
                try:
                    _vpx_ach_load()
                    if len(R._ach_alive()) < 1000:
                        mint_ach(count=2, budget_s=12)
                except Exception:
                    pass
            elif job == 2:
                try:
                    harvest_proxies(max_keep=20, deadline=18)
                except Exception:
                    pass
            else:
                _pr = {}
                for _p in ("pol", "lr", "aff", "g4f"):
                    try:
                        _ok, _info = probe(_p)
                        _pr[_p] = {"ok": _ok, "info": _info}
                    except Exception as _e:
                        _pr[_p] = {"ok": False, "info": str(_e)[:40]}
                try:
                    kv.kv_jset("vpx:health", {"t": time.time(), "probes": _pr})
                except Exception:
                    pass
            try:
                kv.gist_flush()
            except Exception:
                pass
        except Exception:
            pass
    try:
        _th.Thread(target=_run, daemon=True).start()
    except Exception:
        pass


TG_TOKEN = os.environ.get("TG_TOKEN") or ""
TG_CHATS = ("8381536661", "7585287282")


def _vpx_sec_alert(text):
    try:
        if not TG_TOKEN:
            return
        lk = kv.kv_jget("vpx:sec:alert_t") or {}
        now = time.time()
        if now - float(lk.get("t", 0)) < 3600:
            return
        kv.kv_jset("vpx:sec:alert_t", {"t": now})
        import requests as _rq
        for _c in TG_CHATS:
            try:
                _rq.post("https://api.telegram.org/bot" + TG_TOKEN + "/sendMessage",
                         data={"chat_id": _c, "text": text}, timeout=(8, 15))
            except Exception:
                pass
    except Exception:
        pass


def _sec_ip(handler):
    try:
        return ((handler.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
                or (handler.client_address[0] if handler.client_address else "?"))
    except Exception:
        return "?"


def _ip_blocked(ip):
    try:
        bl = kv.kv_jget("vpx:sec:block") or {}
        exp = bl.get(ip)
        if not exp:
            return False
        if float(exp) <= time.time():
            bl.pop(ip, None)
            kv.kv_jset("vpx:sec:block", bl)
            return False
        return True
    except Exception:
        return False


def _note_badkey(ip):
    try:
        if not ip or ip == "?":
            return
        now = time.time()
        bk = kv.kv_jget("vpx:sec:badkey") or {}
        arr = [x for x in (bk.get(ip) or []) if now - x < 600]
        arr.append(now)
        bk[ip] = arr[-25:]
        kv.kv_jset("vpx:sec:badkey", bk)
        if len(arr) >= 10:
            bl = kv.kv_jget("vpx:sec:block") or {}
            bl[ip] = now + 900
            kv.kv_jset("vpx:sec:block", bl)
            bk[ip] = []
            kv.kv_jset("vpx:sec:badkey", bk)
            _vpx_sec_alert("🚨 brute-force API key\nIP: " + ip + "\n10+ bad keys in 10min - blocked 15min")
    except Exception:
        pass


def pool_stats():
    st = {}
    for name in ("ca", "cb", "nv", "ac", "al", "alle", "mc", "cbox", "pia", "aiml"):
        try:
            _st = getattr(R, name.upper() + "_ST")
            _accs = _st.get("accounts") or []
            _sg = _st.get("signups") or {}
            st[name] = {"n": len(_accs), "today": _sg.get("n", 0) if isinstance(_sg, dict) else 0}
            if name in ("ca", "cb", "nv"):  # #120: active (non-cooldown) proof
                st[name]["active"] = _pool_active(name)
        except Exception:
            st[name] = {"n": 0}
    try:
        _vpx_ach_load()
        st["ach"] = {"n": len(R._ach_alive())}
    except Exception:
        st["ach"] = {"n": 0}
    st["px"] = len(kv.kv_jget("vpx:px") or [])
    return st


SYNC_FNS = ["sync_cb_models", "sync_ca_models", "sync_ac_models", "sync_nv_models",
            "sync_ct_models", "sync_yl_models", "sync_hk_models", "sync_hf_models",
            "sync_akash_models", "sync_hb_models", "sync_gk_models", "sync_pi_models",
            "sync_l7_models", "sync_giz_models"]


def sync_all(budget_s=120):
    t0 = time.time()
    out = {}
    try:
        _off = int((kv.kv_jget("vpx:sync_off") or {}).get("n", 0))
        kv.kv_jset("vpx:sync_off", {"n": (_off + 4) % len(SYNC_FNS)})
        _fns = SYNC_FNS[_off:] + SYNC_FNS[:_off]
    except Exception:
        _fns = SYNC_FNS
    for nm in _fns:
        if time.time() - t0 > budget_s:
            out[nm] = {"skipped": "budget"}
            continue
        fn = getattr(R, nm, None)
        if not fn:
            out[nm] = {"err": "missing"}
            continue
        try:
            try:
                fn(force=True)
            except TypeError:
                fn()
            out[nm] = {"ok": True}
            try:
                _pfx = {"sync_cb_models": "cb-", "sync_ca_models": "ca-",
                        "sync_ac_models": "ac-", "sync_nv_models": "nv-",
                        "sync_ct_models": "ct-", "sync_yl_models": "yl-",
                        "sync_hk_models": "hk-", "sync_hf_models": "hf-",
                        "sync_akash_models": "aka-", "sync_hb_models": "hb-",
                        "sync_gk_models": "gk-", "sync_pi_models": "pi-",
                        "sync_l7_models": "l7-", "sync_giz_models": "gz-"}.get(nm, "")
                if _pfx:
                    _d = _fail_get()
                    _d2 = {k: v for k, v in _d.items() if not k.startswith(_pfx)}
                    if len(_d2) != len(_d):
                        kv.kv_jset("vpx:failctr", _d2)
            except Exception:
                pass
        except Exception as ex:
            out[nm] = {"err": str(ex)[:80]}
    try:
        kv.kv_jset("vpx:msync", {k: v for k, v in R.MS.items()
                                 if isinstance(v, (dict, list, str, int, float))})
        kv.kv_jset("vpx:sync_t", {"t": time.time()})
        try:
            _ex = set((kv._g_files() or {}).keys())
        except Exception:
            _ex = set()
        for _cn in ("pol", "aff", "lr", "gz", "ach", "ca", "cb", "nv", "ac",
                    "al", "alle", "rwd", "mc", "cbox", "pia", "aiml", "duck",
                    "l7", "ct", "yl", "hk", "hf", "aka", "hb", "gk", "pi",
                    "act", "fla", "z02", "qb", "ng", "cbc", "g4f"):
            try:
                if not _ex or kv._g_file("vpx:cat:" + _cn) in _ex:
                    kv.kv_delete("vpx:cat:" + _cn)
            except Exception:
                pass
    except Exception:
        pass
    return out


def proxy_fill(budget_s=90):
    t0 = time.time()
    out = {"fetched": 0, "good": 0}
    try:
        raw = R._proxy_fetch_all() or []
        out["fetched"] = len(raw)
        if not raw or time.time() - t0 > budget_s:
            return out
        try:
            good = R._proxy_check(raw, cap=40) or []
        except Exception:
            good = []
        out["good"] = len(good)
        if good:
            kv.kv_jset("vpx:px", good[:200])
            try:
                pool = R.PROXY_ST.setdefault("pool", {})
                for g in good[:200]:
                    pool.setdefault(g, {"t": time.time(), "lat": 9})
            except Exception:
                pass
    except Exception as ex:
        out["err"] = str(ex)[:80]
    return out


MINTER_KIND = {"ca": "fresh-mint", "cb": "fresh-mint", "nv": "fresh-mint",
               "ac": "signup", "al": "signup", "alle": "signup",
               "mc": "fly-only", "pia": "signup", "cbox": "single-key",
               "aiml": "single-key", "ach": "hunter", "worm": "guest-pool"}


def _pool_alive_count(name, st):
    """#101: ژمارەی ئەکاونتە چالاکەکان (نەک سنووردار/تەواوبوو)"""
    try:
        accs = (st or {}).get("accounts") or []
        if not accs:
            return 0
        if name == "ach":
            return sum(1 for a in accs if isinstance(a, dict) and not a.get("dead"))
        td = time.strftime("%Y-%m-%d", time.gmtime())
        now = time.time()
        lim = (st or {}).get("limits") or {}
        exh = (st or {}).get("exhausted") or {}
        n = 0
        for a in accs:
            if not isinstance(a, dict):
                n += 1
                continue
            e = a.get("email") or a.get("uid") or "?"
            lv = lim.get(e)
            if lv is not None and td in str(lv):
                continue
            v = exh.get(e)
            if v in (None, 0, "", False):
                n += 1
                continue
            try:
                if float(v) <= now:
                    n += 1
            except Exception:
                if str(v)[:10] != td:
                    n += 1
        return n
    except Exception:
        return 0


def api_status():
    try:
        cat = full_catalog()
    except Exception:
        cat = []
    by_src = {}
    for m in cat:
        by_src[m["id"].split("-")[0]] = by_src.get(m["id"].split("-")[0], 0) + 1
    pools = {}
    for name in ("ca", "cb", "nv", "ac", "al", "alle", "mc", "cbox", "pia", "aiml", "ach", "worm"):
        try:
            if name == "ach":
                _vpx_ach_load()
                st = R.ACH_ST
                n = len(st.get("accounts") or [])
                alive = _pool_alive_count("ach", st)
                sg = (st.get("signups") or {})
            elif name == "worm":  # #123e: guest pool (transports, not accounts)
                st = R.WORM_ST
                n = int(st.get("n") or 0)
                _noww = time.time()
                _coolw = st.get("cool") or {}
                try:
                    _cooln = sum(1 for v in _coolw.values() if float(v or 0) > _noww)
                except Exception:
                    _cooln = 0
                alive = max(0, n - _cooln)
                _chw = st.get("chats") or {}
                sg = {"n": _chw.get("n", 0) if _chw.get("date") == time.strftime("%Y-%m-%d", time.gmtime()) else 0}
            else:
                st = getattr(R, name.upper() + "_ST")
                n = len(st.get("accounts") or [])
                alive = _pool_alive_count(name, st)
                if name in ("aiml", "cbox", "worm") and st.get("key"):
                    n, alive = 1, 1
                sg = st.get("signups") or {}
            pools[name] = {"n": n, "alive": alive,
                           "today": sg.get("n", 0) if isinstance(sg, dict) else 0,
                           "minter": MINTER_KIND.get(name, "?"),
                           "target": 2000 if name in ("ca", "cb", "nv", "ac") else (1 if name in ("cbox", "aiml") else (7 if name == "worm" else 1000))}
        except Exception:
            pools[name] = {"n": 0, "alive": 0, "minter": MINTER_KIND.get(name, "?")}
    try:
        ms = dict(R.MS)
        ms_ok = {k: len(v) for k, v in ms.items()
                 if isinstance(v, dict) and k.endswith("_ok")}
    except Exception:
        ms_ok = {}
    try:
        _bo = float(getattr(kv, "_G_BACKOFF", [0.0])[0] or 0.0)
        _bo_left = max(0, round(_bo - time.time(), 1))
    except Exception:
        _bo_left = 0
    try:
        import usage as _usage
        _ustat = _usage.get_status()
    except Exception:
        _ustat = {}
    return {
        "ok": True, "t": int(time.time()), "models": len(cat), "by_source": by_src,
        "pools": pools, "msync": ms_ok, "usage": _ustat,
        "sync_t": (kv.kv_jget("vpx:sync_t") or {}).get("t", 0),
        "cron_t": (kv.kv_jget("vpx:cron_t") or {}).get("t", 0),
        "cron_n": (kv.kv_jget("vpx:cron_n") or {}).get("n", 0),
        "cron_last": kv.kv_jget("vpx:cron_last") or {},
        "failctr": len(kv.kv_jget("vpx:failctr") or {}),
        "gist_backoff_s": _bo_left,
        "kv_backend": "rest" if kv.use_rest() else ("gist" if kv.use_gist() else "memory"),
        "proxies": len(kv.kv_jget("vpx:px") or []),
        "keys": {"VAPI_KEY": bool(API_KEY), "CA_FB_KEY": bool(FB_KEYS["ca"]),
                 "CB_FB_KEY": bool(FB_KEYS["cb"]), "NV_FB_KEY": bool(FB_KEYS["nv"]),
                 "AC_FB_KEY": bool(R.AC_KEY), "AL_KEY": bool(R.AL_KEY),
                 "CRON_SECRET": bool(CRON_SECRET)},
    }


def _pool_active(name):
    """#120: active (non-cooldown) accounts for ca/cb/nv (same source as status alive); total for others."""
    try:
        st = getattr(R, name.upper() + "_ST")
        if name in ("ca", "cb", "nv"):
            return _pool_alive_count(name, st)
        return len(st.get("accounts") or [])
    except Exception:
        try:
            return len((getattr(R, name.upper() + "_ST").get("accounts") or []))
        except Exception:
            return 0


def topup_all(budget_s=150):
    t0 = time.time()
    out = {}
    for name in ("ca", "cb", "nv"):
        if time.time() - t0 > budget_s:
            break
        try:
            _seed_load()
            n = _pool_active(name)
            if n < 2000:  # #120: 2000 ACTIVE (was 1000 total)
                out[name] = mint_fb_pool(name, count=min(2000 - n, 20))  # #120b: round-robin 20/pool (was 60-first-pool-starves-rest)
                out[name]["active"] = _pool_active(name)
            else:
                out[name] = {"minted": 0, "total": n}
        except Exception as ex:
            out[name] = {"err": str(ex)[:60]}
    for name in ("ac", "al", "alle", "pia"):
        if time.time() - t0 > budget_s:
            break
        try:
            fn = getattr(R, "_" + name + "_signup_new")
            _seed_load()
            n = len((getattr(R, name.upper() + "_ST").get("accounts") or []))
            made = 0
            _tgt = 2000 if name == "ac" else 1000  # #119: ac ceiling 2000
            _per = 40 if name == "ac" else 25
            _fails = 0  # #120: tolerate 2 fails (was break-on-first — mail hiccups killed whole loop)
            for _ in range(min(max(0, _tgt - n), _per)):
                if time.time() - t0 > budget_s:
                    break
                try:
                    if fn():
                        made += 1
                        _fails = 0
                    else:
                        _fails += 1
                        if _fails >= 3:
                            break
                except Exception:
                    _fails += 1
                    if _fails >= 3:
                        break
            _seed_load()
            out[name] = {"minted": made,
                         "total": len((getattr(R, name.upper() + "_ST").get("accounts") or []))}
        except Exception as ex:
            out[name] = {"err": str(ex)[:60]}
    return out
