"""Ported providers (mechanical copy from main.py @96cf9cc) — shims in shim.py"""
import base64, hashlib, json, os, random, re, threading, time, uuid
import requests
import subprocess

def _sys_keep(msgs, n=19):
    """#94U25: کورتکردنەوەی مێژوو بەبێ فەوتاندنی system — هەموو system ەکان + دوایین N"""
    try:
        msgs = list(msgs or [])
    except Exception:
        return []
    sys_m = [m for m in msgs if isinstance(m, dict) and m.get("role") == "system"]
    rest = [m for m in msgs if not (isinstance(m, dict) and m.get("role") == "system")]
    if len(rest) > n:
        rest = rest[-n:]
    return sys_m + rest

def _sys_txt(msgs, cap=32000):
    """#94U25+#94U26+#94U28: دەقی system ەکان — تا 32k (هەڵەی باسکەند → fallback؛ بڕینی بێدەنگ قەدەغە)"""
    try:
        return " ".join(str(m.get("content") or "") for m in (msgs or []) if isinstance(m, dict) and m.get("role") == "system")[:cap]
    except Exception:
        return ""

def pol_chat(model, history, timeout=110):
    """پرسیار بۆ pollinations — وەڵامی تەواو دەگەڕێنێتەوە (لەگەڵ دووبارەهەوڵ بۆ 429)"""
    msgs = _sys_keep(history, 19)  # #94U25
    last = "وەڵامێک نەگەڕایەوە"
    for attempt in range(3):
        try:
            r = requests.post(POL_URL, json={
                "model": model,
                "messages": msgs,
                "seed": random.randint(1, 999999),
            }, timeout=(15, timeout), headers={
                "Content-Type": "application/json",
                "User-Agent": UA,
            })
            if r.status_code == 429:
                last = "طلبات كثيرة بسرعة — انتظر قليلا وحاول مجددا."
                time.sleep(6 + 4 * attempt)
                continue
            if not r.ok:
                last = f"خطأ في الخادم البديل ({r.status_code})"
                time.sleep(2)
                continue
            ans = (r.text or "").strip()
            if ans:
                return ans
            time.sleep(2)
        except Exception as e:
            last = str(e)
            time.sleep(2)
    raise RuntimeError(last)

class EMError(Exception):
    def __init__(self, msg, code=None):
        super().__init__(msg)
        self.code = code



def gz_chat(messages, model_id, timeout=90, cheap=False):  # #95U1؛ #95U3: cheap=probe هەرزان
    """چاتی GizAI — session ی نەناسراو ← infer → {"status":"completed","output":…}؛ #94U50: 429/401 → سێشن+پرۆکسی نوێ"""
    import time as _t
    if _t.time() < _GZ_BADC.get(model_id, 0):
        raise EMError("gz: cooldown")
    try:
        _gz_mem_load()
    except Exception:
        pass
    _ck95 = None
    try:  # #95U3: کاشی پرۆمپتی کورت (کۆنتێکست-تەواو، نەک تەنها دوا-نامە)
        _lu95 = next((m.get("content") or "" for m in reversed(messages) if m.get("role") != "system" and m.get("content")), "")
        if _lu95 and len(_lu95) <= 40 and _lu95 != "تەنها بە یەک وشە وەڵام بدەوە: باشم":
            import hashlib as _h95
            _ctx95 = _h95.md5(repr([(m.get("role"), (m.get("content") or "")[:200]) for m in messages]).encode()).hexdigest()[:12]
            _ck95 = (model_id, _ctx95)
            _hit95 = _GZ_CACHE.get(_ck95)
            if _hit95 and _t.time() - _hit95[1] < 300 and not cheap:
                return _hit95[0]
    except Exception:
        pass
    hist = _sys_keep([{"type": (m.get("role") or "user"), "content": m.get("content") or ""}
                        for m in messages if m.get("content")], 11)
    if not hist:
        raise EMError("gz: هیچ نامە")
    _last = EMError("gz: شکست")
    _allpx = _gz_qualify(_GZ_SEEDS + _px_list(10)[1:])  # #95U3: 8→10  # #94U60+61: seeds + حەوز → تەنها cookie-forward
    try:
        random.shuffle(_allpx)  # #94U54: هەر خولێک IP ی جیاواز
    except Exception:
        pass
    _now60 = _t.time()
    _use = [_p for _p in _allpx if _now60 > _GZ_WALL.get(_p, 0) and _now60 > _GZ_BURNED.get((_p, model_id), 0)]
    try:  # #94U60: GOOD-first (<6 کاتژمێر)
        _use.sort(key=lambda _p: 0 if _now60 - _GZ_GOOD.get(_p, 0) < 21600 else 1)
    except Exception:
        pass
    if cheap:  # #95U3: probe هەرزان — دایرێکت + باشترین 1
        _loop = [None] + (_use[:1] if _use else _allpx[:1])
    else:
        _loop = [None] + (_use if len(_use) >= 2 else _allpx[:2])  # دایرێکت یەکەم + proxy ـەکان
    _dead95 = _t.time() + min(timeout, 90)  # #95U1
    for _px in _loop:
        _rem95 = _dead95 - _t.time()  # #95U1
        if _rem95 <= 6:
            _last = EMError("gz: deadline")
            break
        try:
            s = requests.Session()
            s.headers.update({"User-Agent": GZ_UA, "Content-Type": "application/json",
                              "Origin": GZ_BASE, "Referer": GZ_BASE + "/assistant?mode=chat&baseModel=dynamic"})
            if _px:
                s.proxies.update({"http": _px, "https": _px})
            s.cookies.set("pfb9", GZ_PFB9, domain="www.giz.ai")
            r0 = s.post(GZ_BASE + "/api/data/spaces/spaceServer.createAnonymousSession",
                        json={"visitorId": _gz_rid(32), "session": {"mode": "chat", "shared": False,
                              "modeInput": {"baseModel": "dynamic", "settings": {"character": "AI", "responseMode": "text"},
                              "reasoning": {"level": "low", "mode": "default"}, "context": "general",
                              "reference": "auto", "showChoices": False}}}, timeout=(10, min(25, max(8, int(_rem95)))))  # #95U1
            sid = (r0.json() or {}).get("sessionId") if r0.status_code in (200, 201) else None
            if not sid:
                _sm = ""
                try:
                    _sm = " " + str((r0.json() or {}).get("message") or "")[:50]
                except Exception:
                    pass
                _last = EMError(f"gz: session {r0.status_code}{_sm}")
                continue
            inst = _gz_rid(21)
            inf = {"model": model_id,
                   "input": {"messages": hist, "sessionId": sid, "mode": "chat",
                             "settings": {"character": "AI", "responseMode": "text"}, "context": "general"},
                   "subscribeId": _gz_rid(22), "instanceId": inst}
            r = s.post(GZ_BASE + "/api/data/users/inferenceServer.infer", json=inf,
                       headers={"x-giz-instance-id": inst}, timeout=(15, min(45, max(10, int(_rem95)))))  # #95U1
        except Exception as e:
            if _px:  # #94U53: پرۆکسی مردوو → خراپ (strikes)
                try:
                    _proxy_mark_bad(_px)
                except Exception:
                    pass
            _last = EMError(f"gz: {str(e)[:60]}")
            continue
        if r.status_code in (429, 401, 403):
            _msg = ""
            try:
                _msg = (r.json() or {}).get("message") or ""
            except Exception:
                pass
            if "pay-as-you-go" in _msg:  # #94U51: مۆدێل پارەدارە — لە کاتالۆگ لابەرە
                try:
                    if _GZ_SYNC.get("catalog", {}).pop(model_id, None) is not None:
                        print(f"[GZ] پارەدار لابرا: {model_id}", flush=True)
                except Exception:
                    pass
                raise EMError(f"gz: {model_id} paywalled")
            if _px:  # #94U60: بیرگەوری — 429=(px,model)/کاتژمێر، 401/403=px/30خولەک
                try:
                    if r.status_code == 429:
                        _GZ_BURNED[(_px, model_id)] = _t.time() + 3700.0
                    else:
                        _GZ_WALL[_px] = _t.time() + 1800.0
                except Exception:
                    pass
            _last = EMError(f"gz: {r.status_code} {_msg[:40]}")
            continue
        if r.status_code != 201 and r.status_code != 200:
            _m2 = ""
            try:
                _m2 = " " + str((r.json() or {}).get("message") or "")[:50]
            except Exception:
                pass
            _last = EMError(f"gz: {r.status_code}{_m2}")  # #94U56؛ #94U57: 400 → IP ی دواتر (loop بەردەوام)
            if r.status_code == 400 and "identity" in _m2.lower():  # #95U5: gated-model (direct) / strip-proxy
                if not _px:
                    try:
                        if _GZ_SYNC.get("catalog", {}).pop(model_id, None) is not None:
                            print(f"[GZ] 🚫 gated لابرا: {model_id} (direct-400 identity)", flush=True)
                    except Exception:
                        pass
                else:
                    try:
                        _GZ_WALL[_px] = _t.time() + 1800.0
                    except Exception:
                        pass
            continue
        try:
            j = r.json()
        except Exception:
            _last = EMError("gz: parse")
            continue
        if (j.get("status") or "completed") != "completed":
            _last = EMError(f"gz: status={j.get('status')}")
            continue
        ans = (j.get("output") or "").strip()
        if not ans:
            _last = EMError("gz: وەڵام بەتاڵ")
            continue
        if _px:  # #94U60: GOOD
            try:
                _GZ_GOOD[_px] = _t.time()
            except Exception:
                pass
        if _ck95:
            try:  # #95U3: کاش + بیرگەوری
                _GZ_CACHE[_ck95] = (ans, _t.time())
                if len(_GZ_CACHE) > 500:
                    _cut95 = _t.time() - 300
                    for _k95 in [_k for _k, _v in _GZ_CACHE.items() if _v[1] < _cut95][:200]:
                        _GZ_CACHE.pop(_k95, None)
            except Exception:
                pass
        try:
            _gz_mem_save()
        except Exception:
            pass
        return ans
    if "429" in str(_last):
        _GZ_BADC[model_id] = _t.time() + GZ_COOLDOWN["quota"]
        raise EMError("gz: کوانتای مۆدێڵ (~١ کاتژمێر)")
    if "401" in str(_last) or "403" in str(_last):
        _GZ_BADC[model_id] = _t.time() + GZ_COOLDOWN["login"]
        raise EMError("gz: لۆگین-واڵ")
    try:
        _gz_mem_save()
    except Exception:
        pass
    print(f"[GZ] هەموو IP ـەکان شکستیان هێنا ({len(_loop)} هەوڵ): {_last}", flush=True)
    raise _last

def _px_list(n=3):
    """#94U49: [None, px1, ...] — یەکەم ڕاستەوخۆ، دواتر پرۆکسی تازە بۆ هەر لیمێتی IP"""
    try:
        pxs = [p for p in (_proxy_get(n) or []) if p][:n]
        return [None] + pxs
    except Exception:
        return [None]

class AIFreeError(Exception):
    pass

class AIFreeChat:
    def __init__(self, model, endpoint=None, timeout=120):
        self.model = model
        self.endpoint = endpoint if (endpoint or "").startswith("http") else BASE_URL + (endpoint or "")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": UA,
            "Content-Type": "application/json",
            "Origin": BASE_URL,
            "Referer": BASE_URL + "/chat/" + model,
        })
        self._nonce = ""

    def _fetch_nonce(self):
        n = ""
        try:
            n = self.session.get(BASE_URL + "/api/chat-nonce", timeout=15).json().get("nonce", "")
        except Exception:
            n = ""
        if not n:
            # ماڵپەرەکە نۆنس بەتاڵ دەدات مەگەر سەرەتا سەردانی پەڕەی چات بکرێت (کوکی سێشن)
            try:
                self.session.headers.pop("Content-Type", None)
                self.session.get(BASE_URL + "/chat/" + self.model, timeout=20)
                self.session.headers["Content-Type"] = "application/json"
                n = self.session.get(BASE_URL + "/api/chat-nonce", timeout=15).json().get("nonce", "")
            except Exception:
                n = ""
        return n

    @staticmethod
    def _proof():
        now = int(time.time() * 1000)
        start = now - random.randint(4000, 15000)
        return {"nonce": "", "keystrokeCount": random.randint(20, 120),
                "pasteEvents": 0, "totalTypingTime": now - start,
                "startTime": start, "submitTime": now}

    def chat(self, question, history=None):
        _sys = _sys_txt(history)  # #94U25b: system بخە ناو پرسیار (باسکەندەکە history ڕۆڵەکان پشتگوێ دەخات)
        _q = f"[Instructions: {_sys}]\n\n{question}" if _sys else question
        payload = {
            "model": self.model, "question": _q, "tone": "friendly",
            "format": "paragraph", "file": None,
            "conversationHistory": _sys_keep(history or [], 19),  # #94U25
            "interactionProof": self._proof(),
            "aiRole": "assistant", "aiName": "", "language": "auto",
        }
        last = None
        for attempt in range(3):
            try:
                if not self._nonce:
                    self._nonce = self._fetch_nonce()
                payload["interactionProof"]["nonce"] = self._nonce
                with self.session.post(self.endpoint, json=payload, stream=True,
                                       timeout=(15, self.timeout)) as r:
                    if r.status_code == 429:
                        raise AIFreeError("طلبات كثيرة بسرعة (429) — انتظر قليلا.")
                    if r.status_code in (403, 407, 502, 503):
                        raise ConnectionError(f"داخستن ({r.status_code})")
                    if r.status_code == 409:
                        raise AIFreeError("سێرڤەرەکە ئێستا بەردەست نییە (409).")
                    r.raise_for_status()
                    ctype = r.headers.get("content-type", "")
                    answer = ""
                    if "text/event-stream" in ctype:
                        for raw in r.iter_lines():
                            line = raw.decode("utf-8", errors="replace") if isinstance(raw, bytes) else raw
                            if not line.startswith("data: "):
                                continue
                            d = line[6:].strip()
                            if d == "[DONE]":
                                break
                            try:
                                answer += json.loads(d).get("token", "")
                            except Exception:
                                pass
                    else:
                        answer = (r.json() or {}).get("answer", "")
                    if not answer:
                        raise ConnectionError("aff: وەڵامی بەتاڵ — نۆنسی نوێ پێویستە")
                    return answer
            except AIFreeError:
                raise
            except Exception as e:
                last = e
                self._nonce = ""
                time.sleep(1.2 * (attempt + 1))
        raise ConnectionError(str(last))

def _lr_anon_session():
    """سێشنی نەناسراوی نوێ — هەر سێشن = ١ نامە (بۆیە بۆ هەر داواکارییەک یەک دروست دەکەین)"""
    s = requests.Session()
    s.headers.update({"User-Agent": LR_UA, "Accept-Language": "en"})
    r = s.post(LR_B + "/api/auth/sign-in/anonymous", json={"newUser": True},
               headers={"Origin": LR_B, "Referer": LR_B + "/chat",
                        "Content-Type": "application/json"}, timeout=(10, 20))
    if r.status_code != 200:
        raise EMError(f"lr: signin {r.status_code}")
    return s

def _lr_um(role, text):
    return {"id": str(uuid.uuid4()), "role": role,
            "parts": [{"type": "text", "text": str(text)[:6000]}]}

def lr_chat(messages, model_id=None, timeout=75):
    """#96U3: چاتی lorka — سێشنی نەناسراو + مێژووی تەواو لە یەک داواکاریدا — SSE text-delta"""
    with _LR_SEM:
        sess = _lr_anon_session()
        sys_txt = " ".join(str(m.get("content")) for m in messages if m.get("role") == "system")[:8000]
        rest = [m for m in messages if m.get("role") != "system"][-12:]
        ums = []
        for i, m in enumerate(rest):
            role = "assistant" if m.get("role") == "assistant" else "user"
            txt = str(m.get("content"))
            if i == 0 and sys_txt and role == "user":
                txt = f"[ئاراستەی سیستەم: {sys_txt}]\n{txt}"
            ums.append(_lr_um(role, txt))
        if not ums:
            ums = [_lr_um("user", "سلام")]
        if ums[0]["role"] != "user":
            ums.insert(0, _lr_um("user", sys_txt or "بەردەوامبە"))
        body = {"id": str(uuid.uuid4()), "type": "chat",
                "visitorId": uuid.uuid4().hex, "messages": ums}
        r = sess.post(LR_B + "/api/v2/chat/anonymous", json=body, timeout=(10, timeout),
                      stream=True, headers={"Origin": LR_B, "Referer": LR_B + "/chat",
                                            "Content-Type": "application/json"})
        if r.status_code == 429:
            raise EMError("lr: لیمیت (429)")
        if r.status_code != 200:
            raise EMError(f"lr: HTTP {r.status_code}")
        parts = []
        for raw in r.iter_lines(chunk_size=None):
            ln = raw.decode("utf-8", "ignore").strip()
            if not ln.startswith("data:"):
                continue
            payload = ln[5:].strip()
            if payload == "[DONE]":
                break
            try:
                d = json.loads(payload)
            except Exception:
                continue
            if d.get("type") == "text-delta":
                parts.append(str(d.get("delta") or ""))
            elif d.get("type") == "error":
                raise EMError(f"lr: {str(d.get('errorText') or d.get('message') or 'error')[:80]}")
        out = "".join(parts).strip()
        if not out:
            raise EMError("lr: وەڵامی بەتاڵ")
        return out

def ach_chat(messages, model_key="consensus", timeout=110, depth=0):
    """چاتی AllChat — ڕۆتەیشنی ئەکاونت + دروستکردنی خۆکار لەسەر limitReached"""
    if depth == 0 and not (ACH_ST.get("accounts")):
        _ach_load()
    sys_txt = " ".join(str(m.get("content")) for m in messages if m.get("role") == "system")[:600]
    rest = [m for m in messages if m.get("role") != "system"]
    last = rest[-1] if rest else {"role": "user", "content": "سلام"}
    hist = [{"role": ("user" if m.get("role") == "user" else "assistant"),
             "content": str(m.get("content"))[:1200]} for m in rest[:-1]][-6:]
    umsg = str(last.get("content"))[:6000]
    if sys_txt:
        umsg = f"[رێنمایی کەسایەتی: {sys_txt}]\n\n{umsg}"
    # #97f: SmartRoute → ناچارکردنی COMPLEX بە پێچانەوەی کاتێگۆری — مۆدێلی پریمیۆمی تایبەت
    if model_key in ACH_SMART:
        umsg += ACH_WRAPS.get(model_key, ACH_WRAPS["consensus"])
        timeout = max(int(timeout or 0), 170)
    for _ in range(2):
        acc = _ach_pick()
        if not acc:
            raise EMError("ach: ئەکاونت نەدروست بوو")
        try:
            ans, cm = _ach_call(acc, model_key, umsg, hist, timeout)
            acc["n"] = int(acc.get("n") or 0) + 1
            if int(acc.get("n") or 0) >= ACH_BUDGET:
                acc["dead"] = 1
            with ACH_LOCK:
                _ach_save()
            if cm and cm.get("models"):
                print(f"[ACH] کۆنسێنسۆس: {' + '.join(cm['models'])} | multi={cm.get('multi')} | conf={cm.get('confidence')}", flush=True)
            # #97g: سەرچاوەکانی وێب → بەستەرەوە بە وەڵام
            if model_key == "web" and cm.get("sources"):
                _ln = "\n".join(f"🔗 {(t or 'سەرچاوە')[:48]}: {u}" for t, u in cm["sources"] if u)
                if _ln:
                    ans = ans.rstrip() + "\n\n" + _ln
            return ans
        except _AchLimit as e:
            s = str(e)
            acc["dead"] = 1
            with ACH_LOCK:
                _ach_save()
            if depth == 0:
                na = _ach_new_account()
                if na:
                    return ach_chat(messages, model_key, timeout, depth=1)
            raise EMError(f"ach: {s[:80]}")
        except EMError:
            raise
        except Exception as e:
            if depth == 0:
                acc["dead"] = 1
                with ACH_LOCK:
                    _ach_save()
                na = _ach_new_account()
                if na:
                    return ach_chat(messages, model_key, timeout, depth=1)
            raise EMError(f"ach: {str(e)[:80]}")
    raise EMError("ach: دووبارە بوونەوە سەرکەوتوو نەبوو")





def _gz_mem_load():
    """#95U3: GOOD/BURNED/WALL لە دیسک (deploy بیرگەوری ناسڕێتەوە)"""
    if _GZ_MEM_LD[0]:
        return
    _GZ_MEM_LD[0] = True
    _GZ_MEM_SV[0] = time.time()
    try:
        d = _json_load_safe(os.path.join(DATA_DIR, "gz_mem.json")) or {}
        for _k, _v in (d.get("good") or {}).items():
            _GZ_GOOD[_k] = float(_v)
        for _k, _v in (d.get("wall") or {}).items():
            _GZ_WALL[_k] = float(_v)
        for _k, _v in (d.get("burned") or {}).items():
            _p = _k.split("\x00")
            if len(_p) == 2:
                _GZ_BURNED[(_p[0], _p[1])] = float(_v)
        print(f"[GZ] 🧠 بیرگەوری بارکرا (GOOD {len(_GZ_GOOD)} WALL {len(_GZ_WALL)} BURN {len(_GZ_BURNED)})", flush=True)
    except Exception:
        pass

def _gz_mem_save():
    """#95U3: پاشەکەوت (throttle 60s)"""
    try:
        _now = time.time()
        if _now - _GZ_MEM_SV[0] < 60:
            return
        _GZ_MEM_SV[0] = _now
        _json_save(os.path.join(DATA_DIR, "gz_mem.json"),
                   {"good": dict(_GZ_GOOD), "wall": dict(_GZ_WALL),
                    "burned": {f"{_k[0]}\x00{_k[1]}": _v for _k, _v in _GZ_BURNED.items()}})
    except Exception:
        pass

def _gz_rid(n):
    import secrets as _sc, string as _st
    return "".join(_sc.choice(_st.ascii_letters + _st.digits + "-_") for _ in range(n))

def _gz_qualify(pxs):
    """#94U61: تەنها proxy ـی cookie-forward (httpbin echo) — stripکەرەکان = 400-identity (fail-open)"""
    import concurrent.futures as _cfq
    _now = time.time()
    _fresh = [p for p in pxs if _now - _GZ_PXOK.get(p, 0) < 3600]
    _todo = [p for p in pxs if p not in _fresh]
    if _todo:
        try:  # httpbin خۆی زیندووە؟ (دایرێکت)
            _r0 = requests.get("https://httpbin.org/headers", headers={"User-Agent": GZ_UA}, timeout=(5, 8))
            if _r0.status_code != 200:
                return pxs
        except Exception:
            return pxs
        _tok = _gz_rid(10)
        def _one(px):
            try:
                _r = requests.get("https://httpbin.org/headers", headers={"User-Agent": GZ_UA, "Cookie": f"gzx={_tok}"},
                                  proxies={"http": px, "https": px}, timeout=(5, 8))
                if _r.status_code == 200 and _tok in _r.text:
                    _GZ_PXOK[px] = time.time()
                    return px
            except Exception:
                pass
            return None
        try:
            _exq = _cfq.ThreadPoolExecutor(max_workers=min(len(_todo), 8))
            try:
                _futs = [_exq.submit(_one, p) for p in _todo]
                for _f in _cfq.as_completed(_futs, timeout=30):
                    try:
                        if _f.result():
                            _fresh.append(_f.result())
                    except Exception:
                        pass
            finally:
                _exq.shutdown(wait=False, cancel_futures=True)
        except Exception:
            pass
    return _fresh if _fresh else pxs

def _ach_load():
    d = _json_load_safe(ACH_ACC_FILE) or {}
    ACH_ST["accounts"] = d.get("accounts") or []
    ACH_ST["idx"] = int(d.get("idx") or 0)
    ACH_ST["signups"] = d.get("signups") or {"date": "", "n": 0}

def _ach_save():
    _json_save(ACH_ACC_FILE, {"accounts": ACH_ST.get("accounts") or [],
                               "idx": ACH_ST.get("idx") or 0,
                               "signups": ACH_ST.get("signups") or {"date": "", "n": 0}})

def _ach_new_account():
    """ئەکاونتی تەواوی AllChat: mail.tm → signUp → verify(oobCode) → signIn — ~٢٥ چرکە"""
    today = time.strftime("%Y-%m-%d", time.gmtime())
    with ACH_LOCK:
        sg = ACH_ST.get("signups") or {"date": "", "n": 0}
        if sg.get("date") == today and int(sg.get("n") or 0) >= ACH_DAY_CAP:
            return None
    try:
        sess = requests.Session()
        idtok = uid = em = pw = mtok = None
        for _px in (_proxy_signup_best(4) + [None]):  # #119: proxy-first (direct last)
            try:
                if _px:
                    sess.proxies.update({"http": _px, "https": _px})
                else:
                    sess.proxies.clear()
                em, pw, mtok = _ach_mail_new(sess)
                r = sess.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signUp?key={ACH_FB_KEY}",
                              json={"email": em, "password": pw, "returnSecureToken": True}, timeout=(12, 30))
                d = r.json() or {}
                if d.get("idToken"):
                    idtok, uid = d.get("idToken"), d.get("localId")
                    break
            except Exception:
                continue
        if not idtok:
            print("[ACH] signUp fail (all proxies+direct)", flush=True)
            return None
        # پشتڕاستکردنەوەی ئیمەیڵ — ناچاری (چات 403 email_unverified)
        try:
            sess.post(f"https://identitytoolkit.googleapis.com/v1/accounts:sendOobCode?key={ACH_FB_KEY}",
                      json={"requestType": "VERIFY_EMAIL", "idToken": idtok}, timeout=(12, 30))
            if mtok:
                code = _ach_wait_oob(sess, mtok)
                if code:
                    sess.post(f"https://identitytoolkit.googleapis.com/v1/accounts:update?key={ACH_FB_KEY}",
                              json={"oobCode": code}, timeout=(12, 30))
        except Exception:
            pass
        tok, _ = _ach_fb_login(sess, em, pw)
        acc = {"email": em, "pw": pw, "uid": uid, "tok": tok or idtok,
               "ts": time.time(), "day": today, "n": 0, "dead": 0}
        with ACH_LOCK:
            ACH_ST.setdefault("accounts", []).append(acc)
            _aa = ACH_ST.get("accounts") or []
            if len(_aa) > 1500:  # #119: was 320 (could never reach 1000 alive)
                _lv = [a for a in _aa if not a.get("dead")][-1200:]
                _dd = [a for a in _aa if a.get("dead")][-300:]
                ACH_ST["accounts"] = _lv + _dd
            sg = ACH_ST.get("signups") or {"date": "", "n": 0}
            if sg.get("date") != today:
                sg = {"date": today, "n": 0}
            sg["n"] = int(sg.get("n") or 0) + 1
            ACH_ST["signups"] = sg
            _ach_save()
        print(f"[ACH] ئەکاونتی نوێ: {em[:18]}… (حەوز: {len(_ach_alive())})", flush=True)
        return acc
    except Exception as e:
        print(f"[ACH] new-acct: {str(e)[:80]}", flush=True)
        return None

def _ach_pick():
    accs = _ach_alive()
    if not accs:
        return _ach_new_account()
    a = accs[ACH_ST.get("idx", 0) % len(accs)]
    ACH_ST["idx"] = (ACH_ST.get("idx", 0) + 1) % len(accs)
    return a

class _AchLimit(Exception):
    pass

def _ach_call(acc, model_key, user_msg, history, timeout):
    """یەک داواکاری — دەگەڕێنێتەوە (وەڵام، consensus_meta) — limitReached → _AchLimit"""
    tok = _ach_tok(acc)
    if not tok:
        raise _AchLimit("no-token")
    hdrs = {"Authorization": f"Bearer {tok}", "Content-Type": "application/json", **ACH_ORIG}
    body = {"userId": acc.get("uid"), "conversationId": "new",
            "userMessage": user_msg, "userMessageId": "u-" + uuid.uuid4().hex[:12],
            "assistantMessageId": "a-" + uuid.uuid4().hex[:12],
            "conversationHistory": history, "memoryLimit": 20 if model_key in ACH_SMART else 10}
    if model_key in ACH_SMART:
        ep = "allChatSmartRoute"
        body["mode"] = "smart"
        if model_key == "web":
            body["forceWebSearch"] = True  # #97g: NEWS_RESEARCH → perplexity/sonar + sources
    else:
        ep = "streamGeneralChat"
        body["model"] = ACH_REAL.get(model_key, "google/gemini-2.5-flash-lite")
    r = requests.post(f"{ACH_API}/{ep}", json=body, headers=hdrs, timeout=(12, timeout), stream=True)
    if r.status_code == 429:
        time.sleep(2)
        r = requests.post(f"{ACH_API}/{ep}", json=body, headers=hdrs, timeout=(12, timeout), stream=True)
    if r.status_code in (401, 403):
        raise _AchLimit(f"auth{r.status_code}")
    if r.status_code == 402:
        raise _AchLimit("tier402")
    parts, cmeta = [], None
    r.raw.decode_content = True
    for raw in r.iter_lines(chunk_size=None):
        if not raw:
            continue
        ln = raw.decode("utf-8", "ignore").strip() if isinstance(raw, bytes) else str(raw).strip()
        if not ln.startswith("data:"):
            continue
        p = ln[5:].strip()
        if p == "[DONE]":
            break
        try:
            d = json.loads(p)
        except Exception:
            continue
        t = d.get("type") if isinstance(d, dict) else None
        if t == "content":
            parts.append(str(d.get("content") or ""))
        elif t == "limitReached":
            raise _AchLimit(str(d.get("reason") or "limit"))
        elif t == "error":
            raise _AchLimit(str(d.get("error") or d.get("message") or "err")[:90])
        elif t == "done":
            cm = d.get("consensus_meta") or {}
            md = d.get("metadata") or {}
            srcs = d.get("sources") or []
            if cm or md or srcs:
                cmeta = {"confidence": cm.get("confidence"), "points": (cm.get("consensus_points") or [])[:4],
                         "models": [x for x in (md.get("primaryModel"), md.get("secondaryModel")) if x],
                         "multi": bool(md.get("isMultiModelResponse")),
                         "sources": [(str(s.get("title") or ""), str(s.get("url") or "")) for s in srcs[:4] if s.get("url")]}
            break
    ans = "".join(parts).strip()
    if not ans:
        raise _AchLimit("empty")
    return ans, cmeta

def _json_save(path, obj):
    """#91A1 + #94U3 + #94U19b: نووسینی ATOMIC + شێفرەکردن + دژە-ڕەیس (per-path lock + tmp ی ناوازە)"""
    with _JSON_LOCKS_G:
        _lk = _JSON_LOCKS.setdefault(path, threading.Lock())
    with _lk:
        return _json_save_locked(path, obj)

def _json_load_safe(path, default=None):
    """#91A1 + #94U3: خوێندنەوەی بەهێز — کاڵفامکردنەوەی خۆکار ئەگەر شێفرەکرابێت + .bak"""
    fer = _get_fernet()
    for p in (path, path + ".bak"):
        if not os.path.exists(p):
            continue
        try:
            with open(p, "rb") as f:
                content = f.read()
            if content.startswith(_ENC_MAGIC):
                if fer:
                    dec = fer.decrypt(content[len(_ENC_MAGIC):])
                    return json.loads(dec.decode("utf-8"))
                else:
                    continue
            else:
                return json.loads(content.decode("utf-8"))
        except Exception:
            continue
    return default


def _guerr_new():
    """#106: guerrillamail — سێیەم جێگرەوەی inbox (بێ auth)؛ دەگەڕێنێتەوە (email, sid)"""
    try:
        import requests as _rq
        d = _rq.get("https://api.guerrillamail.com/ajax.php",
                    params={"f": "get_email_address", "ip": "127.0.0.1", "agent": "Mozilla"},
                    timeout=(10, 25)).json() or {}
        if d.get("email_addr") and d.get("sid_token"):
            return d["email_addr"], d["sid_token"]
    except Exception:
        pass
    return None, None


def _guerr_body(sid):
    """#106: دوا نامەی guerrillamail — دەق یان "" """
    try:
        import requests as _rq
        base = "https://api.guerrillamail.com/ajax.php"
        l = _rq.get(base, params={"f": "get_email_list", "offset": 0, "sid_token": sid}, timeout=(10, 25)).json() or {}
        lst = l.get("list") or []
        if not lst or not (lst[0] or {}).get("mail_id"):
            return ""
        d = _rq.get(base, params={"f": "fetch_email", "email_id": lst[0]["mail_id"], "sid_token": sid}, timeout=(10, 25)).json() or {}
        return "%s\n%s" % (d.get("mail_subject") or "", d.get("mail_body") or "")
    except Exception:
        return ""

def _ach_mail_new(sess):
    """ئیمەیڵی کاتی mail.tm — 429 → خستنەوە (٢ جار)"""
    em = "alchat" + uuid.uuid4().hex[:10] + "@uberip.com"
    pw = "Xq" + uuid.uuid4().hex[:12] + "A!"
    for i in range(3):
        try:
            sess.post("https://api.mail.tm/accounts", json={"address": em, "password": pw}, timeout=(12, 30))
            time.sleep(3 if i == 0 else 1)
            for j in range(2):
                rt = sess.post("https://api.mail.tm/token", json={"address": em, "password": pw}, timeout=(12, 30))
                if rt.status_code == 200 and (rt.json() or {}).get("token"):
                    return em, pw, rt.json()["token"]
                time.sleep(25 if rt.status_code == 429 else 4)
            return em, pw, None
        except Exception as e:
            if i == 2:
                print(f"[ACH] mail: {str(e)[:70]}", flush=True)
            time.sleep(5)
    try:  # #106: mail.tm مرد → 1secmail
        em1, sid1 = _guerr_new()
        if em1:
            print(f"[ACH] mail: guerrilla جێگرەوە ✅ {em1[:20]}", flush=True)
            return em1, pw, "guerr:" + sid1
    except Exception:
        pass
    return em, pw, None

def _ach_wait_oob(sess, mtok, want="oobCode="):
    """چاوەڕوانی نامەی Firebase — دەرهێنانی کۆد"""
    if isinstance(mtok, str) and mtok.startswith("guerr:"):  # #106
        try:
            _, sid = mtok.split(":", 1)
        except Exception:
            return None
        for _ in range(12):
            time.sleep(5)
            txt = _guerr_body(sid)
            m = re.search(r'oobCode=([a-zA-Z0-9_\-]+)', txt or "")
            if m:
                return m.group(1)
        return None
    for _ in range(12):
        time.sleep(5)
        try:
            msgs = sess.get("https://api.mail.tm/messages",
                            headers={"Authorization": f"Bearer {mtok}", "Accept": "application/json"},
                            timeout=(12, 25)).json() or []
        except Exception:
            continue
        for it in (msgs if isinstance(msgs, list) else [])[:3]:
            try:
                full = sess.get(f"https://api.mail.tm/messages/{it['id']}",
                                headers={"Authorization": f"Bearer {mtok}", "Accept": "application/json"},
                                timeout=(12, 25)).json() or {}
            except Exception:
                continue
            m = re.search(r'oobCode=([a-zA-Z0-9_\-]+)', (full.get("text") or "") + (full.get("html") and str(full.get("html")) or ""))
            if m:
                return m.group(1)
    return None

def _ach_fb_login(sess, email, pw):
    """لۆگین — idToken ی تازە (بۆ توکنی بەسەڕبوو >٤٠خ)"""
    r = sess.post(f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={ACH_FB_KEY}",
                  json={"email": email, "password": pw, "returnSecureToken": True}, timeout=(12, 30))
    d = r.json() or {}
    return d.get("idToken"), d.get("localId")

def _ach_alive():
    today = time.strftime("%Y-%m-%d", time.gmtime())
    out = []
    for a in (ACH_ST.get("accounts") or []):
        if a.get("dead"):
            continue
        if int(a.get("n") or 0) >= ACH_BUDGET:
            continue
        if a.get("day") != today:
            a["day"], a["n"] = today, 0  # کوانتا ڕۆژانە نەبووە — ژماردنی ناوخۆ تەنیا
        out.append(a)
    return out

def _ach_tok(acc):
    """توکنی تازە ئەگەر بەسەڕبوو (>٣٥خ)"""
    if time.time() - float(acc.get("ts") or 0) < 2100 and acc.get("tok"):
        return acc["tok"]
    try:
        sess = requests.Session()
        tok, _ = _ach_fb_login(sess, acc.get("email") or "", acc.get("pw") or "")
        if tok:
            acc["tok"], acc["ts"] = tok, time.time()
            with ACH_LOCK:
                _ach_save()
            return tok
    except Exception:
        pass
    return acc.get("tok") or ""

def fetch_models(timeout=15):
    """نوێترین مۆدەڵەکان لە aifreeforever"""
    try:
        r = requests.get(BASE_URL + "/api/chat-models", timeout=timeout,
                         headers={"User-Agent": UA})
        models = {}
        for p in r.json().get("pages", []):
            if p.get("available") and p.get("endpoint") and p.get("id"):
                models[p["id"]] = {
                    "name": p.get("name") or p["id"],
                    "endpoint": p["endpoint"],
                }
        return models
    except Exception:
        return {}

def hide_names(items, key="id"):
    """ناوەکان دەشارێتەوە → سێرڤەری یەک، دوو، سێ… (ڕێکخست بە کلیدووشە)"""
    ordered, used = [], set()
    for keys in SERVER_PRIORITY:
        for it in items:
            low = str(it[key]).lower()
            if it[key] not in used and any(k in low for k in keys):
                used.add(it[key])
                ordered.append(it)
                break
    ordered += [it for it in items if it[key] not in used]
    out = []
    for i, it in enumerate(ordered, 1):
        num = KURDISH_NUMS[i - 1] if i <= len(KURDISH_NUMS) else str(i)
        it = dict(it)
        it["name"] = f"الخادم {num}"
        out.append(it)
    return out

def sync_giz_models(force=False):
    """ئۆتۆ-ئەپدێتی GizAI: کاتالۆگی CDN (٦ کاتژمێر) — بێ probe (کوانتا نەسوتێت)؛
    فیلتەر: gateway/* (پارەدار) و free-limit-0 و شاراوە دەر دەکرێن"""
    import time as _t
    if not force and _t.time() - _GZ_SYNC["t"] < 21600:
        return
    try:
        r = requests.get(GZ_CDN, headers={"User-Agent": GZ_UA}, timeout=(10, 40))
        if r.status_code != 200:
            print(f"[GZ-SYNC] catalog {r.status_code}", flush=True)
            return
        cands = _gz_parse_catalog(r.text)
        if not cands:
            print("[GZ-SYNC] parse شکستی هێنا — کاتالۆگی کۆن دەمێنێتەوە", flush=True)
            return
        cat = {}
        for c in cands:
            v = c["value"]
            if v in GZ_SKIP or v.startswith("gateway/") or c.get("free0"):
                continue
            cat[v] = c["label"]
        # #91A12: NEVER-SHRINK — ئەگەر نوێ < 70% ی کۆن → کۆن بمێنێتەوە (flake ی سایت)
        _oldc = _GZ_SYNC.get("catalog") or {}
        if _oldc and len(cat) < len(_oldc) * 0.7:
            print(f"[GZ-SYNC] ⚠️ نوێ زۆر بچووکە ({len(cat)} < 70% ی {len(_oldc)}) — کۆن پارێزرا", flush=True)
            return
        _GZ_SYNC["catalog"] = cat
        _GZ_SYNC["t"] = _t.time()
        print(f"[GZ-SYNC] کاتالۆگ {len(cands)} → تۆمارکراو {len(cat)}", flush=True)
    except Exception as e:
        print(f"[GZ-SYNC] {str(e)[:80]}", flush=True)

def _tmp_inbox():
    """#94U50: inbox ی کاتی — temp-mail.org سەرەتا، mail.tm جێگرەوە (429-دژە)؛ دەگەڕێنێتەوە (email, poll_fn)"""
    import random as _r
    _UA = _rand_ua()
    try:  # 1) temp-mail.org
        s = requests.Session(); s.headers.update({"User-Agent": _UA})
        mb = s.post("https://web2.temp-mail.org/mailbox", timeout=(10, 30)).json() or {}
        if mb.get("mailbox") and mb.get("token"):
            jwt = mb["token"]

            def _poll(n=14, gap=5):
                mh = {"Authorization": "Bearer " + jwt, "Accept": "application/json"}
                for _ in range(n):
                    time.sleep(gap)
                    try:
                        msgs = (s.get("https://web2.temp-mail.org/messages", headers=mh, timeout=(10, 25)).json() or {}).get("messages") or []
                    except Exception:
                        continue
                    if msgs and msgs[0].get("_id"):
                        try:
                            return s.get(f"https://web2.temp-mail.org/messages/{msgs[0].get('_id')}", headers=mh, timeout=(10, 25)).text or ""
                        except Exception:
                            continue
                return ""
            return mb["mailbox"], _poll
    except Exception:
        pass
    try:  # 2) mail.tm (کاتی 429)
        ms = requests.Session(); ms.headers.update({"User-Agent": _UA})
        dom = (ms.get("https://api.mail.tm/domains", timeout=(15, 30)).json() or {}).get("hydra:member") or []
        if not dom:
            return None, None
        addr = f"tmx{_r.randrange(100000, 999999)}{int(time.time()) % 100000}@{(dom[0] or {}).get('domain')}"
        pw = "Xk9!mQ2#vLp8$zRw"
        r = ms.post("https://api.mail.tm/accounts", json={"address": addr, "password": pw}, timeout=(15, 30))
        if r.status_code not in (200, 201):
            return None, None
        mtok = (ms.post("https://api.mail.tm/token", json={"address": addr, "password": pw}, timeout=(15, 30)).json() or {}).get("token")
        if not mtok:
            return None, None

        def _poll2(n=14, gap=5):
            mh2 = {"Authorization": f"Bearer {mtok}"}
            for _ in range(n):
                time.sleep(gap)
                try:
                    msgs = (ms.get("https://api.mail.tm/messages", headers=mh2, timeout=(15, 30)).json() or {}).get("hydra:member") or []
                except Exception:
                    continue
                if msgs and msgs[0].get("id"):
                    try:
                        d = ms.get(f"https://api.mail.tm/messages/{msgs[0].get('id')}", headers=mh2, timeout=(15, 30)).json() or {}
                        t = d.get("text") or ""
                        h = d.get("html") or ""
                        if isinstance(t, list):
                            t = " ".join(t)
                        if isinstance(h, list):
                            h = " ".join(h)
                        return f"{t}\n{h}"
                    except Exception:
                        continue
            return ""
        print(f"[INBOX] mail.tm جێگرەوە ✅ {addr}", flush=True)
        return addr, _poll2
    except Exception:
        pass
    try:  # 3) 1secmail (کۆتا جێگرەوە)
        em3, sid3 = _guerr_new()
        if not em3:
            return None, None

        def _poll3(n=14, gap=5):
            for _ in range(n):
                time.sleep(gap)
                txt = _guerr_body(sid3)
                if txt and len(txt.strip()) > 10:
                    return txt
            return ""
        print(f"[INBOX] guerrilla جێگرەوە ✅ {em3[:22]}", flush=True)
        return em3, _poll3
    except Exception:
        return None, None

def _gz_parse_catalog(t):
    """#91A6: safe-wrapper — parser هەرگیز sync ەک ناکوژێنێت"""
    try:
        return _gz_parse_catalog__raw(t)
    except Exception:
        return None

def _rand_ua():
    """#91S: ناسنامەی هەڕەمەکی — هەر داواکارییەکی دەرەکی جیاواز"""
    return random.choice(_UA_POOL)


# ---- state inits ----
_GZ_BADC = {}  # model → cooldown تا

_GZ_BURNED = {}  # #94U60: (px,model) → کاتی 429 (کوانتای کاتژمێر)

_GZ_WALL = {}  # #94U60: px → کاتی 401/403 (واڵ 30خولەک)

_GZ_GOOD = {}  # #94U60: px → دوایین سەرکەوتن (GOOD-first)

_GZ_PXOK = {}  # #94U61: px → کاتی qualification (cookie-forward سەلمێنرا)

_GZ_SEEDS = ["http://103.237.102.191:11111", "http://38.194.246.34:999", "http://190.97.241.106:999"]  # #94U61: سەلمێنراو 201/429 (reach+cookie ✅)

_GZ_CACHE = {}  # #95U3: (model,ctx-hash) → (ans, t) — پرۆمپتی کورت ≤40پیت، TTL 5خولەک

_GZ_MEM_LD = [False]

_GZ_MEM_SV = [0.0]

_GZ_SYNC = {"t": 0.0, "thread": None, "labels": {}}

_LR_SEM = threading.Semaphore(4)


def _gz_parse_catalog__raw(raw):
    """JS-catalog → لیستی {value, label, free0} — سکەنی ئۆبجێکت-بە-ئۆبجێکت (خێرا، بێ json5)"""
    import re as _re
    i = raw.find("items:[")
    if i < 0:
        return []
    t = raw[i + len("items:"):]
    out = []
    seen = set()
    pos = 0
    n = len(t)
    while True:
        st = t.find("{value:", pos)
        if st < 0 or st >= n:
            break
        depth = 0
        instr = None
        esc = False
        en = -1
        lim = min(st + 9000, n)
        for idx in range(st, lim):
            ch = t[idx]
            if instr:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == instr:
                    instr = None
                continue
            if ch in ("`", '"', "'"):
                instr = ch
                esc = False
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    en = idx
                    break
        if en < 0:
            pos = st + 7
            continue
        obj = t[st:en + 1]
        pos = en + 1
        mv = _re.search(r'value:\s*["\'`]([^"\'`]{1,80})["\'`]', obj)
        if not mv:
            continue
        v = mv.group(1)
        if v in seen:
            continue
        seen.add(v)
        ml = _re.search(r'label:\s*["\'`]([^"\'`]{0,120})["\'`]', obj)
        free0 = bool(_re.search(r'free:\s*\{[^}]*throttleLimit:\s*0', obj))
        out.append({"value": v, "label": (ml.group(1) if ml else v), "free0": free0})
    return out

def _get_fernet():
    try:
        from cryptography.fernet import Fernet
        return Fernet(_FERNET_KEY)
    except Exception:
        return None

def _json_save_locked(path, obj):
    try:
        tmp = f"{path}.{os.getpid()}.{threading.get_ident()}.tmp"
        raw_json = json.dumps(obj, ensure_ascii=False)
        should_encrypt = _is_pool_file(path) and os.environ.get("NO_ENCRYPT") != "1"
        fer = _get_fernet() if should_encrypt else None
        with open(tmp, "wb") as f:
            if fer:
                enc_data = fer.encrypt(raw_json.encode("utf-8"))
                f.write(_ENC_MAGIC + enc_data)
            else:
                f.write(raw_json.encode("utf-8"))
            f.flush()
            os.fsync(f.fileno())
        if os.path.exists(path):
            try:
                os.replace(path, path + ".bak")
            except Exception:
                pass
        os.replace(tmp, path)
        return True
    except Exception as e:
        print(f"[SAVE] هەڵەی پاشەکەوت {path}: {e}", flush=True)
        return False

def _is_pool_file(path):
    fn = os.path.basename(path)
    return fn in ("ca_accounts.json", "cb_accounts.json", "nv_accounts.json",
                  "cbox_accounts.json", "pia_accounts.json", "aiml_key.json",
                  "ac_accounts.json", "al_accounts.json", "proxy_pool.json") or fn.endswith("_accounts.json") or fn.endswith("_key.json")

def alle_chat(messages, model_id, timeout=110, depth=0):
    """چاتی alle-ai.com — WS streaming؛ لیمیت وەک ئەکاونتەکانی تر نیشانە دەکرێت (#91Z-P)"""
    mkey = f"alle-{model_id}"
    with ALLE_LOCK:
        acc = _alle_pick(model_id)
    if not acc:
        raise EMError("alle: هیچ ئەکاونتێکی بەردەست نییە (لیمیت؟)")
    sys_txt = " ".join(m["content"] for m in messages if m.get("role") == "system")[:32000]
    rest = [m for m in messages if m.get("role") != "system"][-9:]
    if rest and rest[-1].get("role") == "user":
        last = rest.pop()
    else:
        last = {"role": "user", "content": "سلام"}
    tx = ""
    for m in rest[-7:]:
        who = "بەکارهێنەر" if m.get("role") == "user" else "وەڵام"
        tx += f"{who}: {str(m.get('content'))[:700]}\n"
    if sys_txt:
        tx = f"[ئاراستەی سیستەم: {sys_txt}]\n{tx}"
    tx += f"بەکارهێنەر: {last.get('content')}"
    try:
        return _alle_ask(acc, model_id, tx, timeout, mkey)
    except _AlleLimit as e:
        _alle_mark(acc, model_id, str(e))
        raise EMError(str(e))
    except EMError as e:
        s = str(e)
        if "401" in s and depth == 0:
            _alle_login(acc, force=True)
            return alle_chat(messages, model_id, timeout, depth=1)
        if any(x in s.lower() for x in ("limit", "quota", "credit", "exceeded", "free")) and depth == 0:
            _alle_mark(acc, model_id, s)
            with ALLE_LOCK:
                acc2 = _alle_pick(model_id)
            if acc2 and acc2 is not acc:
                return alle_chat(messages, model_id, timeout, depth=1)
        raise EMError(f"alle: {s[:80]}")

def cb_chat(messages, model_id, timeout=110):
    """چاتی ChatbotApp — مێژوو فلێت + حەوزی ئەکاونت + SSE parts"""
    import time as _t, uuid as _u
    meta = (MS.get("cb_ok") or {}).get(model_id)
    if not meta:
        raise EMError("cb: مۆدێڵ نییە")
    bot_id = meta.get("botId") or 120
    tier = meta.get("tier") or "f"
    if tier == "x":
        max_att = 1
    else:
        max_att = min(len(CB_ST.get("accounts") or [1]) + 1, 8)
    lines = []
    for m in _sys_keep(messages, 11):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if role == "system":
            lines.append("[Instructions] " + c)
        elif role == "user":
            lines.append("[User] " + c)
        else:
            lines.append("[Assistant] " + c)
    if not lines:
        raise EMError("cb: هیچ نامە")
    lines.append("[Assistant]")
    prompt = _flat_cut(lines)
    last_err = ""
    for attempt in range(max_att):
        try:
            tok, uid = _cb_token()
        except EMError:
            if not _cb_rotate():
                raise
            continue
        H = {"User-Agent": CB_UA, "Content-Type": "application/json", "accept": "text/event-stream",
             "x_token": tok, "x_user_id": uid, "x_platform": "web", "x_model": str(bot_id),
             "Origin": "https://chat.chatbotapp.ai", "Referer": "https://chat.chatbotapp.ai/"}
        body = {"botId": bot_id, "sessionId": _u.uuid4().hex[:20],
                "userPseudoId": f"{_u.uuid4().int % 10 ** 9}.{int(_t.time())}",
                "hubxId": str(_u.uuid4()),
                "message": {"prompt": prompt, "messageId": str(_u.uuid4())},
                "actions": {"webSearch": False, "createImage": False, "deepSearch": False, "privateSearch": False}}
        try:
            r = requests.post(CB_BASE + "/api/v2/chat", json=body, headers=H,
                              timeout=(15, timeout), stream=True)
        except Exception as e:
            raise EMError(f"cb: {str(e)[:60]}")
        if r.status_code != 200:
            raw = b""
            try:
                for ch in r.iter_content(chunk_size=None):
                    raw += ch
                    if len(raw) > 300:
                        break
            except Exception:
                pass
            msg = ""
            try:
                msg = (json.loads(raw.decode("utf-8", "replace")).get("data") or {}).get("message", "")
            except Exception:
                msg = raw[:60].decode("utf-8", "replace")
            last_err = msg or str(r.status_code)
            if "Insufficient chat credit" in msg:
                if tier == "x":
                    raise EMError("cb: پرێمیۆمی-قورس — بە پارە بەردەستە")
                import datetime as _dt
                acc = _cb_cur_acc()
                if acc:
                    CB_ST.setdefault("exhausted", {})[acc["email"]] = _t.time() + 86000  # #94U24: وەک NV — cooldown-until (24h)
                    _replace_dead_soon("cb")  # #94U24: لە جێی ئەمە → نوێ یەکسەر
                if not _cb_rotate():
                    raise EMError("cb: کرێدیت هەموو ئەکاونتەکان")
                continue
            if "No agent mapping" in msg:
                MS.setdefault("cb_bad", {})[model_id] = {"t": _t.time(), "why": "no-mapping"}
                MS.get("cb_ok", {}).pop(model_id, None)
                _ms_save()
                raise EMError("cb: مۆدێڵ نەماوە")
            raise EMError(f"cb: {last_err[:60]}")
        parts = []
        agent = ""
        r.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
        for line in r.iter_lines(decode_unicode=True):
            if not line.startswith("data:"):
                continue
            try:
                d = json.loads(line[5:].strip())
            except Exception:
                continue
            dd = d.get("data") or {}
            if isinstance(dd, dict):
                if dd.get("agent_id"):
                    agent = dd["agent_id"]
                c = dd.get("content")
                if isinstance(c, dict) and c.get("parts"):
                    for p in c["parts"]:
                        if isinstance(p, dict) and p.get("thought"):
                            continue  # پارچەی بیرکردنەوە
                        parts.append((p or {}).get("text", "") if isinstance(p, dict) else str(p))
        # پترن: دێڵتا زیادەکان + ڕووداوی کۆتایی-کۆکراو (وەک Nova §2.32)
        if len(parts) > 1 and parts[-1].startswith("".join(parts[:-1])):
            ans = parts[-1].strip()
        else:
            ans = "".join(parts).strip()
        if ans:
            return ans
        last_err = "بەتاڵ"
        _tok_drop("cb")
        CB_ST["tok"] = None
    raise EMError(f"cb: {last_err[:60] or 'شکست'}")

def ca_chat(messages, model_id, timeout=110):
    """چاتی ChatbotAI — send + پۆڵی get-all + حەوزی ئەکاونت + خۆکار-ساینئەپ"""
    import time as _t
    cat = _ca_models_catalog()
    if model_id not in cat:
        raise EMError("ca: مۆدێڵ نییە")
    mkey, mver = model_id, cat[model_id][0]
    lines = []
    for m in _sys_keep(messages, 11):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if role == "system":
            lines.append("[Instructions] " + c)
        elif role == "user":
            lines.append("[User] " + c)
        else:
            lines.append("[Assistant] " + c)
    if not lines:
        raise EMError("ca: هیچ نامە")
    lines.append("[Assistant]")
    prompt = _flat_cut(lines)
    last_err = ""
    for attempt in range(8):
        try:
            tok = _ca_token()
        except EMError:
            if not _ca_rotate(mkey):
                raise
            continue
        H = {"User-Agent": CA_UA, "Content-Type": "application/json",
             "authorization": tok, "Origin": CA_BASE, "Referer": CA_BASE + "/"}
        try:
            r = requests.post(CA_BASE + "/api/chat/message/send",
                              json={"message": prompt, "model": mkey, "temporaryChat": False,
                                    "modelVersion": mver}, headers=H, timeout=(15, 40))
        except Exception as e:
            raise EMError(f"ca: {str(e)[:60]}")
        ok = False
        sid = ""
        err = ""
        try:
            j = r.json() or {}
            ok = bool(j.get("success"))
            sid = str(j.get("sessionId") or "")
            err = str(j.get("error") or "")
        except Exception:
            err = r.text[:80]
        if not ok:
            last_err = err or str(r.status_code)
            low = last_err.lower()
            if "limit" in low or "free message" in low or "no free" in low:
                acc = getattr(_TLS, "ca_acc", None)
                if acc is None:
                    _accs = CA_ST.get("accounts") or []
                    acc = _accs[CA_ST["idx"] % len(_accs)] if _accs else None
                if acc is not None:
                    lm = CA_ST.setdefault("limits", {}).setdefault(acc["email"], {})
                    lm[mkey] = _lim_today()  # مۆدێڵ-لیمێت — هەمیشە بەروارکراو
                    # #91Z-P: ستار تەنها بۆ limit ی ڕاستەقینەی گشتی (free message / no free / daily limit)
                    # هەڵەکانی "account limit"/"rate" ی تایبەت بە مۆدێڵ → تەنها mkey (نەک *)
                    if ("free message" in low or "no free" in low or "daily" in low):
                        lm["*"] = _lim_today()
                        _replace_dead_soon("ca")  # #94U24: مردنی گشتی → نوێ لە جێی
                    _ca_save_acc()
                if not _ca_rotate(mkey):
                    raise EMError("ca: سنووری هەموو ئەکاونتەکان")
                continue
            if r.status_code in (401, 403):
                CA_ST["tok"] = None
                if not _ca_rotate(mkey):
                    raise EMError("ca: توکن")
                continue
            raise EMError(f"ca: {last_err[:60]}")
        # پۆڵی وەڵام — get-all (POST)
        deadline = _t.time() + min(timeout, 100)
        while _t.time() < deadline:
            _t.sleep(2.5)
            try:
                r2 = requests.post(CA_BASE + "/api/session/get-all", headers=H, json={}, timeout=(15, 30))
                sessions = (r2.json() or {}).get("sessions") or []
            except Exception:
                continue
            for s in sessions:
                if str(s.get("sessionId")) != sid:
                    continue
                ms = s.get("messages") or []
                if ms and ms[-1].get("finish_reason") == "stop":
                    ans = (ms[-1].get("content") or "").strip()
                    if ans:
                        return ans
        last_err = "بەتاڵ/درەنگ"
        _tok_drop("ca")
        CA_ST["tok"] = None
    raise EMError(f"ca: {last_err[:60] or 'شکست'}")

def nv_chat(messages, model_id, timeout=110):
    """چاتی Nova — هەمان فلۆوی §2.29 + حەوزی ئەکاونت (٥ نامەی خۆڕایی/ئەکاونت)"""
    import time as _t, uuid as _u
    meta = (MS.get("nv_ok") or {}).get(model_id)
    if not meta:
        raise EMError("nv: مۆدێڵ نییە")
    bot_id = meta.get("botId") or 0
    tier = meta.get("tier") or "f"
    max_att = 3 if tier == "p" else (1 if tier == "x" else 12)  # #94U37: 8→12 بۆ punch-through لەناو مردووەکان
    lines = []
    for m in _sys_keep(messages, 11):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if role == "system":
            lines.append("[Instructions] " + c)
        elif role == "user":
            lines.append("[User] " + c)
        else:
            lines.append("[Assistant] " + c)
    if not lines:
        raise EMError("nv: هیچ نامە")
    lines.append("[Assistant]")
    prompt = _flat_cut(lines)
    last_err = ""
    import datetime as _dtm
    _today = _dtm.datetime.utcnow().strftime("%Y-%m-%d")
    _ens_retried = set()  # #94U37: ensure+retry یەک جار بۆ هەر ئەکاونتێک لەم بانگەوازە
    for attempt in range(max_att):
        try:
            tok, uid = _nv_token()
        except EMError:
            if not _nv_rotate():
                raise
            continue
        H = {"User-Agent": NV_UA, "Content-Type": "application/json", "accept": "text/event-stream",
             "X_Token": tok, "X_User_Id": uid, "X_Platform": "web", "X_Model": str(bot_id),
             "Origin": "https://chat.novaapp.ai", "Referer": "https://chat.novaapp.ai/"}
        if True:  # #94U36: ensure-credits بۆ هەموو tier (پێشتر تەنها p/x) — grant ئەگەر مابێت
            accs0 = NV_ST.get("accounts") or []
            em0 = accs0[NV_ST["idx"] % len(accs0)]["email"] if accs0 else ""
            en = NV_ST.setdefault("ensured", {})
            if en.get(em0) != _today:
                try:
                    requests.get(NV_BASE + "/api/v2/ensure-credits",
                                 headers={"User-Agent": NV_UA, "X_Token": tok, "X_User_Id": uid,
                                          "X_Platform": "web", "Origin": "https://chat.novaapp.ai",
                                          "Referer": "https://chat.novaapp.ai/"}, timeout=(10, 20))
                except Exception:
                    pass
                en[em0] = _today
                _nv_save_acc()
        body = {"botId": bot_id, "sessionId": _u.uuid4().hex[:20],
                "userPseudoId": f"{_u.uuid4().int % 10 ** 9}.{int(_t.time())}",
                "hubxId": str(_u.uuid4()),
                "message": {"prompt": prompt, "messageId": str(_u.uuid4())},
                "actions": {"webSearch": False, "createImage": False, "deepSearch": False, "privateSearch": False}}
        try:
            r = requests.post(NV_BASE + "/api/v2/chat", json=body, headers=H,
                              timeout=(15, timeout), stream=True)
        except Exception as e:
            raise EMError(f"nv: {str(e)[:60]}")
        if r.status_code != 200:
            raw = b""
            try:
                for ch in r.iter_content(chunk_size=None):
                    raw += ch
                    if len(raw) > 300:
                        break
            except Exception:
                pass
            msg = ""
            try:
                msg = (json.loads(raw.decode("utf-8", "replace")).get("data") or {}).get("message", "")
            except Exception:
                msg = raw[:60].decode("utf-8", "replace")
            last_err = msg or str(r.status_code)
            if "Insufficient chat credit" in msg:
                if tier == "x":
                    raise EMError("nv: پرێمیۆمی-قورس — بە پارە بەردەستە")
                acc = getattr(_TLS, "nv_acc", None)
                if acc is None:
                    _accs = NV_ST.get("accounts") or []
                    acc = _accs[NV_ST["idx"] % len(_accs)] if _accs else None
                _em = (acc or {}).get("email") or ""
                if acc is not None and _em not in _ens_retried:  # #94U37: grant ماوە؟ — ensure + 1 retry پێش ناسناخەکە
                    _ens_retried.add(_em)
                    try:
                        requests.get(NV_BASE + "/api/v2/ensure-credits",
                                     headers={"User-Agent": NV_UA, "X_Token": tok, "X_User_Id": uid,
                                              "X_Platform": "web", "Origin": "https://chat.novaapp.ai",
                                              "Referer": "https://chat.novaapp.ai/"}, timeout=(10, 20))
                    except Exception:
                        pass
                    try:
                        NV_ST.setdefault("ensured", {})[_em] = _today
                        _nv_save_acc()
                    except Exception:
                        pass
                    _t.sleep(2)
                    continue  # هەمان ئەکاونت دووبارە (بێ rotate، بێ exc+)
                if acc is not None:
                    NV_ST.setdefault("exhausted", {})[acc["email"]] = _t.time() + 86000  # #120: 600s→24h (like CB)
                    _replace_dead_soon("nv")  # #94U24: لە جێی ئەمە → نوێ یەکسەر
                    NV_ST.setdefault("exc", {})[acc["email"]] = (NV_ST.get("exc") or {}).get(acc["email"], 0) + 3  # #94U37: پشتڕاستکراوە-مردوو (دوای ensure+retry) → skip یەکسەر
                if not _nv_rotate():
                    raise EMError("nv: حەوزی ئەکاونتەکان تەواوە")
                _t.sleep(1.5)
                continue
            if "No agent mapping" in msg:
                MS.setdefault("nv_bad", {})[model_id] = {"t": _t.time(), "why": "no-mapping"}
                MS.get("nv_ok", {}).pop(model_id, None)
                _ms_save()
                raise EMError("nv: مۆدێڵ نەماوە")
            raise EMError(f"nv: {last_err[:60]}")
        parts = []
        r.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
        for line in r.iter_lines(decode_unicode=True):
            if not line.startswith("data:"):
                continue
            try:
                d = json.loads(line[5:].strip())
            except Exception:
                continue
            dd = d.get("data") or {}
            if isinstance(dd, dict):
                c = dd.get("content")
                if isinstance(c, dict) and c.get("parts"):
                    for p in c["parts"]:
                        if isinstance(p, dict) and p.get("thought"):
                            continue  # پارچەی بیرکردنەوە — فڕێدان
                        parts.append((p or {}).get("text", "") if isinstance(p, dict) else str(p))
        if not parts:
            _tok_drop("nv")
            NV_ST["tok"] = None
            last_err = "بەتاڵ"
            continue
        # پترن: دێڵتا زیادەکان + لە کۆتایی ڕووداوی کۆتایی-کۆکراو
        if len(parts) > 1 and parts[-1].startswith("".join(parts[:-1])):
            ans = parts[-1].strip()
        else:
            ans = "".join(parts).strip()
        if ans:
            return ans
        last_err = "بەتاڵ"
        _tok_drop("nv")
        NV_ST["tok"] = None
    raise EMError(f"nv: {last_err[:60] or 'شکست'}")

def rwd_chat(model_id, messages, timeout=110):
    """پرسیار بۆ rewind — خۆکارانە ناسنامە دەگۆڕێت کاتێک تۆکن تەواو دەبێت"""
    for attempt in (0, 1):
        s = _rwd_session()
        ua = s.headers["User-Agent"]
        try:
            r = s.post(RWD_BASE + "/v1/chat/completions/",
                       headers={"User-Agent": ua, "Content-Type": "application/json"},
                       json={"model": model_id, "messages": messages}, timeout=(15, timeout))
        except Exception as e:
            if attempt == 0:
                _rwd_next_identity()
                continue
            raise EMError(f"rwd: {str(e)[:60]}")
        if r.status_code == 400:
            # ناسنامەی ئەم UA یە بەکارهاتووە — گۆڕی بدەر بۆ ئەوی تر
            _rwd_mark_dead()  # #94U46
            _rwd_next_identity()
            continue
        if r.status_code == 429:
            raise EMError("rwd: ڕێژە زۆرە — چاوەڕێ بکە")
        try:
            j = r.json()
        except Exception:
            _rwd_next_identity()
            continue
        err = j.get("error")
        if isinstance(err, dict):
            code = str(err.get("code") or "")
            if code == "INSUFFICIENT_TOKENS":
                # تۆکنەکانی ئەم ناسنامەیە تەواو بوون — UA ی نوێ = ٢٥٠٠ی نوێ
                _rwd_mark_dead()  # #94U46: ئەمە مردووە — جێگۆڕکێی 1-بۆ-1
                if attempt == 0:
                    _rwd_next_identity()
                    continue
                raise EMError("rwd: هەموو ناسنامەکان تەواو بوون")
            raise EMError("rwd: " + (code or str(err)[:50])[:60])
        ch = (j.get("choices") or [{}])[0]
        ans = ((ch.get("message") or {}).get("content") or "").strip()
        if ans:
            try:
                _rwd_charge(sum(len(str(m.get("content") or "")) for m in messages), len(ans))
            except Exception:
                pass
            if (ch.get("finish_reason") or "") == "length" or ans[-1].isalnum():  # #94U45: بڕانی سێرڤەر (~1600 تۆکن) یان کۆتایی نیوە-وشە → بەردەوامی خۆکار
                ans = _rwd_continue(model_id, ans, timeout)
            return ans
        _rwd_next_identity()
    raise EMError("rwd: نەگەڕایەوە")

def al_chat(messages, model_id, timeout=110):
    """چاتی AllChatBots — کوکی سێشن + /api/chat — 402 → فەیلئۆڤەر"""
    sess = _al_login()
    lines = []
    for m in _sys_keep(messages, 11):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if role == "system":
            lines.append("[Instructions] " + c)
        elif role == "user":
            lines.append("[User] " + c)
        else:
            lines.append("[Assistant] " + c)
    if not lines:
        raise EMError("al: هیچ نامە")
    lines.append("[Assistant]")
    prompt = _flat_cut(lines)
    H = {"User-Agent": AL_UA, "Content-Type": "application/json",
         "Origin": "https://allchatbots.ai", "Referer": "https://allchatbots.ai/"}
    ck = {AL_COOKIE: json.dumps(sess)}
    body = {"messages": [{"role": "user", "content": prompt}], "modelId": model_id, "stream": False}
    for attempt in range(2):
        try:
            r = requests.post(AL_BASE + "/api/chat", json=body, headers=H, cookies=ck, timeout=(15, timeout))
        except Exception as e:
            raise EMError(f"al: {str(e)[:60]}")
        if r.status_code in (401, 403) and attempt == 0:
            sess = _al_login(force=True)
            ck = {AL_COOKIE: json.dumps(sess)}
            continue
        if r.status_code == 402 and attempt == 0:  # #94U49: ئەکاونتی داهاتوو
            _al_rotate()
            sess = _al_login(force=True)
            ck = {AL_COOKIE: json.dumps(sess)}
            continue
        if r.status_code == 402:
            raise EMError("al: سەبسکریپشن پێویستە — دەگوازرێتەوە")
        if r.status_code == 429 and attempt == 0:  # #94U49: ئەکاونتی داهاتوو
            _al_rotate()
            sess = _al_login(force=True)
            ck = {AL_COOKIE: json.dumps(sess)}
            continue
        if r.status_code == 429:
            _replace_dead_soon("al")  # #94U49: نوێ لە جێی
            raise EMError("al: لیمیت")
        if r.status_code != 200:
            raise EMError(f"al: HTTP{r.status_code}")
        ct = (r.headers.get("content-type") or "")
        if "text/event" in ct:
            parts = []
            r.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
            for line in r.iter_lines(decode_unicode=True):
                if not line or not line.startswith("data:"):
                    continue
                try:
                    d = json.loads(line[5:].strip())
                except Exception:
                    continue
                for k in ("content", "text", "delta"):
                    v = d.get(k)
                    if isinstance(v, str):
                        parts.append(v)
                        break
            ans = "".join(parts).strip()
        else:
            try:
                j = r.json()
            except Exception:
                raise EMError("al: وەڵامی نەناسراو")
            ans = ""
            for cand in (j.get("content"), j.get("message"), j.get("text"),
                         (j.get("choices") or [{}])[0].get("message", {}).get("content") if isinstance(j.get("choices"), list) else None):
                if isinstance(cand, str) and cand.strip():
                    ans = cand.strip()
                    break
        if ans:
            return ans
        raise EMError("al: بەتاڵ")
    raise EMError("al: شکست")

def ac_chat(messages, model_id, timeout=110):
    """چاتی AskAI — send + SSE stream ی session + حەوزی ئەکاونت + خۆکار-ساینئەپ"""
    import time as _t
    cat = _ac_catalog()
    if model_id not in cat:
        raise EMError("ac: مۆدێڵ نییە")
    mkey, mver = model_id, cat[model_id][0]
    lines = []
    for m in _sys_keep(messages, 11):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if role == "system":
            lines.append("[Instructions] " + c)
        elif role == "user":
            lines.append("[User] " + c)
        else:
            lines.append("[Assistant] " + c)
    if not lines:
        raise EMError("ac: هیچ نامە")
    lines.append("[Assistant]")
    prompt = _flat_cut(lines)
    last_err = ""
    for attempt in range(8):
        try:
            tok = _ac_token()
        except EMError:
            if not _ac_rotate(mkey):
                raise
            continue
        H = {"User-Agent": AC_UA, "Content-Type": "application/json", "authorization": tok,
             "Origin": AC_BASE, "Referer": AC_BASE + "/", "accept": "text/event-stream"}
        try:
            r = requests.post(AC_BASE + "/api/chat/message/send",
                              json={"message": prompt, "model": mkey, "temporaryChat": False,
                                    "modelVersion": mver}, headers=H, timeout=(15, 40))
        except Exception as e:
            raise EMError(f"ac: {str(e)[:60]}")
        ok = False
        sid = ""
        err = ""
        try:
            j = r.json() or {}
            ok = bool(j.get("success"))
            sid = str(j.get("sessionId") or "")
            err = str(j.get("error") or "")
        except Exception:
            err = r.text[:80]
        if not ok:
            last_err = err or str(r.status_code)
            low = last_err.lower()
            if "limit" in low or "free message" in low or "no free" in low:
                acc = getattr(_TLS, "ac_acc", None)
                if acc is None:
                    _accs = AC_ST.get("accounts") or []
                    acc = _accs[AC_ST["idx"] % len(_accs)] if _accs else None
                if acc is not None:
                    lm = AC_ST.setdefault("limits", {}).setdefault(acc["email"], {})
                    lm[mkey] = _lim_today()  # مۆدێڵ-لیمێت
                    if ("free message" in low or "no free" in low or "daily" in low):
                        lm["*"] = _lim_today()  # تەنها limit ی ڕاستەقینەی گشتی
                        _replace_dead_soon("ac")  # #94U24: مردنی گشتی → نوێ لە جێی
                    _ac_save_acc()
                if not _ac_rotate(mkey):
                    raise EMError("ac: سنووری هەموو ئەکاونتەکان")
                continue
            if r.status_code in (401, 403):
                AC_ST["tok"] = None
                if not _ac_rotate(mkey):
                    raise EMError("ac: توکن")
                continue
            raise EMError(f"ac: {last_err[:60]}")
        # SSE stream — snapshot ی نشست
        ans = ""
        deadline = _t.time() + min(timeout, 100)
        try:
            r2 = requests.get(AC_BASE + "/api/session/stream",
                              params={"sessionId": sid, "isTool": "false", "isAssistant": "false"},
                              headers=H, timeout=(15, 100), stream=True)
            r2.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
            for line in r2.iter_lines(decode_unicode=True):
                if _t.time() > deadline:
                    break
                if not line or not line.startswith("data:"):
                    continue
                try:
                    d = json.loads(line[5:].strip())
                except Exception:
                    continue
                if d.get("type") != "snapshot":
                    continue
                data = d.get("data") or {}
                ms = data.get("messages") or []
                am = [x for x in ms if x.get("role") == "assistant"]
                if am and data.get("status") == "completed":
                    ans = (am[-1].get("message") or "").strip()
                    break
            try:
                r2.close()
            except Exception:
                pass
        except Exception as e:
            last_err = str(e)[:60]
            AC_ST["tok"] = None
            continue
        if ans:
            return ans
        last_err = "بەتاڵ/درەنگ"
        AC_ST["tok"] = None
    raise EMError(f"ac: {last_err[:60] or 'شکست'}")

class _AlleLimit(Exception):
    pass

def _ac_catalog():
    cat = {}
    for k, v in (MS.get("ac_ok") or {}).items():
        cat[k] = (v.get("version") or k, v.get("label") or k)
    for k, v in AC_FALLBACK.items():
        cat.setdefault(k, v)
    return cat

def _ac_rotate(model_key):
    accs = AC_ST.get("accounts") or []
    lim = AC_ST.get("limits") or {}
    chosen = None
    with _AC_LK:
        for _ in range(len(accs)):
            AC_ST["idx"] = (AC_ST["idx"] + 1) % len(accs)
            acc = accs[AC_ST["idx"]]
            em = lim.get(acc["email"]) or {}
            if not _lim_hit(em, model_key):  # #91Z
                chosen = acc
                break
    if chosen is not None:
        _TLS.ac_acc = chosen
        AC_ST["tok"] = None
        _ac_save_acc()
        return True
    res = _ac_signup_new()
    if res:
        try:
            _TLS.ac_acc = (AC_ST.get("accounts") or [])[-1]
        except Exception:
            pass
    return bool(res)

def _ac_token():
    import time as _t
    acc = getattr(_TLS, "ac_acc", None)
    if acc is None:
        try:
            _ac_rotate(None)  # #94U21: یەکەم داوا → لیسی خۆی
        except Exception:
            pass
        acc = getattr(_TLS, "ac_acc", None)
        if acc is None:
            accs = AC_ST.get("accounts") or []
            acc = accs[AC_ST["idx"] % len(accs)] if accs else None
    if acc is not None:
        em = acc.get("email")
        with _AC_LK:
            c = (AC_ST.get("toks") or {}).get(em)
        if c and _t.time() - c[1] < 2700:
            return c[0]
        res = _ac_firebase("signInWithPassword", acc["email"], acc["password"])
        if res:
            with _AC_LK:
                AC_ST.setdefault("toks", {})[em] = (res[0], _t.time())
            if not acc.get("boot"):
                try:
                    _ac_bootstrap(res[0], res[1], acc["email"])
                except Exception:
                    pass
                acc["boot"] = True
                _ac_save_acc()
            return res[0]
    resn = _ac_signup_new()
    if not resn:
        raise EMError("ac: هیچ ئەکاونت")
    try:
        _na = (AC_ST.get("accounts") or [])[-1]
        _TLS.ac_acc = _na
        with _AC_LK:
            AC_ST.setdefault("toks", {})[_na.get("email")] = (resn[0], _t.time())
    except Exception:
        pass
    return resn[0]

def _al_login(force=False):
    """چوونەژوورەوەی Supabase — سێشن (~٥٠ خولەک کاش)"""
    import time as _t
    if not force and AL_ST.get("sess") and _t.time() - AL_ST.get("sess_t", 0) < 2700:
        return AL_ST["sess"]
    accs = AL_ST.get("accounts") or []
    if not accs:
        raise EMError("al: هیچ ئەکاونت")
    acc = accs[AL_ST["idx"] % len(accs)]
    try:
        r = requests.post(AL_SB + "/auth/v1/token?grant_type=password",
                          headers={"apikey": AL_KEY, "Content-Type": "application/json"},
                          json={"email": acc["email"], "password": acc["password"]}, timeout=(10, 25))
    except Exception as e:
        raise EMError(f"al: {str(e)[:60]}")
    if r.status_code != 200 or not (r.json() or {}).get("access_token"):
        # #91AA: ئەکاونتی مردوو → ئەکاونتی دواتر/سایناپی نوێ
        AL_ST["idx"] += 1
        try:
            _al_rotate()
            return _al_login(force=True)
        except Exception:
            raise EMError("al: چوونەژوورەوە شکست")
    AL_ST["sess"] = r.json()
    AL_ST["sess_t"] = _t.time()
    _al_save_acc()
    return AL_ST["sess"]

def _al_rotate():
    """#91AA: ئەکاونتی دواتر — ئەگەر هیچ نەما سایناپی نوێ"""
    accs = AL_ST.get("accounts") or []
    AL_ST["idx"] = (AL_ST.get("idx", 0) + 1) % max(len(accs), 1)
    AL_ST["sess"] = None
    _al_save_acc()
    return bool(_al_signup_new())

def _alle_ask(acc, model_id, text, timeout=110, mkey=""):
    """فڵۆوی تەواو: WS → auth → subscribe → create/prompt → ai-response → چانکەکان"""
    import websocket as _ws
    _alle_login(acc)
    hdrs = _alle_hdrs(acc)
    w = _ws.create_connection(ALLE_WSS, timeout=12,
                              header=["Origin: https://app.alle-ai.com",
                                      "User-Agent: " + (acc.get("ua") or _ALLE_UA)])
    try:
        hello = json.loads(w.recv())
        sid = (json.loads(hello.get("data") or "{}") or {}).get("socket_id")
        if not sid:
            raise EMError("alle: ws hello شکست")
        r = requests.post(ALLE_AUTH_EP, json={"socket_id": sid,
                                              "channel_name": f"private-App.Models.User.{acc.get('uid')}"},
                          headers=hdrs, timeout=(10, 20))
        au = (r.json() or {}).get("auth")
        if not au:
            raise EMError("alle: broadcasting/auth شکست")
        w.send(json.dumps({"event": "pusher:subscribe",
                           "data": {"auth": au, "channel": f"private-App.Models.User.{acc.get('uid')}"}}))
        pos = int(acc.get("pos") or 1)
        r = requests.post(ALLE_API + "/create/prompt",
                          json={"conversation": acc["conv"], "prompt": text, "position": [pos, pos],
                                "combine": False, "compare": False, "web_search": False},
                          headers={**hdrs, "Content-Type": "application/json"}, timeout=(10, 30))
        if r.status_code == 401:
            _alle_login(acc, force=True)
            hdrs = _alle_hdrs(acc)
            r = requests.post(ALLE_API + "/create/prompt",
                              json={"conversation": acc["conv"], "prompt": text, "position": [pos, pos],
                                    "combine": False, "compare": False, "web_search": False},
                              headers={**hdrs, "Content-Type": "application/json"}, timeout=(10, 30))
        if r.status_code != 200:
            raise EMError(f"alle: prompt {r.status_code} {r.text[:60]}")
        pid = (r.json() or {}).get("id")
        acc["pos"] = pos + 1
        _alle_save_acc()
        r = requests.post(ALLE_API + "/ai-response",
                          json={"conversation": acc["conv"], "model": model_id, "is_new": False,
                                "prompt": pid, "prev": [], "combine": False, "compare": False},
                          headers={**hdrs, "Content-Type": "application/json"}, timeout=(10, 30))
        if r.status_code == 429:
            raise _AlleLimit(f"alle ڕێژە: {r.text[:80]}")
        if r.status_code == 403:
            # Access Denied — لیمیت ی ئەکاونت یان مۆدێلی ڕێگەنەدراو
            raise _AlleLimit(f"alle 403: {(r.json() or {}).get('message', '')[:60]}")
        if r.status_code != 200:
            raise EMError(f"alle: ai-response {r.status_code} {r.text[:60]}")

        parts, t0 = [], time.time()
        w.settimeout(max(5, min(30, timeout - (time.time() - t0))))
        while time.time() - t0 < timeout:
            try:
                m = json.loads(w.recv())
            except _ws.WebSocketTimeoutException:
                break
            ev = m.get("event", "")
            if "ping" in ev or "pong" in ev or "subscription" in ev:
                continue
            dd = m.get("data", "{}")
            try:
                dd = json.loads(dd) if isinstance(dd, str) else dd
            except Exception:
                dd = {}
            if ev.endswith("chat.chunk"):
                parts.append(str(dd.get("chunk") if isinstance(dd, dict) else dd))
            elif ev.endswith("chat.stream.failed"):
                msg = str((dd or {}).get("error") or (dd or {}).get("message") or "failed")[:90]
                raise _AlleLimit(f"alle stream: {msg}") if any(
                    x in msg.lower() for x in ("limit", "quota", "credit", "free", "exceeded")) else EMError(f"alle: {msg}")
            elif ev.endswith("chat.stream.complete"):
                break
        ans = "".join(parts).strip()
        if not ans:
            raise EMError("alle: وەڵام بەتاڵ")
        return ans
    finally:
        try:
            w.close()
        except Exception:
            pass

def _alle_login(acc, force=False):
    """لۆگین — token ی Laravel (uid|hash) + uid بۆ کەناڵی WS"""
    if acc.get("token") and not force:
        return True
    r = requests.post(ALLE_API + "/login",
                      json={"email": acc["email"], "password": acc["password"]},
                      headers={"User-Agent": acc.get("ua") or _ALLE_UA, "Accept": "application/json",
                               "Content-Type": "application/json",
                               "Origin": "https://app.alle-ai.com", "Referer": "https://app.alle-ai.com/auth"},
                      timeout=(10, 30))
    d = r.json() or {}
    data = d.get("data") or {}
    if not d.get("status") or not data.get("token"):
        raise EMError(f"alle login: {str(d.get('message'))[:60]}")
    acc["token"] = data["token"]
    acc["uid"] = (data.get("user") or {}).get("id")
    _alle_save_acc()
    print(f"[ALLE] لۆگین ✅ {acc['email']} uid={acc.get('uid')}", flush=True)
    return True

def _alle_mark(acc, mkey, err):
    """#91Z-P ی ئەکاونتەکانی تر — لیمیت وەک CA: mkey هەمیشە، ستاری * تەنها بۆ ڕوونەکان"""
    lm = ALLE_ST.setdefault("limits", {}).setdefault(acc.get("email") or "?", {})
    today = time.strftime("%Y-%m-%d", time.gmtime())
    lm[mkey] = today
    low = str(err).lower()
    if any(w in low for w in ("free message", "no free", "daily", "message limit", "limit reached", "monthly limit")):
        lm["*"] = today
        _replace_dead_soon("alle")  # #94U49: مردنی گشتی → نوێ لە جێی
    _alle_save_acc()

def _alle_pick(mkey):
    """هەڵبژاردنی ئەکاونت — ئەوانەی لیمیتن بۆ ئەم مۆدێلە دەپەڕێت (وەک #91P2: دەگەڕێن، نەسڕدرێنەوە)"""
    accs = ALLE_ST.get("accounts") or []
    if not accs:
        return None
    today = time.strftime("%Y-%m-%d", time.gmtime())
    lim = ALLE_ST.get("limits") or {}
    n = len(accs)
    for i in range(n):
        a = accs[(ALLE_ST.get("idx", 0) + i) % n]
        L = lim.get(a.get("email") or "?") or {}
        if L.get("*") == today or L.get(mkey) == today:
            continue
        ALLE_ST["idx"] = (ALLE_ST.get("idx", 0) + i + 1) % n
        return a
    return None

def _ca_models_catalog():
    cat = {}
    for k, v in (MS.get("ca_ok") or {}).items():
        cat[k] = (v.get("version") or k, v.get("label") or k)
    for k, v in CA_FALLBACK.items():
        cat.setdefault(k, v)
    return cat

def _ca_rotate(model_key):
    """ئەکاونتی دواتر بۆ ئەم مۆدێڵە — ئەوانەی سنووریان تێپەڕاندووە لابەرە؛ ئەگەر نەمابوو → نوێ"""
    accs = CA_ST.get("accounts") or []
    lim = CA_ST.get("limits") or {}
    chosen = None
    with _CA_LK:
        for _ in range(len(accs)):
            CA_ST["idx"] = (CA_ST["idx"] + 1) % len(accs)
            acc = accs[CA_ST["idx"]]
            em = lim.get(acc["email"]) or {}
            if not _lim_hit(em, model_key):  # #91Z: ستاری دوێنێ = ئازاد
                chosen = acc
                break
    if chosen is not None:
        _TLS.ca_acc = chosen
        CA_ST["tok"] = None
        _ca_save_acc()
        return True
    res = _ca_signup_new(model_key)
    if res:
        try:
            _TLS.ca_acc = (CA_ST.get("accounts") or [])[-1]
        except Exception:
            pass
    return bool(res)

def _ca_token():
    import time as _t
    acc = getattr(_TLS, "ca_acc", None)
    if acc is None:
        try:
            _ca_rotate(None)  # #94U21: یەکەم داوا → لیسی خۆی (تەنها ستار-لیمێت لابەرە)
        except Exception:
            pass
        acc = getattr(_TLS, "ca_acc", None)
        if acc is None:
            accs = CA_ST.get("accounts") or []
            acc = accs[CA_ST["idx"] % len(accs)] if accs else None
    if acc is not None:
        em = acc.get("email")
        with _CA_LK:
            c = (CA_ST.get("toks") or {}).get(em)
        if c and _t.time() - c[1] < 2700:
            return c[0]
        res = _ca_firebase("signInWithPassword", acc["email"], acc["password"])
        if res:
            with _CA_LK:
                CA_ST.setdefault("toks", {})[em] = (res[0], _t.time())
            return res[0]
    resn = _ca_signup_new()
    if not resn:
        raise EMError("ca: هیچ ئەکاونت")
    try:
        _na = (CA_ST.get("accounts") or [])[-1]
        _TLS.ca_acc = _na
        with _CA_LK:
            CA_ST.setdefault("toks", {})[_na.get("email")] = (resn[0], _t.time())
    except Exception:
        pass
    return resn[0]

def _cb_cur_acc():
    acc = getattr(_TLS, "cb_acc", None)  # #94U21: لیسی ئەم تڕێدە پێشینەی هەیە
    if acc:
        return acc
    accs = CB_ST.get("accounts") or []
    if not accs:
        return None
    return accs[CB_ST["idx"] % len(accs)]

def _cb_rotate():
    """ئەکاونتی دواتر — ئەگەر هەمووی تەواو بوو → ئەکاونتی نوێ"""
    accs = CB_ST.get("accounts") or []
    if not accs:
        res = _cb_signup_new()
        return bool(res)
    chosen = None
    with _CB_LK:
        for _ in range(len(accs)):
            CB_ST["idx"] = (CB_ST["idx"] + 1) % len(accs)
            acc = accs[CB_ST["idx"]]
            _exv = CB_ST.get("exhausted", {}).get(acc["email"], 0)
            try:
                _dead = float(_exv) > time.time()  # #94U24: cooldown-until (وەک NV)
            except Exception:
                _dead = str(_exv)[:10] == __import__("datetime").datetime.utcnow().strftime("%Y-%m-%d")
            if _dead:
                continue
            chosen = acc
            break
    if chosen is not None:
        _TLS.cb_acc = chosen
        CB_ST["tok"] = None
        _cb_save_acc()
        return True
    # هەموو ئەم ڕۆژە تەواون → ئەکاونتی نوێ
    res = _cb_signup_new()
    if res:
        try:
            _TLS.cb_acc = (CB_ST.get("accounts") or [])[-1]
        except Exception:
            pass
        return True
    _cb_save_acc()
    return False

def _cb_token():
    import time as _t
    acc = getattr(_TLS, "cb_acc", None)
    if acc is None:
        try:
            _cb_rotate()  # #94U21: یەکەم داوا → لیسی خۆی لەژێر لۆک
        except Exception:
            pass
        acc = getattr(_TLS, "cb_acc", None) or _cb_cur_acc()
    if not acc:
        res = _cb_signup_new()
        if not res:
            raise EMError("cb: هیچ ئەکاونت")
        try:
            _na = (CB_ST.get("accounts") or [])[-1]
            _TLS.cb_acc = _na
            with _CB_LK:
                CB_ST.setdefault("toks", {})[_na.get("email")] = (res[0], res[1], _t.time())
        except Exception:
            pass
        return res
    em = acc.get("email")
    with _CB_LK:
        c = (CB_ST.get("toks") or {}).get(em)
    if c and _t.time() - c[2] < 2700:
        return c[0], c[1]
    res = _cb_firebase("signInWithPassword", acc["email"], acc["password"])
    if not res:
        # ئەکاونتەکە نییە — دواتری
        raise EMError("cb: sign-in شکات")
    with _CB_LK:
        CB_ST.setdefault("toks", {})[em] = (res[0], res[1], _t.time())
    return res

def _flat_cut(lines, cap=40000):
    """#94U26+#94U28: بڕینی زیرەک — system تا 32k + مێژوو تا 40k (هەڵە → fallback)"""
    try:
        sys_l = [l for l in lines if l.startswith("[Instructions]")]
        rest = [l for l in lines if not l.startswith("[Instructions]")]
        sys_txt = "\n".join(sys_l)[:32000]
        rest_txt = "\n".join(rest)
        room = cap - len(sys_txt) - 1
        tail = rest_txt[-room:] if len(rest_txt) > room else rest_txt
        return (sys_txt + "\n" + tail) if tail else sys_txt
    except Exception:
        return "\n".join(lines)[-cap:]

def _lim_today():
    """#91Z: بەرواری ئەمڕۆ UTC — بۆ تاگی لیمێت"""
    return time.strftime("%Y-%m-%d", time.gmtime())

def _ms_save():
    try:
        _json_save(MODEL_SYNC_FILE, MS)
    except Exception:
        pass

def _nv_rotate():
    import time as _ts
    accs = NV_ST.get("accounts") or []
    if not accs:
        return bool(_nv_signup_new())
    ex = NV_ST.get("exhausted") or {}
    xc = NV_ST.get("exc") or {}
    now = _ts.time()
    chosen = None
    with _NV_LK:
        _n = len(accs)
        for _pass in (0, 1):  # #94U37: لە کۆتاییەوە (نوێترین یەکەم — کرێدیتی تازە)؛ pass 0: exc<3
            for _i in range(_n):
                _j = _n - 1 - _i
                acc = accs[_j]
                if float(ex.get(acc["email"], 0)) > now:
                    continue  # هێشتا سارد نەبووەتەوە (کۆڵ ٦٠٠ چرکە)
                if _pass == 0 and (xc.get(acc["email"], 0) or 0) >= 3:
                    continue  # #94U36: ٣+ insufficient ئەمڕۆ — مەیدەرەوە ئەگەر ئاڵتەرناتیڤ هەیە
                NV_ST["idx"] = _j
                chosen = acc
                break
            if chosen is not None:
                break
    if chosen is not None:
        _TLS.nv_acc = chosen
        NV_ST["tok"] = None
        _nv_save_acc()
        return True
    res = _nv_signup_new()
    if res:
        try:
            _TLS.nv_acc = (NV_ST.get("accounts") or [])[-1]
        except Exception:
            pass
        return True
    # فەرموودەی کۆتایی — ئەگەر ساینئەپ شکست خوارد، هەر ئەکاونتێک (تەنانەت ساردبوو)
    with _NV_LK:
        NV_ST["idx"] = (NV_ST["idx"] + 1) % len(accs)
        _TLS.nv_acc = accs[NV_ST["idx"]]
    NV_ST["tok"] = None
    _nv_save_acc()
    return True

def _nv_token():
    import time as _t
    acc = getattr(_TLS, "nv_acc", None)
    if acc is None:
        try:
            _nv_rotate()  # #94U21: یەکەم داوا → لیسی خۆی لەژێر لۆک (بڵاوبوونەوە لە سەرەتاوە)
        except Exception:
            pass
        acc = getattr(_TLS, "nv_acc", None)
        if acc is None:
            accs = NV_ST.get("accounts") or []
            acc = accs[NV_ST["idx"] % len(accs)] if accs else None
    if acc is not None:
        em = acc.get("email")
        with _NV_LK:
            c = (NV_ST.get("toks") or {}).get(em)
        if c and _t.time() - c[2] < 2700:
            return c[0], c[1]
        res = _nv_firebase("signInWithPassword", acc["email"], acc["password"])
        if res:
            with _NV_LK:
                NV_ST.setdefault("toks", {})[em] = (res[0], res[1], _t.time())
            return res
    resn = _nv_signup_new()
    if not resn:
        raise EMError("nv: هیچ ئەکاونت")
    try:
        _na = (NV_ST.get("accounts") or [])[-1]
        _TLS.nv_acc = _na
        with _NV_LK:
            NV_ST.setdefault("toks", {})[_na.get("email")] = (resn[0], resn[1], _t.time())
    except Exception:
        pass
    return resn

def _replace_dead_soon(kind):
    """#94U24: لەبری ئەکاونتی مردوو → ئەکاونتی نوێ یەکسەر (1-بە-1؛ بودجە+سەقف سنووردارە)"""
    try:
        threading.Thread(target=_replace_dead_worker, args=(kind,), daemon=True).start()
    except Exception:
        pass

def _rwd_charge(pin_chars, pout_chars, ua=None):
    """#94U46: خەرجکردنی بودجە (~پیت/3 تۆکن)؛ ئەگەر ≥2300 → مردوو."""
    try:
        ua = ua or _rwd_cur()
        est = int(pin_chars / 3) + int(pout_chars / 3) + 20
        with _RWD_LK:
            _u = RWD_ST.setdefault("used", {})
            _u[ua] = (_u.get(ua) or 0) + est
            _crossed = _u[ua] >= RWD_BUDGET
            if _crossed:
                RWD_ST.setdefault("dead", {})[ua] = 1
        if _crossed:
            _rwd_swap(ua)  # #94U48: یەکسەر جێگۆڕکێ — 1-بۆ-1
        else:
            _rwd_save()
    except Exception:
        pass

def _rwd_continue(model_id, ans, timeout=110):
    """#94U45: بەردەوامی خۆکار — هەر پارچە ناسنامەی تازەی 2500 تۆکن؛ تا 3 پارچە (~6400 تۆکن ≈ 20k پیت)"""
    out = ans
    for _cn in range(3):
        try:
            _rwd_next_identity()
            s = _rwd_session()
            ua = s.headers["User-Agent"]
            tail = out[-1500:]
            r = s.post(RWD_BASE + "/v1/chat/completions/",
                       headers={"User-Agent": ua, "Content-Type": "application/json"},
                       json={"model": model_id, "messages": [
                           {"role": "system", "content": "You are continuing a previous answer. Continue seamlessly from the exact cutoff point in the same language and style. No intro, no repetition, no new greeting."},
                           {"role": "user", "content": f"Previous answer cut off here:\n...\n{tail}\n\n[Continue from exactly where it stopped and complete the answer fully]"}]},
                       timeout=(15, timeout))
            j = r.json() or {}
            if isinstance(j.get("error"), dict):
                break
            ch = (j.get("choices") or [{}])[0]
            chunk = ((ch.get("message") or {}).get("content") or "").strip()
            if not chunk:
                break
            out = out + "\n" + chunk
            try:
                _rwd_charge(len(tail) + 300, len(chunk))
            except Exception:
                pass
            print(f"[RWD] 📜 بەردەوامی #{_cn + 1}: +{len(chunk)} پیت", flush=True)
            if (ch.get("finish_reason") or "") != "length" and not chunk[-1].isalnum():
                break
        except Exception as e:
            print(f"[RWD] بەردەوامی شکستی هێنا: {str(e)[:50]}", flush=True)
            break
    return out

def _rwd_mark_dead(ua=None):
    try:
        ua = ua or _rwd_cur()
        with _RWD_LK:
            RWD_ST.setdefault("dead", {})[ua] = 1
        _rwd_swap(ua)  # #94U48: یەکسەر جێگۆڕکێ — 1-بۆ-1
    except Exception:
        pass

def _rwd_next_identity():
    """گۆڕینی ناسنامە — UA ی داهاتوو = بودجەی تازەی ٢٥٠٠ تۆکن؛ #94U46: مردوو → جێگۆڕکێی 1-بۆ-1 (1000 زیندووی بەردەوام)"""
    try:
        _rwd_ensure()
        with _RWD_LK:
            _RWD_STATE["i"] = (_RWD_STATE["i"] + 1) % len(_RWD_UAS)
            _i = _RWD_STATE["i"]
            _cur = _RWD_UAS[_i]
            _dead = RWD_ST.get("dead") or {}
            _used = RWD_ST.get("used") or {}
            if _cur in _dead or (_used.get(_cur) or 0) >= RWD_BUDGET:
                if (RWD_ST.get("total") or 0) < RWD_ABSMAX:
                    _nu = _rwd_gen_ua(set(_RWD_UAS))
                    _RWD_UAS[_i] = _nu
                    RWD_ST["total"] = (RWD_ST.get("total") or 0) + 1
                else:
                    for _k in range(len(_RWD_UAS)):
                        _j = (_i + _k) % len(_RWD_UAS)
                        if _RWD_UAS[_j] not in _dead and (_used.get(_RWD_UAS[_j]) or 0) < RWD_BUDGET:
                            _RWD_STATE["i"] = _j
                            break
        _rwd_save()
    except Exception:
        try:
            _RWD_STATE["i"] = (_RWD_STATE["i"] + 1) % len(_RWD_UAS)
        except Exception:
            pass

def _rwd_session(timeout=15):
    """سێشن بە UA ی ئێستا — GET ی سەرەتا کوکییەی anon_token دەگرێت"""
    _rwd_ensure()
    _rwd_skip_dead()
    s = requests.Session()
    ua = _RWD_UAS[_RWD_STATE["i"] % len(_RWD_UAS)]
    s.headers["User-Agent"] = ua
    try:
        s.get(RWD_BASE + "/v1/models", headers={"User-Agent": ua}, timeout=timeout)
    except Exception:
        pass
    return s

def _tok_drop(kind):
    """#94U21: سڕینەوەی تۆکنی کاشکراوی ئەکاونتی ئەم تڕێدە (وەک tok=None ی کۆن)"""
    try:
        acc = getattr(_TLS, kind + "_acc", None)
        st = {"nv": NV_ST, "cb": CB_ST, "ca": CA_ST, "ac": AC_ST}.get(kind)
        if acc is not None and st is not None:
            (st.get("toks") or {}).pop(acc.get("email"), None)
    except Exception:
        pass

def _ac_bootstrap(tok, uid, email):
    """پرۆفایلی cerebro + user/set بە cerebroId — بەبێ ئەمە نەوەکە ناگوزەرێت"""
    import random as _r, string as _s
    cid = "web_" + "".join(_r.choices(_s.ascii_letters + _s.digits, k=9))
    try:
        requests.post("https://gateway.cerebroapi.com/user/web",
                      json={"user_id": cid, "app_id": "com.codeway.chatappweb", "version": "1.0.0",
                            "operating_system": "Windows", "properties": {"userAgent": AC_UA}},
                      headers={"User-Agent": AC_UA}, timeout=(10, 20))
    except Exception:
        pass
    import time as _t
    try:
        requests.post(AC_BASE + "/api/user/set",
                      json={"userId": uid, "firebaseUserId": uid, "email": email,
                            "createdAt": int(_t.time() * 1000), "cerebroId": cid,
                            "providerData": [{"providerId": "password", "uid": email, "displayName": None,
                                              "email": email, "phoneNumber": None, "photoURL": None}],
                            "originOnboarding": "Home", "emailConsent": True,
                            "temporaryChatOnboarding": True},
                      headers={"authorization": tok, "User-Agent": AC_UA, "Origin": AC_BASE,
                               "Referer": AC_BASE + "/", "Content-Type": "application/json"},
                      timeout=(10, 25))
    except Exception:
        pass

def _ac_firebase(ep, email, pw):
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:{ep}?key={AC_KEY}",
                      json={"email": email, "password": pw, "returnSecureToken": True},
                      headers={"User-Agent": AC_UA}, timeout=(10, 25))
    if r.status_code != 200:
        return None
    j = r.json() or {}
    tok = j.get("idToken")
    if not tok:
        return None
    return tok, j.get("localId") or ""

def _alle_hdrs(acc):
    return {"User-Agent": acc.get("ua") or _ALLE_UA, "Accept": "application/json",
            "Authorization": "Bearer " + (acc.get("token") or ""),
            "Origin": "https://app.alle-ai.com", "Referer": "https://app.alle-ai.com/chat"}

def _ca_firebase(ep, email, pw):
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:{ep}?key={CA_KEY}",
                      json={"email": email, "password": pw, "returnSecureToken": True},
                      headers={"User-Agent": CA_UA}, timeout=(10, 25))
    if r.status_code != 200:
        return None
    tok = (r.json() or {}).get("idToken")
    return (tok, "") if tok else None

def _cb_firebase(ep, email, pw):
    import time as _t
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:{ep}?key={CB_KEY}",
                      json={"email": email, "password": pw, "returnSecureToken": True},
                      headers={"User-Agent": CB_UA}, timeout=(10, 25))
    if r.status_code != 200:
        return None
    j = r.json()
    tok = j.get("idToken")
    if not tok:
        return None
    import base64 as _b
    p = tok.split(".")[1]
    p += "=" * (-len(p) % 4)
    try:
        uid = _b.urlsafe_b64decode(p).decode("utf-8", "replace")
        uid = json.loads(uid).get("user_id") or ""
    except Exception:
        uid = ""
    return tok, uid

def _lim_hit(em, model_key=None):
    """#91Z: ئایا ئەم ئەکاونتە ئەمڕۆ limit ە؟ — ستار/مۆدێڵ-لیمێتی دوێنێ خۆکارانە بەسەردەچێت
       (کۆن: True ی هەمیشەیی = ئەمڕۆ دەژمێردرێت — سبەی ئازاد دەبێت؛ تەنها lifetime هەمیشەییە)"""
    if not em:
        return False
    today = _lim_today()
    star = em.get("*")
    if star:
        if star is True or str(star) == today:
            return True
    if model_key:
        mv = em.get(model_key)
        if mv and (mv is True or str(mv) == today):
            return True
    return False

def _nv_firebase(ep, email, pw):
    r = requests.post(f"https://identitytoolkit.googleapis.com/v1/accounts:{ep}?key={NV_KEY}",
                      json={"email": email, "password": pw, "returnSecureToken": True},
                      headers={"User-Agent": NV_UA}, timeout=(10, 25))
    if r.status_code != 200:
        return None
    j = r.json() or {}
    tok = j.get("idToken")
    if not tok:
        return None
    return tok, j.get("localId") or ""

def _replace_dead_worker(kind):
    try:
        if kind == "ca":
            st, fn, fz = CA_ST, _ca_signup_new, True
        elif kind == "cb":
            st, fn, fz = CB_ST, _cb_signup_new, True
        elif kind == "nv":
            st, fn, fz = NV_ST, _nv_signup_new, True
        elif kind == "ac":
            st, fn, fz = AC_ST, _ac_signup_new, False
        elif kind == "pia":
            st, fn, fz = PIA_ST, _pia_signup_new, False
        elif kind == "alle":  # #94U49
            st, fn, fz = ALLE_ST, _alle_signup_new, False
        elif kind == "al":  # #94U49
            st, fn, fz = AL_ST, _al_signup_new, False
        elif kind == "em":  # #94U63
            st, fn, fz = EM_ST, _em_signup_new, False
        else:
            return
        if not _REPLACE_SEM.acquire(timeout=120):
            return
        try:
            time.sleep(random.uniform(1, 5))
            accs = st.get("accounts") or []
            today = _lim_today()
            now = time.time()
            lim = st.get("limits") or {}
            exh = st.get("exhausted") or {}
            healthy = sum(1 for a in accs if _pool_acc_alive(a, lim, exh, today, now))
            if healthy >= len(accs):
                return  # هەموو زیندوون (پێشتر جێگۆڕکێ کراوە) — بودجە مەخەرە
            print(f"[REPLACE] {kind}: {healthy}/{len(accs)} زیندوو — جێگۆڕکێ...", flush=True)
            fn(force=True) if fz else fn()
        finally:
            _REPLACE_SEM.release()
    except Exception as e:
        print(f"[REPLACE] {kind}: {str(e)[:50]}", flush=True)

def _rwd_cur():
    _rwd_ensure()
    try:
        return _RWD_UAS[_RWD_STATE["i"] % len(_RWD_UAS)]
    except Exception:
        return _RWD_UAS[0] if _RWD_UAS else ""

def _rwd_ensure():
    """#94U46: حەوزی 1000 — load یان دروستکردن + ڕیسیتی ڕۆژانە + جێگۆڕکێی مردووەکان (lazy)."""
    global _RWD_UAS
    try:
        with _RWD_LK:
            today = _lim_today()
            if not _RWD_UAS or len(_RWD_UAS) < 1000:
                d = _json_load_safe(_rwd_file()) or {}
                _li = d.get("idents") or []
                RWD_ST["used"] = d.get("used") or {}
                RWD_ST["dead"] = d.get("dead") or {}
                RWD_ST["day"] = d.get("day") or ""
                RWD_ST["total"] = d.get("total") or 0
                _ex = set(_li)
                while len(_li) < 1000:
                    _li.append(_rwd_gen_ua(_ex))
                    _ex.add(_li[-1])
                _RWD_UAS = _li
            if RWD_ST.get("day") != today:  # بەیانی نوێ → هەموو بودجەکان دەگەڕێنەوە
                RWD_ST["day"] = today
                RWD_ST["used"] = {}
                RWD_ST["dead"] = {}
                RWD_ST["total"] = 0
                _rwd_save(force=True)
                return
            _dead = RWD_ST.get("dead") or {}
            if _dead and (RWD_ST.get("total") or 0) < RWD_ABSMAX:  # #94U48: هەر مردووێک — یەکسەر (تا 200/جار)
                _ex = set(_RWD_UAS)
                _n_rep = 0
                for _j in range(len(_RWD_UAS)):
                    if _RWD_UAS[_j] in _dead and (RWD_ST.get("total") or 0) < RWD_ABSMAX:
                        _nu = _rwd_gen_ua(_ex)
                        _ex.add(_nu)
                        _dead.pop(_RWD_UAS[_j], None)
                        (RWD_ST.get("used") or {}).pop(_RWD_UAS[_j], None)
                        _RWD_UAS[_j] = _nu
                        RWD_ST["total"] = (RWD_ST.get("total") or 0) + 1
                        _n_rep += 1
                        if _n_rep >= 200:
                            break
                if _n_rep:
                    _rwd_save()
    except Exception:
        pass

def _rwd_gen_ua(existing=None):
    """#94U46: UA ی ڕاستەقینە و ناوازە — Chrome/Edge/Firefox/Safari."""
    import random as _r
    ex = existing or set()
    for _ in range(50):
        _k = _r.random()
        if _k < 0.55:
            _m, _b, _pp = _r.randint(120, 136), _r.randint(1000, 6999), _r.randint(0, 220)
            _pl = _r.choice(["(Windows NT 10.0; Win64; x64)", "(Macintosh; Intel Mac OS X 10_15_7)", "(X11; Linux x86_64)"])
            ua = f"Mozilla/5.0 {_pl} AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{_m}.0.{_b}.{_pp} Safari/537.36"
        elif _k < 0.70:
            _m, _b, _pp = _r.randint(120, 136), _r.randint(1000, 6999), _r.randint(0, 220)
            ua = f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{_m}.0.{_b}.{_pp} Safari/537.36 Edg/{_m}.0.{_b}.{_pp}"
        elif _k < 0.85:
            _v = _r.randint(120, 133)
            _pl = _r.choice(["Windows NT 10.0; Win64; x64", "X11; Linux x86_64", "Macintosh; Intel Mac OS X 10.15"])
            ua = f"Mozilla/5.0 ({_pl}; rv:{_v}.0) Gecko/20100101 Firefox/{_v}.0"
        else:
            _v = _r.choice(["17.4", "17.5", "17.6", "18.0", "18.1"])
            ua = f"Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/{_v} Safari/605.1.15"
        if ua not in ex and ua not in _RWD_UAS:
            return ua
    return f"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.{_r.randint(1000, 9999)}.{_r.randint(0, 99)} Safari/537.36"

def _rwd_save(force=False):
    try:
        _now = time.time()
        if not force and _now - RWD_ST.get("sv_t", 0) < 60:
            return
        RWD_ST["sv_t"] = _now
        _json_save(_rwd_file(), {"idents": _RWD_UAS, "used": RWD_ST.get("used") or {},
                                 "dead": RWD_ST.get("dead") or {}, "day": RWD_ST.get("day") or "",
                                 "total": RWD_ST.get("total") or 0})
    except Exception:
        pass

def _rwd_skip_dead():
    """#94U46: ئەگەر ناسنامەی ئێستا مردووە → بچۆ سەر زیندوو."""
    try:
        with _RWD_LK:
            _dead = RWD_ST.get("dead") or {}
            _used = RWD_ST.get("used") or {}
            for _k in range(min(len(_RWD_UAS), 60)):
                _j = (_RWD_STATE["i"] + _k) % len(_RWD_UAS)
                if _RWD_UAS[_j] not in _dead and (_used.get(_RWD_UAS[_j]) or 0) < RWD_BUDGET:
                    _RWD_STATE["i"] = _j
                    return
        _rwd_next_identity()
    except Exception:
        pass

def _rwd_swap(ua):
    """#94U48: جێگۆڕکێی یەکسەر — مردوو لە هەمان شوێن دەگۆڕدرێت بە تازە (1000 هەمیشە پڕ)."""
    try:
        if (RWD_ST.get("total") or 0) >= RWD_ABSMAX:
            return False
        with _RWD_LK:
            if ua in _RWD_UAS:
                _RWD_UAS[_RWD_UAS.index(ua)] = _rwd_gen_ua(set(_RWD_UAS))
                RWD_ST["total"] = (RWD_ST.get("total") or 0) + 1
            (RWD_ST.get("dead") or {}).pop(ua, None)
            (RWD_ST.get("used") or {}).pop(ua, None)
        _rwd_save()
        return True
    except Exception:
        return False

def _pool_acc_alive(a, lim, exh, today, now):
    """#94U24: زیندوویی یەکگرتوو — وەک rotate ەکان (cooldown-until + general/model-limit)"""
    e = a.get("email") or "?"
    if today in (lim.get(e) or {}).values():
        return False
    v = exh.get(e)
    if v:
        try:
            if float(v) > now:
                return False
        except Exception:
            if str(v)[:10] == today:
                return False
    return True

def _rwd_file():
    return os.path.join(DATA_DIR, "rwd_pool.json")

def cb_servers():
    out = []
    for k, meta in sorted((MS.get("cb_ok") or {}).items()):
        out.append({"id": f"cb-{_cb_slug(k)}", "name": f"{(meta or {}).get('label') or k} (CB)",
                    "model_id": k, "kind": "cb"})
    return out

def ca_servers():
    src = MS.get("ca_ok") or {k: {"version": v[0], "label": v[1]} for k, v in CA_FALLBACK.items()}
    out = []
    for k in sorted(src):
        lbl = (src[k] or {}).get("label") or k
        out.append({"id": f"ca-{re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-')}",
                    "name": f"{lbl} (CA)", "model_id": k, "kind": "ca"})
    return out

def _ca_models_catalog():
    cat = {}
    for k, v in (MS.get("ca_ok") or {}).items():
        cat[k] = (v.get("version") or k, v.get("label") or k)
    for k, v in CA_FALLBACK.items():
        cat.setdefault(k, v)
    return cat

def rwd_servers(timeout=15):
    """سێرڤەرەکانی rewind — بەقوەتەکان + فلاشەکان (بە ڕیزبەندی پشتڕاستکراو)"""
    try:
        live = rwd_models_live(timeout)
    except Exception:
        live = []
    chosen = [m for m in _RWD_VERIFIED if not live or m in live]
    if live:
        for mid in live:
            tail = mid.lower().split("/")[-1].split(":")[0]
            segs = tail.split("-")
            if any(any(s == h or s.startswith(h) for h in _RWD_FREE_HINTS) for s in segs) and mid not in chosen:
                chosen.append(mid)
            if len(chosen) >= 32:
                break
    return [{"id": mid, "name": mid, "model_id": mid, "kind": "rwd"} for mid in chosen]

def al_servers():
    return []  # پارەدار — لابراو لە مینیو (ڕیسێپی پارێزراوە لە کۆد)

def ac_servers():
    src = MS.get("ac_ok") or {k: {"version": v[0], "label": v[1]} for k, v in AC_FALLBACK.items()}
    out = []
    for k in sorted(src):
        lbl = (src[k] or {}).get("label") or k
        out.append({"id": f"ac-{re.sub(r'[^a-z0-9]+', '-', k.lower()).strip('-')}",
                    "name": f"{lbl} (AC)", "model_id": k, "kind": "ac"})
    return out

def nv_servers():
    out = []
    for k, meta in sorted((MS.get("nv_ok") or {}).items()):
        out.append({"id": f"nv-{re.sub(r'[^a-z0-9]+', '-', str(k).lower()).strip('-') or 'model'}",
                    "name": f"{(meta or {}).get('label') or k} (NV)", "model_id": k, "kind": "nv"})
    return out

def alle_servers():
    """٩ مۆدێلی چاتی Alle (هەموو خۆڕایی — خێزانی Gemini)"""
    out = []
    for uid, nm in (("gemini-3-7-flash", "Gemini 3.7 Flash"), ("gemini-3-6-flash", "Gemini 3.6 Flash"),
                    ("gemini-3-5-flash", "Gemini 3.5 Flash"), ("gemini-3-flash", "Gemini 3 Flash"),
                    ("gemini-3-1-pro", "Gemini 3.1 Pro"), ("gemini-3-1-flash-lite", "Gemini 3.1 Flash Lite"),
                    ("gemini-2-5-pro", "Gemini 2.5 Pro"), ("gemini-2-5-flash", "Gemini 2.5 Flash"),
                    ("gemini-2-5-flash-lite", "Gemini 2.5 Flash Lite")):
        out.append({"id": f"alle-{uid}", "name": f"{nm} (Alle)",
                    "model_id": uid, "kind": "alle"})
    return out

AL_MODELS = {
    "gpt-6-astra": "GPT-6 Astra", "gpt-5.6-sol": "GPT-5.6 Sol", "gpt-5.6-terra": "GPT-5.6 Terra",
    "gpt-5.6-luna": "GPT-5.6 Luna", "gpt-5.5": "GPT-5.5", "gpt-5.4": "GPT-5.4",
    "gpt-5.4-mini": "GPT-5.4 mini", "gpt-5.4-nano": "GPT-5.4 nano", "gpt-5": "GPT-5",
    "gpt-5-mini": "GPT-5 mini", "gpt-5-nano": "GPT-5 nano", "gpt-4.1": "GPT-4.1",
    "claude-opus-5": "Claude Opus 5", "claude-opus-4-8": "Claude Opus 4.8", "claude-opus-4-7": "Claude Opus 4.7",
    "claude-opus-4-6": "Claude Opus 4.6", "claude-opus-4-5": "Claude Opus 4.5", "claude-sonnet-5": "Claude Sonnet 5",
    "claude-sonnet-4-6": "Claude Sonnet 4.6", "claude-sonnet-4-5": "Claude Sonnet 4.5",
    "claude-haiku-4-5": "Claude Haiku 4.5", "claude-fable-5-1": "Claude Fable 5.1", "claude-fable-5": "Claude Fable",
    "gemini-3.1-pro": "Gemini 3.1 Pro", "gemini-2.5-pro": "Gemini 2.5 Pro", "gemini-3.8-flash": "Gemini 3.8 Flash",
    "gemini-3.7-flash": "Gemini 3.7 Flash", "gemini-3.6-flash": "Gemini 3.6 Flash", "gemini-3.5-flash": "Gemini 3.5 Flash",
    "gemini-2.5-flash": "Gemini 2.5 Flash", "gemini-3.1-flash-lite": "Gemini 3.1 Flash Lite",
    "grok-4.6": "Grok 4.6", "grok-4.5": "Grok 4.5", "grok-4": "Grok 4", "grok-3": "Grok 3", "grok-3-mini": "Grok 3 mini",
    "deepseek-v4-pro": "DeepSeek V4 Pro", "deepseek-v4-flash": "DeepSeek V4 Flash",
    "deepseek-chat": "DeepSeek V3", "deepseek-reasoner": "DeepSeek R1",
    "openrouter-auto": "OpenRouter Auto", "kimi-k3": "Kimi K3", "moonshot-32k": "Moonshot v1 32k",
    "moonshot-128k": "Moonshot v1 128k", "mistral-large": "Mistral Large", "mistral-medium": "Mistral Medium",
    "mistral-small": "Mistral Small", "auto": "Auto"}

def _cb_slug(v):
    import re as _re
    sl = _re.sub(r"[^a-zA-Z0-9]+", "-", v).strip("-").lower()
    return sl[:60] or "model"

def _proxy_mark_bad(px):
    """#91H: مردوو لە باد-سێت و حەوز یەکسان لادەبرێت؛ #94U39b: 3 زەبر (هێواش ≠ مردوو)؛ #94U41: منزلی 5 زەبر + کەلەپوور + چاکی کلی socks"""
    b = px.replace("http://", "")
    bk = px.split("://", 1)[-1]  # کلیلی strikes (هاوشێوەی سفرکردنەوە لەسەر سەرکەوتن)
    _pool = PROXY_ST.get("pool") or {}
    _pe = _pool.get(b) or _pool.get(bk) or _pool.get(px)
    _was_res = bool((_pe or {}).get("res"))
    _lim = 5 if _was_res else 3
    _st = PROXY_ST.setdefault("strikes", {})
    if len(_st) > 2000:
        _st.clear()
    _st[bk] = (_st.get(bk) or 0) + 1
    if _st[bk] < _lim:
        return False
    PROXY_ST["bad"].add(b)
    if len(PROXY_ST["bad"]) > 5000:  # #94U44: بیرگەی bad سنووردارە
        for _ in range(len(PROXY_ST["bad"]) - 5000):
            PROXY_ST["bad"].pop()
    _st.pop(bk, None)
    try:
        _pool.pop(b, None)
        _pool.pop(bk, None)
        _pool.pop(px, None)
    except Exception:
        pass
    if _was_res:
        _dr = PROXY_ST.setdefault("dead_res", set())
        _dr.add(px)
        while len(_dr) > 500:
            _dr.pop()
    return True

def rwd_models_live(timeout=15):
    """لیستی مۆدێلەکانی rewind — تەنها چاتی ئاسایی، بێ batch/alias"""
    r = requests.get(RWD_BASE + "/v1/models", headers={"User-Agent": UA}, timeout=timeout)
    r.raise_for_status()
    out = []
    for m in r.json().get("models", []):
        mid = m.get("id") or ""
        if m.get("type") != "chat":
            continue
        if ":batch" in mid or mid.startswith("~"):
            continue
        out.append(mid)
    return out

def _al_signup_new():
    """#91AA: سایناپی نوێی allchatbots (Supabase) — پۆڵی ئەکاونت دروست دەکات"""
    try:
        import random as _r, string as _s2
        user = "al" + "".join(_r.choices(_s2.ascii_lowercase + _s2.digits, k=8))
        em, pw = f"{user}@dreameg.com", "Al" + "".join(_r.choices(_s2.ascii_letters + _s2.digits, k=10)) + "!7"
        r = requests.post(AL_SB + "/auth/v1/signup",
                          headers={"apikey": AL_KEY, "Content-Type": "application/json"},
                          json={"email": em, "password": pw}, timeout=(10, 25))
        if r.status_code != 200:
            return False
        AL_ST.setdefault("accounts", []).append({"email": em, "password": pw})
        AL_ST["idx"] = len(AL_ST["accounts"]) - 1
        AL_ST["sess"] = None
        _al_save_acc()
        print(f"[AL] ئەکاونتی نوێ ✅ {em}", flush=True)
        return True
    except Exception as e:
        print(f"[AL] سایناپ: {str(e)[:50]}", flush=True)
        return False

def _alle_signup_new():
    """#94U48: سایناپی نوێی alle-ai — inbox→register→کۆد A-######→verify→login→replicate→conv (زنجیرە سەلمێنراوە)"""
    import random as _r, string as _s, time as _t, re as _re
    try:
        today = _lim_today()
        _accs = ALLE_ST.get("accounts") or []
        _lim = ALLE_ST.get("limits") or {}
        _alive = sum(1 for _a in _accs if today not in (_lim.get(_a.get("email") or "?") or {}).values())
        if len(_accs) >= 10000 or _alive >= 1000:
            return None
        if not _sg_reserve(ALLE_ST, 10000, today, ALLE_LOCK):
            return None
        try:
            _alle_save_acc()  # #94U50: بودجە خێرا پاشەکەوت بکە (هەوڵەکان دیار بن)
        except Exception:
            pass
        _UA = _r.choice([_ALLE_UA, _rand_ua()])
        email, _poll = _tmp_inbox()  # #94U50: temp-mail.org → mail.tm
        if not email or not _poll:
            print("[ALLE] inbox fail (temp-mail 429 + mail.tm)", flush=True)
            return None
        fn_ = _r.choice(["Tara", "Dilan", "Avin", "Shilan", "Hana", "Lana", "Alan", "Aram", "Diyar", "Hemin", "Karwan", "Rebin"])
        ln_ = _r.choice(["Wali", "Karim", "Hassan", "Omar", "Salih", "Aziz", "Mahmud", "Qadir"])
        pw = "Ix" + "".join(_r.choices(_s.ascii_letters + _s.digits, k=10)) + "1!"
        H = {"Accept": "application/json", "Content-Type": "application/json", "User-Agent": _UA,
             "Origin": "https://app.alle-ai.com", "Referer": "https://app.alle-ai.com/auth"}
        rg = requests.post(ALLE_API + "/register",
            json={"first_name": fn_, "last_name": ln_, "email": email, "password": pw, "password_confirmation": pw},
            headers=H, timeout=(10, 30))
        rd = rg.json() or {}
        tok = (rd.get("data") or {}).get("token")
        if rg.status_code != 201 or not tok:
            print(f"[ALLE] register fail: {rg.status_code} {rg.text[:80]}", flush=True)
            return None
        _body = _poll(14, 5)  # #94U50
        _m = _re.search(r'A-\d{6}', _body or "")
        code = _m.group(0) if _m else None
        if not code:
            print(f"[ALLE] کۆد نەگەیشت {email}", flush=True)
            return None
        AH = {**H, "Authorization": "Bearer " + tok}
        v = requests.post(ALLE_API + "/email/verify", json={"code": code}, headers=AH, timeout=(10, 20))
        if v.status_code != 200 or not (v.json() or {}).get("is_valid"):
            print(f"[ALLE] verify fail: {v.status_code} {v.text[:80]}", flush=True)
            return None
        lg = requests.post(ALLE_API + "/login", json={"email": email, "password": pw}, headers=H, timeout=(10, 30))
        ld = (lg.json() or {}).get("data") or {}
        ftok, uid = ld.get("token"), (ld.get("user") or {}).get("id")
        if lg.status_code != 200 or not ftok:
            print(f"[ALLE] login fail: {lg.status_code}", flush=True)
            return None
        rp = requests.post(ALLE_API + f"/share/{ALLE_SHARE}",
            headers={**H, "Authorization": "Bearer " + ftok}, timeout=(10, 30))
        sess = ((rp.json() or {}).get("data") or {}).get("session")
        if rp.status_code != 200 or not sess:
            print(f"[ALLE] replicate fail: {rp.status_code} {rp.text[:80]}", flush=True)
            return None
        with ALLE_LOCK:
            ALLE_ST.setdefault("accounts", []).append(
                {"email": email, "password": pw, "token": ftok, "uid": uid, "conv": sess, "pos": 1, "ua": _UA})
            _alle_save_acc()
        print(f"[ALLE] ئەکاونتی نوێ ✅ {email} uid={uid}", flush=True)
        return True
    except Exception as e:
        print(f"[ALLE] سایناپ: {str(e)[:60]}", flush=True)
        return None

def _ac_signup_new():
    import datetime as _dt
    today = _dt.datetime.utcnow().strftime("%Y-%m-%d")
    sg = AC_ST.get("signups") or {"date": "", "n": 0}
    if sg.get("date") != today:
        sg = {"date": today, "n": 0}
    if len(AC_ST.get("accounts") or []) >= 10000:  # #94U32: 40→300؛ #94U47: →10000 (وەک CA/CB/NV)
        return None
    if not _sg_breaker_allow(AC_KEY):  # #94U34
        return None
    if not _sg_reserve(AC_ST, 10000, today, _AC_LK):  # #94U23 بودجە لەژێر لۆک؛ #94U47: 200→10000/ڕۆژ (breaker دەیپارێزێت)
        print(f"[AC] day-cap hit n={(AC_ST.get('signups') or {}).get('n')}", flush=True)  # #119
        return None
    n = AC_ST["next_num"] + random.randint(0, 2000)  # #94U32 jitter
    for _ in range(6):
        email = f"komex{n}@duidir.com"
        pw = f"{email}#{random.randint(10000, 99999)}"
        res = _fb_signup(AC_KEY, email, pw, _rand_ua())  # #94U32: proxy-first لەبری _ac_firebase ی ڕاستەوخۆ
        if res:
            acc = {"email": email, "password": pw, "boot": True, "ua": _rand_ua()}
            try:
                _ac_bootstrap(res[0], res[1], email)
            except Exception as e:
                print(f"[AC] bootstrap fail {email}: {e}", flush=True)
            AC_ST["accounts"] = (AC_ST.get("accounts") or []) + [acc]
            AC_ST["idx"] = len(AC_ST["accounts"]) - 1
            AC_ST["next_num"] = n + 1
            AC_ST["tok"] = None
            _ac_save_acc()
            print(f"[AC] ئەکاونتی نوێ ✅ {email}", flush=True)
            return res
        time.sleep(random.uniform(1.0, 2.0))  # #94U32 jitter
        n += 1
    AC_ST["next_num"] = n
    _ac_save_acc()
    print("[AC] all 6 emails failed this round", flush=True)  # #119
    return None

def _sg_breaker_allow(key):
    """#94U34: ئایا ساینئەپ بۆ ئەم کلیلە ڕێگەپێدراوە؟ (دوای 10 شکستی throttle لەسەریەک → پشووی 2h)"""
    try:
        with _SG_BREAKER_LK:
            b = _SG_BREAKER.get(key) or {}
            return not (b.get("until", 0) > time.time())
    except Exception:
        return True

def _sg_reserve(ST, cap, today, lock):
    """#94U23: بودجەی ساینئەپ — پشکنین+تۆمار لەژێر لۆک (ڕەیس-دژە؛ کاپ ڕەق؛ هەوڵی شکستخواردووش بودجە دەخوات)"""
    try:
        with lock:
            sg = ST.get("signups") or {"date": "", "n": 0}
            if sg.get("date") != today:
                sg = {"date": today, "n": 0}
            if sg.get("n", 0) >= cap:
                ST["signups"] = sg
                return False
            sg["n"] = sg.get("n", 0) + 1
            ST["signups"] = sg
            return True
    except Exception:
        return False

_PIA_FASTPOLL = [False]  # V10.3: cron sets True (24s max poll)


def _pia_signup_new():
    """#91PIA-AUTO: ئەکاونتی نوێی piax — temp-mail.org + کۆد + لۆگین (هەموو خۆکارانە لە VM)"""
    try:
        today = time.strftime("%Y-%m-%d", time.gmtime())
        sg = PIA_ST.get("signups") or {"date": "", "n": 0}
        if sg.get("date") != today:
            sg = {"date": today, "n": 0}
        if len(PIA_ST.get("accounts") or []) >= 10000:  # #94U32: 12→60؛ #94U47: →10000
            return None
        if not _sg_reserve(PIA_ST, 300, today, PIA_LOCK):  # #94U23 بودجە لەژێر لۆک؛ #94U47: 30→300/ڕۆژ (temp-mail سنووردارە)
            return None
        email, _poll = _tmp_inbox()  # #94U50: temp-mail.org → mail.tm
        if not email or not _poll:
            print("[PIA-SIGNUP] mailbox fail (temp-mail 429 + mail.tm)", flush=True)
            return None
        s2 = requests.Session()
        s2.headers.update({"User-Agent": _rand_ua(), "Accept-Language": "en",
                           "Origin": "https://www.piax.org", "Referer": "https://www.piax.org/"})
        _px_win, r2 = None, None
        for _px in (_proxy_signup_best(4) + [None]):  # #119: proxy-first
            try:
                _kw = {"json": {"channel": "pia", "email": email, "device": {"deviceType": "pc", "osPlatform": "web"}},
                       "timeout": (10, 40)}
                if _px:
                    _kw["proxies"] = {"http": _px, "https": _px}
                r2 = s2.post(PIA_API + "/user-api/user/sendEmailVerifyCode", **_kw)
                if (r2.json() or {}).get("code") == 1:
                    _px_win = _px
                    break
            except Exception:
                r2 = None
                continue
        if r2 is None or (r2.json() or {}).get("code") != 1:
            print(f"[PIA-SIGNUP] sendCode fail: {(r2.text[:80] if r2 is not None else 'net')}", flush=True)
            return None
        _pn, _pi = ((4, 6) if _PIA_FASTPOLL[0] else (16, 6))  # V10.3: cron fast-poll
        _body = _poll(_pn, _pi)  # #94U50
        _nums = re.findall(r"\b(\d{4,8})\b", _body or "")
        code = _nums[0] if _nums else None
        if not code:
            print(f"[PIA-SIGNUP] کۆد نەگەیشت {email}", flush=True)
            return None
        _kw5 = {"json": {"email": email, "code": code, "channel": "pia"}, "timeout": (10, 40)}
        if _px_win:
            _kw5["proxies"] = {"http": _px_win, "https": _px_win}
        r5 = s2.post(PIA_API + "/user-api/user/emailLogin", **_kw5)
        d5 = r5.json() or {}
        if not d5.get("token"):
            print(f"[PIA-SIGNUP] login fail: {r5.text[:100]}", flush=True)
            return None
        with PIA_LOCK:
            PIA_ST.setdefault("accounts", []).append({"email": email, "token": d5["token"]})
            _pia_save_acc()
        print(f"[PIA-SIGNUP] ئەکاونتی نوێ ✅ {email}", flush=True)
        return email
    except Exception as e:
        print(f"[PIA-SIGNUP] {str(e)[:80]}", flush=True)
        return None

def _g4f_ensure_credits(min_credits=6, bake_max=2):
    """کەیک بنێژە ئەگەر کریت کەمە (١ کەیک = ٥ کریت، ~٥-١٥ چرکە)"""
    with _G4F_BAKE_LOCK:
        try:
            st = _g4f_status()
        except Exception:
            return
        _G4F_CREDIT["v"] = int(st.get("credit_cents") or 0)
        if _G4F_CREDIT["v"] >= min_credits:
            return
        diff = int(st.get("difficulty") or 24)
        try:
            r = requests.get(G4F_BASE + "/cake/issue?n=" + str(bake_max),
                             headers=_g4f_headers(), timeout=(10, 15))
            uuids = (r.json() or {}).get("uuids") or []
        except Exception:
            return
        for u_id in uuids:
            tot = _g4f_bake_one(u_id, diff)
            if tot:
                _G4F_CREDIT["v"] = tot
            time.sleep(0.3)
            if _G4F_CREDIT["v"] >= min_credits:
                break

def _g4f_headers():
    return {"User-Agent": _pick_ua(ACT_UAS),
            "Content-Type": "application/json",
            "Referer": "https://g4f.dev/"}

def act_chat(model_id, messages, timeout=110):
    """چات بۆ aichatting — SSE، ناسنامەی خۆکار (کوات تەواو بوو → نوێی دەکاتەوە)"""
    for attempt in (0, 1):
        visitor_id, raw_token, cookie_token = _act_identity()
        ua = ACT_UAS[_ACT_STATE["i"] % len(ACT_UAS)]
        h = {
            "User-Agent": ua, "source": "web", "lang": "en",
            "Content-Type": "application/json",
            "Cookie": "aichatting.website.visitorId=" + cookie_token,
            "vToken": raw_token,
            "Origin": "https://www.aichatting.net",
            "Referer": "https://www.aichatting.net/free-chatgpt/",
            "Accept": "text/event-stream,application/json",
        }
        msgs = _sys_keep([{"role": m["role"], "content": [{"type": "text", "text": m["content"]}]}
                            for m in messages if m.get("role") in ("user", "assistant", "system")], 19)
        payload = {"spaceHandle": True, "roleId": None, "messages": msgs,
                   "conversationId": None, "model": model_id}
        try:
            r = requests.post(ACT_BASE + "/aigc/chat/v2/askai/stream",
                              headers=h, json=payload, timeout=(15, timeout))
        except Exception as e:
            if attempt == 0:
                continue
            raise EMError(f"act: {str(e)[:60]}")
        if r.status_code == 401 and attempt == 0:
            continue  # ناسنامەی نوێ
        if r.status_code != 200:
            if attempt == 0:
                continue
            raise EMError(f"act: {r.status_code}")
        # SSE — data: بەشەکان، "--@DONE@--" کۆتایی (UTF-8 — r.text عەرەبی تێکدەدات)
        # ئاماژەکانی ئەوان: "-=- --" = بۆشایی، "-=-n--" = هێڵی نوێ (لە c3.js)
        out = []
        for line in r.content.decode("utf-8", "replace").splitlines():
            if line.startswith("data:"):
                part = line[5:]
                if part.startswith(" "):
                    part = part[1:]
                part = part.rstrip("\r")
                if part and part != "--@DONE@--":
                    out.append(part)
        ans = "".join(out).replace("-=- --", " ").replace("-=-n--", "\n").strip()
        if ans:
            return ans
        if attempt == 0:
            continue
    raise EMError("act: وەڵام نەگەڕایەوە")

def act_servers():
    """سێرڤەرەکانی aichatting — هەموو مۆدێلە پشتڕاستکراوەکان"""
    return [{"id": "act-" + m, "name": m, "model_id": m, "kind": "act"} for m in ACT_MODELS]

def aiml_chat(messages, model_id, timeout=110):
    """چاتی AI/ML API — OpenAI-جۆر — 403 (فەندز) → فەیلئۆڤەر"""
    lines = []
    for m in _sys_keep(messages, 19):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        lines.append({"role": role, "content": c})
    if not lines:
        raise EMError("aiml: هیچ نامە")
    key = _aiml_ensure_key()
    try:
        r = requests.post("https://api.aimlapi.com/v1/chat/completions",
                          headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json",
                                   "User-Agent": "Mozilla/5.0"},
                          json={"model": model_id, "messages": lines}, timeout=(15, timeout))
    except Exception as e:
        raise EMError(f"aiml: {str(e)[:60]}")
    if r.status_code in (401, 403):
        try:
            j = r.json()
        except Exception:
            j = {}
        msg = str((j.get("message") or j.get("error") or ""))[:60]
        if "funds" in msg.lower():
            MS.get("aiml_ok", {}).pop(model_id, None)
            _ms_save()
            raise EMError("aiml: فەندز — دەگوازرێتەوە بۆ سەرچاوەی هەمان مۆدێڵ")
        if r.status_code == 401:
            # #91AA: token+key یەکسان نوێ بکرێنەوە — بێ دەستێوەردان
            def _aiml_renew():
                try:
                    AIML_ST["tok"] = None
                    AIML_ST["key"] = None
                    AIML_ST["tok_t"] = 0.0
                    _aiml_login()
                    _aiml_ensure_key()
                    print("[AIML] 🔁 token+key نوێ کرایەوە", flush=True)
                except Exception:
                    pass
            threading.Thread(target=_aiml_renew, daemon=True).start()
            raise EMError("aiml: توکن")
        raise EMError(f"aiml: {msg or r.status_code}")
    if r.status_code == 429:
        raise EMError("aiml: لیمیت")
    if r.status_code != 200:
        raise EMError(f"aiml: HTTP{r.status_code}")
    try:
        j = r.json()
        ans = (j.get("choices") or [{}])[0].get("message", {}).get("content", "")
        if isinstance(ans, list):
            ans = "".join(x.get("text", "") for x in ans if isinstance(x, dict))
        ans = (ans or "").strip()
        if ans:
            return ans
    except Exception:
        pass
    raise EMError("aiml: بەتاڵ")

def aiml_servers():
    return []  # پارەدار — لابراو لە مینیو (ڕیسێپی پارێزراوە لە کۆد)

def aka_chat(messages, model_id="openai-gpt-oss-120b", timeout=110):
    """چاتی akash — سیستەم-پرۆمپت لە مێژوو دەهێنرێت (بەتاڵ = نیوتراڵ)؛ 403 سێشن → ڕۆتەیشن؛ #94U49: 429 → سێشن+پرۆکسی نوێ"""
    import time as _t
    if _t.time() < AKA_LIMIT["until"]:
        raise EMError("aka: cooldown")
    sys_content = ""
    rest = []
    for m in messages:
        if m.get("role") == "system" and not sys_content:
            sys_content = m.get("content") or ""
        elif m.get("content"):
            rest.append(m)
    if not sys_content:
        sys_content = _AKA_NEUTRAL
    _pxs = _px_list(2)
    last_err = None
    for attempt in range(3):
        _px = _pxs[attempt] if attempt < len(_pxs) else None
        try:
            if attempt == 0 and _AKA["ses"]:
                s = _AKA["ses"]
            else:
                s = _aka_session(force=True, px=_px)
        except Exception as e:
            last_err = e
            continue
        cid = "".join(random.choices(_AKA_CHARS, k=12))
        hist = rest[-10:]
        body = {"id": cid,
                "messages": [{"role": m.get("role", "user"), "content": m.get("content") or "",
                              "parts": [{"type": "text", "text": m.get("content") or ""}]} for m in hist],
                "model": model_id, "system": sys_content, "temperature": 0.6, "topP": 0.95, "context": []}
        try:
            r = s.post(AKA_BASE + "/api/chat/", json=body, timeout=(15, timeout), stream=True)
        except Exception as e:
            last_err = EMError(f"aka: {str(e)[:60]}")
            continue
        if r.status_code == 403 or r.status_code == 401:
            _AKA["ses"] = None
            last_err = EMError(f"aka: {r.status_code} سێشن")
            continue
        if r.status_code == 429:
            _AKA["ses"] = None
            last_err = EMError("aka: 429")
            continue
        if r.status_code != 200:
            if r.status_code in (400, 500) and model_id in MS.get("aka_ok", {}):
                MS["aka_ok"].pop(model_id, None)
                MS.setdefault("aka_bad", {})[model_id] = {"code": r.status_code, "t": _t.time()}
                _ms_save()
            raise EMError(f"aka: {r.status_code}")
        raw = b""
        try:
            for ch in r.iter_content(512):
                raw += ch
                if len(raw) > 120_000:
                    break
        except Exception:
            pass
        t = raw.decode("utf-8", "replace")
        texts = re.findall(r'^0:"(.*)"', t, re.M)
        try:
            ans = "".join(json.loads(f'"{x}"') for x in texts)
        except Exception:
            ans = "".join(texts)
        ans = ans.strip()
        if ans:
            return ans
        last_err = EMError("aka: وەڵام بەتاڵ")
    if last_err and "429" in str(last_err):
        AKA_LIMIT["until"] = _t.time() + 900
        raise EMError("aka: 429 → دیلی ١٥ خولەک")
    raise last_err or EMError("aka: شکست")

def aka_servers():
    out = []
    for mid in list(MS.get("aka_ok", {}).keys())[:6]:
        label = "GPT-OSS 120B" if "gpt-oss" in str(mid) else str(mid).replace("-", " ").title()
        slug = re.sub(r'[^a-z0-9.]+', '-', str(mid).lower()).strip('-')
        out.append({"id": f"aka-{slug}", "name": f"{label} (Akash)",
                    "model_id": mid, "kind": "aka"})
    return out

def cbc_chat(messages, model=None, timeout=120):
    """پرسیار بۆ chatbotchatapp — GPT-5 (تەنها مۆدێڵی بێ login) — دەقی تەواو دەگەڕێنێتەوە"""
    import hashlib as _hl
    import uuid as _uu
    msgs = [m for m in (messages or []) if isinstance(m, dict) and m.get("content")][-10:]
    if not msgs:
        msgs = [{"role": "user", "content": "سلام"}]
    arr = [{"role": ("user" if m.get("role") == "user" else "assistant"),
            "content": str(m.get("content"))[:4000]} for m in msgs]
    modal = "model-gpt-5" if not model else str(model)
    if modal == "gpt-5":
        modal = "model-gpt-5"
    last_err = "cbc: وەڵامی بەتاڵ"
    for _px in [None] + list(_proxy_get(3) or []):
        try:
            s = requests.Session()
            s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"})
            _kw = {"proxies": {"http": _px, "https": _px}} if _px else {}
            home = s.get(CBC_BASE + "/", timeout=(10, 20), **_kw).text
            m = re.search(r'name="csrf-token" content="([^"]+)"', home or "")
            if not m:
                last_err = "cbc: no csrf"
                continue
            csrf = m.group(1)
            ts = s.post(CBC_BASE + "/api/get-timestamp", data={"href": CBC_BASE + "/"},
                        headers={"X-CSRF-TOKEN": csrf, "X-Requested-With": "XMLHttpRequest"},
                        timeout=(10, 20), **_kw).json()
            r = int(ts.get("timestamp") or 0)
            if not r:
                last_err = "cbc: no timestamp"
                continue
            content = arr[r % len(arr)]["content"]
            nonce = str(_uu.uuid4())
            acc = "timestamp%dnonce%smessages%skeyTokenXXXXXXYYYvv1" % (r, nonce, content)
            mid = _hl.md5(acc.encode()).hexdigest()
            payload = {"id": mid, "timestamp": r, "nonce": nonce, "messages": arr,
                       "url": CBC_BASE + "/", "modal": modal,
                       "conversationId": str(_uu.uuid4())}
            rr = s.post(CBC_BASE + "/api", json=payload,
                        headers={"X-CSRF-TOKEN": csrf, "Accept": "text/event-stream"},
                        timeout=(15, timeout), stream=True, **_kw)
            if rr.status_code == 429:
                last_err = "cbc: سنووری ڕێژە (429)"
                continue
            if rr.status_code != 200:
                last_err = "cbc: %s" % rr.status_code
                continue
            out = []
            rr.encoding = "utf-8"  # #110U2: latin-1 mojibake guard
            for line in rr.text.splitlines():
                line = line.strip()
                if not line.startswith("data:"):
                    continue
                tok = line[5:].strip()
                if not tok.startswith("{"):
                    continue
                try:
                    j = json.loads(tok)
                except Exception:
                    continue
                if j.get("code") == "dailyChatLimitOfGuest":
                    last_err = "cbc: سنووری ڕۆژانەی میوان"
                    out = None
                    break
                try:
                    for ch in j.get("choices") or []:
                        parts = ((ch.get("content") or {}).get("parts")) or []
                        for p in parts:
                            t = p.get("text") or ""
                            if t:
                                out.append(t)
                except Exception:
                    pass
            if out is None:
                continue
            ans = "".join(out).strip()
            if ans:
                return ans
            last_err = "cbc: وەڵامی بەتاڵ"
        except Exception as e:
            last_err = "cbc: %s" % str(e)[:70]
    raise EMError(last_err)
def cbox_chat(messages, model_key="aichat", timeout=110, depth=0):
    """چاتی chat-box.ai — SSE (chunk/complete)؛ مولتی‌پارت؛ ئەکاونت-ڕۆتەیشن + refresh + دروستکردنی خۆکار"""
    acc = _cbox_pick()
    if not acc:
        raise EMError("cx: ئەکاونت نەدروست بوو")
    sys_txt = " ".join(m["content"] for m in messages if m.get("role") == "system")[:32000]
    rest = [m for m in messages if m.get("role") != "system"][-8:]
    q = ""
    for m in rest[:-1]:
        who = "بەکارهێنەر" if m.get("role") == "user" else "وەڵام"
        q += f"{who}: {str(m.get('content'))[:600]}\n"
    last = rest[-1] if rest else {"role": "user", "content": "سلام"}
    if sys_txt:
        q = f"[ئاراستەی سیستەم: {sys_txt}]\n{q}"
    q += f"بەکارهێنەر: {last.get('content')}"
    mid = CBOX_FREE_ID
    for _ in range(2):
        parts = []
        final_msg = ""
        try:
            rt = "WebSearch" if str(model_key) == "websearch" else "Text"
            files = [("message", (None, q[:8000])),
                     ("modelId", (None, mid)),
                     ("roomType", (None, rt))]
            r = requests.post(CBOX_API + "/chat/stream", files=files,
                              headers={"User-Agent": _CBOX_UA, "Accept": "text/event-stream",
                                       "Origin": "https://chat-box.ai", "Referer": "https://chat-box.ai/app/en",
                                       "X-Device-Fingerprint": acc.get("fp") or "",
                                       "x-device-fingerprint": acc.get("fp") or "",
                                       "x-user-origin-source": "ads",
                                       "Authorization": "Bearer " + (acc.get("at") or "")},
                              timeout=(12, timeout), stream=True)
            if r.status_code == 401:
                if _cbox_refresh(acc):
                    continue
                acc["dead"] = 1
                with CBOX_LOCK:
                    _cbox_save()
                na = _cbox_new_account()
                if na and depth == 0:
                    return cbox_chat(messages, model_key, timeout, depth=1)
                raise EMError("cx: توکن مردووە")
            if r.status_code in (403, 429):
                body = ""
                try:
                    body = r.text[:300]
                except Exception:
                    pass
                # FEATURE_NOT_SUPPORTED → ئەکاونت ناکات → نوێ
                acc["dead"] = 1
                with CBOX_LOCK:
                    _cbox_save()
                na = _cbox_new_account()
                if na and depth == 0:
                    return cbox_chat(messages, model_key, timeout, depth=1)
                raise EMError(f"cx: gate {r.status_code} {body[:80]}")
            err_evt = None
            for raw in r.iter_lines(chunk_size=None):
                if not raw:
                    continue
                ln = raw.decode("utf-8", "ignore").strip() if isinstance(raw, bytes) else str(raw).strip()
                if not ln.startswith("data:"):
                    continue
                payload = ln[5:].strip()
                try:
                    d = json.loads(payload)
                except Exception:
                    continue
                if isinstance(d, dict) and d.get("error"):
                    err_evt = str((d.get("error") or {}).get("errors", [{}])[0].get("type") if (d.get("error") or {}).get("errors") else (d.get("error") or {}).get("message") or "error")
                    break
                ev = (d.get("event") or {}) if isinstance(d, dict) else {}
                et = ev.get("type")
                if et == "chunk" and ev.get("content"):
                    parts.append(str(ev["content"]))
                elif et == "complete":
                    fm = ev.get("fullMessage") or {}
                    final_msg = str(fm.get("message") or "")
                    ws = fm.get("webSearch") or {}
                    _wsl = ws.get("links") or []
                    if _wsl:
                        try:
                            _src = "\n".join(f"🔗 {l.get('title') or 'source'}: {l.get('url') or l}" for l in _wsl[:4] if l)
                            if _src:
                                final_msg = (final_msg or "") + "\n" + _src
                        except Exception:
                            pass
                elif et == "error":
                    err_evt = str(ev.get("error") or ev.get("message") or "stream error")
                    break
            if err_evt:
                low = err_evt.lower()
                if any(x in low for x in ("free_tier", "limit", "quota", "usage", "subscription", "not_supported")):
                    acc["dead"] = 1
                    with CBOX_LOCK:
                        _cbox_save()
                    na = _cbox_new_account()
                    if na and depth == 0:
                        return cbox_chat(messages, model_key, timeout, depth=1)
                    raise _CxLimit(err_evt[:90])
                # #94U42: هەڵەی کاتی سێرڤەر (SERVER_ERROR) → یەک دووبارە بە ئەکاونتی نوێ، نەک ❌ یەکسەر
                if depth == 0:
                    try:
                        na = _cbox_new_account()
                    except Exception:
                        na = None
                    if na:
                        return cbox_chat(messages, model_key, timeout, depth=1)
                raise EMError(f"cx: {err_evt[:90]}")
            ans = (final_msg or "".join(parts)).strip()
            if not ans:
                raise EMError("cx: وەڵام بەتاڵ")
            # سەرکەوتوو — ژماردن
            today = time.strftime("%Y-%m-%d", time.gmtime())
            if acc.get("day") != today:
                acc["day"], acc["n"] = today, 0
            acc["n"] = int(acc.get("n") or 0) + 1
            with CBOX_LOCK:
                _cbox_save()
            return ans
        except _CxLimit as e:
            raise EMError(f"cx: {e}")
        except EMError:
            raise
        except Exception as e:
            s = str(e)
            if depth == 0:
                na = _cbox_new_account()
                if na:
                    return cbox_chat(messages, model_key, timeout, depth=1)
            raise EMError(f"cx: {s[:80]}")
    raise EMError("cx: دووبارە بوونەوە سەرکەوتوو نەبوو")

def cbox_servers():
    out = []
    for key, model, nm in CBOX_MODELS:
        out.append({"id": f"cx-{key}", "name": f"{nm} (Chatbox)", "model_id": key, "kind": "cbox"})
    return out

def ct_chat(messages, model_id="gpt-5.6-luna", timeout=150):
    """چاتی chattide.ai — میوان: ٢ چات/ڕۆژ بۆ هەر IP؛ کۆدی 229 → پرۆکسی داهاتوو (#94U49)؛ ئەگەر هەموو تەواو → دیلی تا نیوەشەوی UTC"""
    import time as _t
    if _t.time() < CT_LIMIT["quota_until"]:
        raise EMError("ct: daily quota (2/IP/day)")
    if _t.time() < CT_LIMIT["wobble_until"]:
        raise EMError("ct: wobble cooldown")
    body = {"spaceHandle": True, "roleId": 0, "conversationId": None, "model": model_id,
            "messages": [{"role": m.get("role", "user"),
                          "content": [{"type": "text", "text": m.get("content") or ""}]} for m in messages]}
    _last = EMError("ct: شکست")
    for _px in _px_list(3):  # #94U49: ناسنامەی نوێ + IP ی نوێ بۆ هەر هەوڵێک
        hd, ck = _ct_identity()
        _kw = {"proxies": {"http": _px, "https": _px}} if _px else {}
        try:
            r = requests.post("https://api.chattide.ai/aigc/chat/v2/professional/stream",
                              json=body, headers=hd, cookies=ck, timeout=(15, timeout), **_kw)
        except Exception as e:
            _last = EMError(f"ct: {str(e)[:60]}")
            continue
        if r.status_code in (429, 403):
            _last = EMError("ct: 229 quota")
            continue
        if r.status_code != 200:
            raise EMError(f"ct: {r.status_code}")
        txt = r.text
        if '"code":229' in txt or "quota has been exhausted" in txt:
            _last = EMError("ct: 229 quota")
            continue
        out = []
        _wob = False
        for line in txt.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            tok = line[5:].strip()
            if not tok or tok == "--@DONE@--":
                continue
            if tok.startswith("Please refresh"):
                _wob = True
                break
            if tok.startswith("{"):
                try:
                    j = json.loads(tok)
                except Exception:
                    continue
                if str(j.get("code")) == "229" or "quota" in str(j.get("message") or "").lower():
                    _last = EMError("ct: 229 quota")
                    out = None
                    break
                continue
            out.append(tok)
        if out is None:
            continue
        if _wob:
            _last = EMError("ct: refresh-wobble")
            continue
        ans = "".join(out).replace("-=- --", " ").replace("-=-n--", "\n").strip()
        ans = re.sub(r" {3,}", "  ", ans)
        if not ans:
            _last = EMError("ct: وەڵام بەتاڵ")
            continue
        CT_LIMIT["quota_until"] = 0.0
        CT_LIMIT["wobble_until"] = 0.0
        return ans
    if "229" in str(_last) or "quota" in str(_last):
        CT_LIMIT["quota_until"] = _ct_quota_ts()
        raise EMError("ct: 229 quota → دیلی بۆ نیوەشەوی UTC")
    if "wobble" in str(_last) or "بەتاڵ" in str(_last):
        CT_LIMIT["wobble_until"] = _t.time() + 600
    raise _last

def ct_servers():
    ids = list(MS.get("ct_ok", {}).keys()) or [f for f, _ in _CT_FALLBACK]
    labels = dict(_CT_FALLBACK)
    out = []
    for mid in ids[:6]:
        label = labels.get(mid, _ct_label(mid))
        slug = re.sub(r'[^a-z0-9.]+', '-', str(mid).lower()).strip('-')
        out.append({"id": f"ct-{slug}", "name": f"{label} (ChatTide)",
                    "model_id": mid, "kind": "ct"})
    return out

def duck_chat(model_id, messages, timeout=110):
    """چاتی duck.ai — system دەفڕێتە ناو یەکەم نامەی بەکارهێنەر + سێشن/پرۆکسی نوێ (#94U49)"""
    global DUCK_SESSION
    sys_txt = " ".join(m["content"] for m in messages if m.get("role") == "system")[:32000]
    rest = [m for m in messages if m.get("role") != "system"][-21:]
    if rest and rest[0].get("role") == "user" and sys_txt:
        rest[0] = dict(rest[0])
        rest[0]["content"] = f"[ئاراستەی سیستەم: {sys_txt}]\n\n{rest[0]['content']}"
    elif sys_txt:
        rest = [{"role": "user", "content": f"[ئاراستەی سیستەم: {sys_txt}]"}] + rest
    last = None
    for i, _px in enumerate(_px_list(2)):
        if i > 0:  # #94U49: سێشنی نوێ + IP ی نوێ
            try:
                DUCK_SESSION = None
                DUCK_WARMED[0] = False
            except Exception:
                pass
        try:
            return _duck_attempt(model_id, rest, timeout, px=_px)
        except EMError as e:
            last = e
            if "418" not in str(e) and "429" not in str(e):
                raise
            time.sleep(1.5 + i)
    raise last or EMError("duck: شکست")

def duck_servers():
    return [
        {"id": "duck-gpt-5.4-mini", "name": "GPT 5.4 Mini (Duck)",
         "model_id": "gpt-5.4-mini", "kind": "duck"},
        {"id": "duck-claude-haiku-4-5", "name": "Claude Haiku 4.5 (Duck)",
         "model_id": "claude-haiku-4-5", "kind": "duck"},
        {"id": "duck-mistral-small", "name": "Mistral Small (Duck)",
         "model_id": "mistral-small-2603", "kind": "duck"},
        {"id": "duck-gpt-oss-120b", "name": "GPT OSS 120B (Duck)",
         "model_id": "tinfoil/gpt-oss-120b", "kind": "duck"},
        {"id": "duck-gemma-4-31b", "name": "Gemma 4 31B (Duck)",
         "model_id": "tinfoil/gemma4-31b", "kind": "duck"},
    ]

def fla_chat(messages, timeout=110):
    """چاتی flatai — یەک مۆدێڵی سێرڤەری (GLM)؛ #94U49: کواتی ڕۆژانەی IP → سێشنی نوێ بە پرۆکسی"""
    import uuid as _uuid
    msgs = _sys_keep([{"role": m["role"], "content": m["content"]}
                        for m in messages if m.get("role") in ("user", "assistant", "system")], 19)
    sys_txt = ""
    for _i, _m in enumerate(msgs):  # #94U25: system لە هەر شوێنێک بێت بدۆزەرەوە
        if _m.get("role") == "system" and _m.get("content"):
            sys_txt = msgs.pop(_i)["content"]
            break

    def F(**kv):
        return {k: (None, v) for k, v in kv.items()}

    _last = EMError("fla: شکست")
    for _px in _px_list(3):  # #94U49: سێشنی WP ی نوێ + IP ی نوێ بۆ هەر هەوڵێک
        s = requests.Session()
        s.headers.update({
            "User-Agent": _pick_ua(ACT_UAS),
            "Origin": "https://flatai.org",
            "Referer": "https://flatai.org/free-ai-chatbot-no-registration/",
        })
        if _px:
            s.proxies.update({"http": _px, "https": _px})
        try:
            s.get("https://flatai.org/free-ai-chatbot-no-registration/", timeout=(15, 30))
            r = s.post(FLA_AJAX, files=F(action="chatbot2_session"), timeout=(15, 30))
            sess = r.json()["data"]
            r = s.post(FLA_AJAX, files=F(action="chatbot2_history", nonce=sess["nonce"],
                                         history_nonce=sess["history_nonce"], operation="load"),
                       timeout=(15, 30))
            ld = r.json()["data"]
            chat_id = str(_uuid.uuid4())
            chats = json.loads(ld["values"].get("allChats", "{}"))
            chats[chat_id] = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime()),
                              "title": "New conversation", "messages": []}
            s.post(FLA_AJAX, files=F(action="chatbot2_history", nonce=sess["nonce"],
                                     history_nonce=sess["history_nonce"], operation="save",
                                     values=json.dumps({**ld["values"], "allChats": json.dumps(chats)}),
                                     revision=str(ld["revision"])), timeout=(15, 30))
            r = s.post(FLA_AJAX, files=F(action="my_chatbot", nonce=sess["nonce"],
                                         history_nonce=sess["history_nonce"],
                                         request_id=str(_uuid.uuid4()), chat_id=chat_id,
                                         messages=json.dumps(msgs),
                                         system_message_content=sys_txt),
                       timeout=(15, timeout))
            if r.status_code == 429:
                _last = EMError("fla: کواتی ڕۆژانە تەواو (IP)")
                continue
            ct = r.headers.get("content-type", "")
            if r.status_code != 200 or "event-stream" not in ct:
                _last = EMError(f"fla: {r.status_code}")
                continue
            text = ""
            for line in r.content.decode("utf-8", "replace").splitlines():
                if line.startswith("data: "):
                    try:
                        d = json.loads(line[6:])
                        if isinstance(d, dict) and isinstance(d.get("text"), str) and d["text"]:
                            text = d["text"]  # کۆتا (done) دەباتەوە
                    except Exception:
                        pass
            if text.strip():
                return text.strip()
            _last = EMError("fla: وەڵام نەگەڕایەوە")
        except EMError as e:
            if "کوات" in str(e):
                _last = e
                continue
            raise
        except Exception as e:
            _last = EMError(f"fla: {str(e)[:60]}")
    raise _last

def fla_servers():
    return [{"id": "flatai-glm", "name": "GLM (flatai)", "model_id": "glm", "kind": "fla"}]

def g4f_chat(messages, model_id, timeout=110):
    """چاتی g4f.space — کریتی PoW؛ ٤٠٢/٤٢٩ → ١٥ خولەک cooldown"""
    import time as _t
    if _t.time() < G4F_LIMIT["until"]:
        raise EMError("g4f: cooldown")
    if _G4F_CREDIT["v"] < 4:
        _g4f_ensure_credits(min_credits=4, bake_max=1)
    try:
        r = requests.post(G4F_BASE + "/v1/chat/completions",
                          json={"model": model_id, "messages": messages},
                          headers=_g4f_headers(), timeout=(15, timeout))
    except Exception as e:
        raise EMError(f"g4f: {str(e)[:60]}")
    if r.status_code != 200:
        if r.status_code in (402, 429):
            G4F_LIMIT["until"] = _t.time() + 900
        raise EMError(f"g4f: {r.status_code}")
    try:
        return (r.json()["choices"][0]["message"].get("content") or "").strip()
    except Exception:
        raise EMError("g4f: parse")

def gk_chat(messages, model_id="glm-4-flash", timeout=150):
    """چاتی gadegetkit — generate-signature ← ai-text/chat (سیستەم-پرۆمپت لە messages)"""
    import time as _t
    if _t.time() < GK_LIMIT["until"]:
        raise EMError("gk: cooldown")
    hist = _sys_keep([{"role": m.get("role", "user"), "content": m.get("content") or ""}
                        for m in messages if m.get("content")], 15)
    if not hist:
        raise EMError("gk: هیچ نامە")
    try:
        s = requests.Session()
        s.headers.update({"User-Agent": GK_UA, "Content-Type": "application/json",
                          "Origin": GK_BASE, "Referer": GK_BASE + "/ai-tools/chatbot"})
        s.get(GK_BASE + "/ai-tools/chatbot", timeout=(10, 25))
        ts = str(int(_t.time() * 1000))
        rs = s.post(GK_BASE + "/api/internal/generate-signature",
                    json={"timestamp": int(ts), "path": "/api/ai-text/chat"}, timeout=(10, 25))
        sig = (rs.json() or {}).get("signature")
        if not sig:
            raise EMError("gk: signature نییە")
        r = s.post(GK_BASE + "/api/ai-text/chat", json={"messages": hist, "locale": "en"},
                   headers={"x-timestamp": ts, "x-signature": sig}, timeout=(15, timeout))
    except EMError:
        raise
    except Exception as e:
        raise EMError(f"gk: {str(e)[:60]}")
    if r.status_code != 200:
        if r.status_code == 429:
            GK_LIMIT["until"] = _t.time() + 600
        raise EMError(f"gk: {r.status_code}")
    try:
        j = r.json()
    except Exception:
        raise EMError("gk: parse")
    ans = (j.get("text") or "").strip()
    if not ans or not j.get("success"):
        raise EMError("gk: وەڵام بەتاڵ")
    return ans

def gk_servers():
    out = []
    if "glm-4-flash" in MS.get("gk_ok", {}) or not MS.get("gk_ok"):
        out.append({"id": "gk-glm-4-flash", "name": "GLM 4 Flash (GK)", "model_id": "glm-4-flash", "kind": "gk"})
    return out

def hb_chat(messages, model_id="hotbot-chat", timeout=110):
    """چاتی hotbot — یەک مۆدێڵ؛ ٤ چات بە IP؛ #94U49: پرۆکسی لەسەر لیمێت/بەتاڵی"""
    import time as _t
    if _t.time() < HB_LIMIT["until"]:
        raise EMError("hb: cooldown")
    last = ""
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            last = m["content"]
            break
    if not last:
        raise EMError("hb: هیچ پرسیار")
    import uuid as _uuid
    hist = _sys_keep([{"role": m.get("role", "user"), "content": m.get("content") or ""}
                        for m in messages if m.get("content")], 11)
    _last = EMError("hb: شکست")
    for _px in _px_list(3):  # #94U49: دایرێکت + ٣ پرۆکسی
        cid = str(_uuid.uuid4())
        _kw = {"proxies": {"http": _px, "https": _px}} if _px else {}
        try:
            requests.get(HB_BASE + "/", headers={"User-Agent": HB_UA}, timeout=(10, 20), **_kw)
        except Exception:
            pass
        try:
            rm = requests.post(HB_BASE + "/api/moderate",
                               json={"text": last[-800:], "imageUrls": [], "chatId": cid, "requestType": "text"},
                               headers={"User-Agent": HB_UA, "Content-Type": "application/json",
                                        "Origin": HB_BASE, "Referer": HB_BASE + "/"}, timeout=(10, 20), **_kw)
            if rm.status_code == 200 and (rm.json() or {}).get("flagged"):
                raise EMError("hb: moderate بلۆک")
        except EMError:
            raise
        except Exception:
            pass
        try:
            r = requests.post(HB_BASE + "/api/chat",
                              json={"messages": hist, "model": "hotbot-chat", "chatId": cid,
                                    "effort": "light", "camp": False},
                              headers={"User-Agent": HB_UA, "Content-Type": "application/json",
                                       "Origin": HB_BASE, "Referer": HB_BASE + "/"},
                              timeout=(15, timeout), stream=True, **_kw)
        except Exception as e:
            _last = EMError(f"hb: {str(e)[:60]}")
            continue
        if r.status_code in (429, 403):
            _last = EMError("hb: 429")
            continue
        if r.status_code != 200:
            raise EMError(f"hb: {r.status_code}")
        try:
            raw = r.content
        except Exception:
            raw = b""
        t = raw.decode("utf-8", "replace")
        ans_parts = []
        for m2 in re.finditer(r'data: (\{\"content\":\".*?\"\})', t):
            try:
                ans_parts.append(json.loads(m2.group(1)).get("content", ""))
            except Exception:
                pass
        ans = "".join(ans_parts).strip()
        if not ans:
            _last = EMError("hb: بەتاڵ (کوانتا)")
            continue
        return ans
    HB_LIMIT["until"] = _t.time() + 300
    raise _last if "بەتاڵ" not in str(_last) else EMError("hb: بەتاڵ → دیلی ٥ خولەک (کوانتا)")

def hb_servers():
    out = []
    if "hotbot-chat" in MS.get("hb_ok", {}) or not MS.get("hb_ok"):
        out.append({"id": "hb-hotbot-chat", "name": "HotBot Chat", "model_id": "hotbot-chat", "kind": "hb"})
    return out

def hf_chat(messages, model_id="deepseek-ai/DeepSeek-V4.1-Flash", timeout=110):
    """چاتی HF Inference — OpenAI-ستایل؛ 402 = کرێتی مانگانە (دیلی تا یەکی مانگ)؛ 429 = ١٠ خولەک"""
    import time as _t
    if _t.time() < HF_LIMIT["until"]:
        raise EMError("hf: credit cooldown")
    body = {"model": model_id, "messages": _sys_keep(messages, 23), "max_tokens": 4000}  # #94U25 #94U29 LONG-OUT
    try:
        r = requests.post(HF_BASE + "/chat/completions", json=body,
                          headers=_hf_headers(), timeout=(15, timeout))
    except Exception as e:
        raise EMError(f"hf: {str(e)[:60]}")
    if r.status_code != 200:
        if r.status_code == 402:
            # کرێتی مانگانە تەواو — دیلی تا یەکی مانگی داهاتوو + پاککردنەوەی مینیو
            now = _t.time()
            nxt = (_t.gmtime(now).tm_year + (1 if _t.gmtime(now).tm_mon == 12 else 0),
                   1 if _t.gmtime(now).tm_mon == 12 else _t.gmtime(now).tm_mon + 1, 1)
            import calendar as _cal
            HF_LIMIT["until"] = _cal.timegm(nxt + (0, 0, 0)) + 300
            if MS.get("hf_ok"):
                MS["hf_ok"].clear()
                _ms_save()
                print("[HF] کرێتی تەواو — hf_ok پاککرایەوە تا ڕێککەوتنی مانگ", flush=True)
            raise EMError("hf: 402 → دیلی تا مانگی داهاتوو")
        if r.status_code == 429:
            HF_LIMIT["until"] = _t.time() + 600
            raise EMError("hf: 429 → دیلی ١٠ خولەک")
        # مردوو لە ترافیکی ڕاستەقینە (400/404/503) → لە hf_ok بۆ hf_bad (دووبارە ٢٤ کاتژمێر)
        if r.status_code in (400, 404, 503) and model_id in MS.get("hf_ok", {}):
            MS["hf_ok"].pop(model_id, None)
            MS.setdefault("hf_bad", {})[model_id] = {"code": r.status_code, "t": _t.time()}
            _ms_save()
            print(f"[HF] مردوو لە چات: {model_id} ({r.status_code}) — لابرا", flush=True)
        raise EMError(f"hf: {r.status_code}")
    try:
        m = r.json()["choices"][0]["message"]
    except Exception:
        raise EMError("hf: parse")
    return (m.get("content") or "").strip()

def hf_servers():
    labels = {}
    out = []
    for mid in list(MS.get("hf_ok", {}).keys())[:40]:
        tail = str(mid).split("/")[-1]
        label = re.sub(r'[-_]', ' ', tail).strip()
        slug = re.sub(r'[^a-z0-9.]+', '-', str(mid).lower()).strip('-').replace('/', '-')
        out.append({"id": f"hf-{slug}", "name": f"{label} (HF)",
                    "model_id": mid, "kind": "hf"})
    return out

def hk_chat(messages, model_id="deepseek/deepseek-v4-flash", timeout=120):
    """چاتی heck.ai — تک-شۆت (پرسیار + وەڵامی پێشوو)؛ 402 = کرێکی OpenRouter ەکەیان؛ #94U49: 429 → سێشن+پرۆکسی نوێ"""
    import time as _t
    if _t.time() < HK_LIMIT["until"]:
        raise EMError("hk: upstream credit cooldown")
    last, pq, pa = "", None, None
    for m in reversed(messages):
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if m.get("role") == "user":
            last = c
            break
        if pa is None:
            pa = c
        elif pq is None:
            pq = c
    if not last:
        raise EMError("hk: هیچ پرسیار")
    _sys = _sys_txt(messages)  # #94U25: system مەفەوتێنە — بیخە سەر پرسیار
    _q = (f"[Instructions: {_sys}]\n\n{last[-4000:]}" if _sys else last[-4000:])  # #94U26: system تەواو (14k) + کۆتایی پرسیار
    r = None
    for _i, _px in enumerate(_px_list(2)):  # #94U49: دایرێکت + ٢ پرۆکسی
        try:
            sid = _hk_session(force=(_i > 0))
        except Exception as e:
            if _i == 0:
                raise EMError(f"hk: {str(e)[:60]}")
            continue
        body = {"model": model_id, "question": _q, "language": "English",
                "sessionId": sid, "previousQuestion": pq, "previousAnswer": pa,
                "imgUrls": [], "superSmartMode": False}
        _kw = {"proxies": {"http": _px, "https": _px}} if _px else {}
        try:
            r = requests.post(HK_BASE + "/chat", json=body, headers=_hk_headers(),
                              timeout=(15, timeout), stream=True, **_kw)
        except Exception:
            r = None
            continue
        if r.status_code in (429, 403):
            r = None
            continue
        break
    if r is None:
        HK_LIMIT["until"] = _t.time() + 600
        raise EMError("hk: 429 → دیلی ١٠ خولەک")
    if r.status_code != 200:
        if r.status_code in (400, 500) and model_id in MS.get("hk_ok", {}):
            MS["hk_ok"].pop(model_id, None)
            MS.setdefault("hk_bad", {})[model_id] = {"code": r.status_code, "t": _t.time()}
            _ms_save()
        raise EMError(f"hk: {r.status_code}")
    out = []
    err = None
    paywall = False
    r.encoding = "utf-8"  # #110U2: latin-1 mojibake guard
    for line in r.text.splitlines():
        line = line.strip()
        if not line.startswith("data:"):
            continue
        tok = line[5:].strip()
        if not tok or tok == "[ERROR]":
            continue
        if tok.startswith("{"):
            try:
                j = json.loads(tok)
            except Exception:
                continue
            msg = str(j.get("message") or "")
            if j.get("error") or "error" in str(j.get("error", "")).lower():
                err = msg[:90]
                if "Payment Required" in msg or "402" in msg or "credits" in msg.lower():
                    paywall = True
                break
            for key in ("content", "text", "answer", "token", "delta"):
                v = j.get(key)
                if isinstance(v, str) and v:
                    out.append(v)
                    break
            continue
        out.append(tok)
    ans = "".join(out).strip()
    if paywall:
        HK_LIMIT["until"] = _hk_quota_ts()
        if MS.get("hk_ok"):
            MS["hk_ok"].clear()
            _ms_save()
            print("[HK] کرێکی سەرەوە بەتاڵ — hk_ok پاککرایەوە تا چاک بوو", flush=True)
        raise EMError("hk: 402 upstream → دیلی تا نیوەشەوی UTC")
    if not ans:
        raise EMError(f"hk: {err or 'وەڵام بەتاڵ'}")
    return ans

def hk_servers():
    labels = dict(HK_CATALOG)
    out = []
    for mid in list(MS.get("hk_ok", {}).keys())[:12]:
        label = labels.get(mid, mid.split("/")[-1])
        slug = re.sub(r'[^a-z0-9.]+', '-', str(mid).lower()).strip('-').replace('/', '-')
        out.append({"id": f"hk-{slug}", "name": f"{label} (Heck)",
                    "model_id": mid, "kind": "hk"})
    return out

def l7_chat(messages, model_id="mistral-Nemo-Instruct-2407", timeout=90):
    """چاتی llm7.io — میوان: ١٠ داواکاری/خولەک، ٦٠/کاتژمێر بێ کلیل؛ #94U49: پرۆکسی لەسەر لیمێت"""
    import time as _t
    if _t.time() < L7_LIMIT["until"]:
        raise EMError("l7: cooldown")
    body = {"model": model_id, "messages": messages, "max_tokens": 4000}  # #94U29 LONG-OUT
    r = None
    _last_e = None
    for _px in _px_list(3):  # #94U49: دایرێکت + ٣ پرۆکسی
        _kw = {"proxies": {"http": _px, "https": _px}} if _px else {}
        try:
            r = requests.post(L7_BASE + "/chat/completions", json=body,
                              headers={"User-Agent": _pick_ua(ACT_UAS),
                                       "Content-Type": "application/json",
                                       "Referer": "https://llm7.io"},
                              timeout=(15, timeout), **_kw)
        except Exception as e:
            _last_e, r = e, None
            continue
        if r.status_code in (429, 402, 403):
            continue  # IP خێو کراوە → IP ی داهاتوو
        break
    if r is None:
        raise EMError(f"l7: {str(_last_e)[:60]}")
    if r.status_code != 200:
        if r.status_code in (429, 402):
            L7_LIMIT["until"] = _t.time() + 600
        elif r.status_code in (400, 401, 404) and model_id in MS.get("l7_ok", {}):
            # مۆدێڵ لە ترافیکی ڕاستەقینەدا مردووە (نەک ڕێگری کاتی) — لە ok بۆ bad بیبە (٢٤ کاتژمێر دووبارە)
            MS["l7_ok"].pop(model_id, None)
            MS.setdefault("l7_bad", {})[model_id] = {"code": r.status_code, "t": _t.time()}
            _ms_save()
            print(f"[L7] مردوو لە چاتی ڕاستەقینە: {model_id} ({r.status_code}) — لە ok لابرا", flush=True)
        raise EMError(f"l7: {r.status_code}")
    try:
        m = r.json()["choices"][0]["message"]
    except Exception:
        raise EMError("l7: parse")
    return (m.get("content") or "").strip()

def l7_servers():
    ids = list(MS["l7_ok"].keys())
    if not ids:
        ids = [f for f, _ in L7_FALLBACK]
    labels = dict(L7_FALLBACK)
    out = []
    for mid in ids[:8]:
        label = labels.get(mid, (mid.split("-")[0].capitalize() if mid else "LLM7"))
        slug = re.sub(r'[^a-z0-9.]+', '-', mid.lower()).strip('-')
        out.append({"id": f"l7-{slug}", "name": f"{label} (LLM7)",
                    "model_id": mid, "kind": "l7"})
    return out

def mc_chat(messages, model_key="gemini-3.1-flash-lite", timeout=110, depth=0):
    """چاتی MultiChats — مێژوو لەناو پرۆمپت + ڕۆتەیشنی ئەکاونت + نوێکردنەوەی hih خۆکار"""
    if depth == 0 and not (MC_ST.get("accounts")):
        _mc_load()
    sys_txt = " ".join(str(m.get("content")) for m in messages if m.get("role") == "system")[:600]
    rest = [m for m in messages if m.get("role") != "system"]
    last = rest[-1] if rest else {"role": "user", "content": "سلام"}
    tr = "\n".join(("بەکارهێنەر: " if m.get("role") == "user" else "وەڵام: ") + str(m.get("content"))[:700]
                   for m in rest[:-1])[-3500:]
    umsg = str(last.get("content"))[:6000]
    if tr:
        umsg = f"[چاتی پێشوو]\n{tr}\n\n[پرسیاری نوێ]\n{umsg}"
    if sys_txt:
        umsg = f"[رێنمایی کەسایەتی: {sys_txt}]\n\n{umsg}"
    model = next((k for k, _n in MC_MODELS if norm_model(k) == norm_model(model_key)), model_key)
    tries = 0
    while tries < 5:
        acc = _mc_pick()
        if not acc:
            threading.Thread(target=_mc_signup_new, daemon=True).start()
            raise EMError("mc: حەوز بەتاڵە — چەند خولەکێکی تر حەوز پڕ دەبێتەوە")
        try:
            ans = _mc_call(acc, model, umsg, timeout)
            today = time.strftime("%Y-%m-%d", time.gmtime())
            if acc.get("day") != today:
                acc["day"], acc["n"] = today, 0
            acc["n"] = int(acc.get("n") or 0) + 1
            if int(acc.get("n") or 0) >= MC_ACC_DAY:
                acc["cool"] = time.time() + 3600  # کوانتای ڕۆژانە تەواو — تا بەیانی
            with MC_LOCK:
                _mc_save()
            return ans
        except _McHih:
            _mc_hih(force=True)  # تۆکنی کۆن/نەگونجاو — مینتەر لە دوایین فایلەوە یان خۆی
            tries += 1
            time.sleep(1)
        except _McAuth:
            if not _mc_refresh(acc):
                acc["dead"] = 1
                with MC_LOCK:
                    _mc_save()
            tries += 1
        except _McLimit as e:
            acc["cool"] = time.time() + MC_COOL_429
            with MC_LOCK:
                _mc_save()
            if len([a for a in _mc_alive()]) < max(3, MC_TARGET // 10):
                threading.Thread(target=_mc_signup_new, daemon=True).start()
            tries += 1
            time.sleep(1)
        except EMError:
            raise
        except Exception as e:
            tries += 1
            if tries >= 5:
                raise EMError(f"mc: {str(e)[:80]}")
            time.sleep(1)
    raise EMError("mc: هەموو هەوڵەکان شکانیان خوارد")

def mc_servers():
    out = []
    for slug, nm in MC_MODELS:
        out.append({"id": f"mc-{slug}", "name": f"{nm} (MultiChats)", "model_id": slug, "kind": "mc"})
    return out

def ng_chat(messages, timeout=110):
    """چاتی notegpt — مێژوو بۆ یەک نامە؛ template ی homework یش لابردن؛ #94U49: پرۆکسی لەسەر لیمێت"""
    import time as _t
    if _t.time() < NG_LIMIT["until"]:
        raise EMError("ng: cooldown")
    sys_txt = " ".join(m["content"] for m in messages if m.get("role") == "system")[:32000]
    user_txt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_txt = m["content"]
            break
    if not user_txt:
        user_txt = " ".join(m.get("content", "") for m in messages)[-2000:]
    if sys_txt:
        user_txt = f"[ئاراستەی سیستەم: {sys_txt}]\n\n{user_txt}"
    _last = EMError("ng: شکست")
    for _px in _px_list(3):  # #94U49: دایرێکت + ٣ پرۆکسی
        _kw = {"proxies": {"http": _px, "https": _px}} if _px else {}
        try:
            r = requests.post("https://notegpt.io/api/v2/homework/stream",
                              json={"message": user_txt, "language": "auto", "model": "gemini-3.1-flash-lite",
                                    "tone": "default", "length": "moderate",
                                    "conversation_id": str(__import__("uuid").uuid4())},
                              headers={"User-Agent": _pick_ua(ACT_UAS),
                                       "Origin": "https://notegpt.io",
                                       "Referer": "https://notegpt.io/ai-answer-generator"},
                              timeout=(15, timeout), stream=True, **_kw)
        except Exception as e:
            _last = EMError(f"ng: {str(e)[:60]}")
            continue
        if r.status_code in (429, 403):
            _last = EMError("ng: 429")
            continue
        if r.status_code != 200:
            raise EMError(f"ng: {r.status_code}")
        text = []
        limit_hit = False
        r.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
        for line in r.iter_lines(decode_unicode=True):
            if not line or not line.startswith("data: "):
                continue
            try:
                d = json.loads(line[6:])
            except Exception:
                continue
            if isinstance(d.get("text"), str):
                text.append(d["text"])
            if d.get("code") == 164016:
                limit_hit = True
        ans = "".join(text).strip()
        if limit_hit and not ans:
            _last = EMError("ng: لیمیت ڕۆژانە")
            continue
        # template ی homework پاک بکەوە
        ans = re.sub(r"^###\s*Question\s*\d*\s*", "", ans)
        ans = re.sub(r"\n?###\s*(Answer|Solution Steps|[^\n]*)\s*", "\n", ans)
        ans = ans.strip()
        if ans:
            return ans
        _last = EMError("ng: وەڵام نەگەڕایەوە")
    if "429" in str(_last) or "لیمیت" in str(_last):
        NG_LIMIT["until"] = _t.time() + 1800
    raise _last

def ng_servers():
    return [{"id": "ng-gemini-flash-lite", "name": "Gemini 3.1 Flash Lite (NoteGPT)",
             "model_id": "gemini-3.1-flash-lite", "kind": "ng"}]

def pi_chat(messages, model_id="pi-chat", timeout=50):  # #94U19: 110→50 (stream-hang)
    """چاتی Pi — مێژوو فلێت دەکرێت بۆ یەک دەق؛ SSE partial → یەک وەڵام؛ #94U49: 429 → سێشن+پرۆکسی نوێ"""
    import time as _t, uuid as _u, json as _j
    if _t.time() < PI_LIMIT["until"]:
        raise EMError("pi: cooldown")
    lines = []
    for m in _sys_keep(messages, 11):
        role = m.get("role")
        c = (m.get("content") or "").strip()
        if not c:
            continue
        if role == "system":
            lines.append("[Instructions] " + c)
        elif role == "user":
            lines.append("[User] " + c)
        else:
            lines.append("[Assistant] " + c)
    if not lines:
        raise EMError("pi: هیچ نامە")
    lines.append("[Assistant]")
    text = _flat_cut(lines)
    import re as _re
    text = _re.sub(r"\[User\]\s*\[Assistant\]", "", text)
    last = ""
    _px2 = None
    for attempt in (1, 2):
        try:
            s = PI_STATE.get("s")
            did = PI_STATE.get("did")
            if s is None:
                s, did = _pi_session()
            _kw = {"proxies": {"http": _px2, "https": _px2}} if _px2 else {}
            r = s.post(PI_BASE + "/api/v2/chat",
                       json={"text": text, "conversation": "",
                             "eqDistinctId": did, "eqSessionId": str(_u.uuid4()),
                             "clientId": str(_u.uuid4())},
                       headers=_pi_headers(), timeout=(15, timeout), stream=True, **_kw)
            if r.status_code in (401, 403, 429) and attempt == 1:
                PI_STATE["s"] = None
                if r.status_code == 429:  # #94U49: دیلی مەکە — سێشنی نوێ + پرۆکسی
                    try:
                        _p = _proxy_get(1) or []
                        _px2 = _p[0] if _p else None
                    except Exception:
                        _px2 = None
                continue
            if r.status_code == 429:
                PI_LIMIT["until"] = _t.time() + 300
                raise EMError("pi: 429")
            if r.status_code != 200:
                raise EMError(f"pi: {r.status_code}")
            parts = []
            buf = ""
            _dl = _t.time() + min(timeout, 60)
            for ch in r.iter_content(chunk_size=None):
                if _t.time() > _dl:
                    break  # #94U19: دێدلاینی stream — نەهێشتنی گیربوون
                buf += ch.decode("utf-8", "replace")
                while "\n" in buf:
                    ln, buf = buf.split("\n", 1)
                    ln = ln.strip()
                    if ln.startswith("data:"):
                        try:
                            d = _j.loads(ln[5:].strip())
                            t2 = d.get("text")
                            if isinstance(t2, str):
                                parts.append(t2)
                        except Exception:
                            pass
            last = "".join(parts).strip()
            if last:
                return last
            # بەتاڵ — ئەگەر trial تەواو بووە، نشستی نوێ
            PI_STATE["s"] = None
            continue
        except EMError:
            raise
        except Exception as e:
            PI_STATE["s"] = None
            if attempt == 2:
                raise EMError(f"pi: {str(e)[:60]}")
    if last:
        return last
    raise EMError("pi: وەڵام بەتاڵ")

def pi_servers():
    out = []
    if "pi-chat" in MS.get("pi_ok", {}) or not MS.get("pi_ok"):
        out.append({"id": "pi-pi-chat", "name": "Pi (pi.ai)", "model_id": "pi-chat", "kind": "pi"})
    return out

def pia_chat(messages, agent_id, timeout=110, depth=0):
    """چاتی piax — SSE (openrouter-chunks)؛ sys دەفڕێتە ناو پرۆمپت؛ ئەکاونت-ڕۆتەیشن + لیمیت"""
    with PIA_LOCK:
        acc = _pia_pick(agent_id)
    if not acc:
        raise EMError("piax: هیچ ئەکاونتێکی بەردەست نییە")
    sys_txt = " ".join(m["content"] for m in messages if m.get("role") == "system")[:32000]
    rest = [m for m in messages if m.get("role") != "system"][-8:]
    q = ""
    for m in rest[:-1]:
        who = "بەکارهێنەر" if m.get("role") == "user" else "وەڵام"
        q += f"{who}: {str(m.get('content'))[:600]}\n"
    last = rest[-1] if rest else {"role": "user", "content": "سلام"}
    if sys_txt:
        q = f"[ئاراستەی سیستەم: {sys_txt}]\n{q}"
    q += f"بەکارهێنەر: {last.get('content')}"
    try:
        r = requests.post(PIA_API + "/ai-api/ai/agent/chatStream",
                          json={"device": {"deviceType": "pc", "osPlatform": "web"},
                                "agentId": str(agent_id), "query": q[:8000],
                                "conversationId": "", "parentMessageId": "", "files": []},
                          headers={"Accept-Language": "en", "User-Agent": _PIA_UA,
                                   "Authorization": acc.get("token") or "",
                                   "Content-Type": "application/json",
                                   "Origin": "https://www.piax.org",
                                   "Referer": "https://www.piax.org/chat"},
                          timeout=(12, timeout), stream=True)
        if r.status_code == 401:
            _pia_mark(acc, agent_id, "auth")
            raise EMError("piax: توکن مردووە")
        parts = []
        for raw in r.iter_lines(chunk_size=None):
            if not raw:
                continue
            ln = raw.decode("utf-8", "ignore").strip() if isinstance(raw, bytes) else str(raw).strip()
            if not ln.startswith("data:"):
                continue
            payload = ln[5:].strip()
            if payload == "[DONE]":
                break
            try:
                d = json.loads(payload)
            except Exception:
                continue
            if d.get("event") == "error":
                msg = str(d.get("answer") or d.get("message") or "error")[:90]
                if any(x in msg.lower() for x in ("subscription", "upgrade", "quota", "limit", "frequent", "credit")):
                    raise _PiaLimit(msg)
                raise EMError(f"piax: {msg}")
            ch = (d.get("choices") or [{}])[0]
            delta = (ch.get("delta") or {}).get("content") or ch.get("text") or ""
            if delta:
                parts.append(delta)
        ans = "".join(parts).strip()
        if not ans:
            raise EMError("piax: وەڵام بەتاڵ")
        return ans
    except _PiaLimit as e:
        _pia_mark(acc, agent_id, str(e))
        raise EMError(f"piax: {e}")
    except EMError:
        raise
    except Exception as e:
        s = str(e)
        if any(x in s.lower() for x in ("limit", "quota", "frequent", "subscription")) and depth == 0:
            _pia_mark(acc, agent_id, s)
            raise EMError(f"piax: {s[:80]}")
        raise EMError(f"piax: {s[:80]}")

def pia_servers():
    out = []
    for aid, model, nm in PIA_AGENTS:
        out.append({"id": f"pia-{model}", "name": f"{nm} (Piax)",
                    "model_id": aid, "kind": "pia"})
    return out

def qb_chat(messages, timeout=60):  # #94U19: 110→60
    """چاتی quillbot — مێژووی وەک یەک نامەی یەکگیراو؛ NDJSON: type=content/usage"""
    import uuid as _uuid
    # مێژوو بۆ یەک پرسیار کۆبکەوە (سیستەم لە سەرەتا + دوا نامەی بەکارهێنەر)
    sys_txt = " ".join(m["content"] for m in messages if m.get("role") == "system")[:32000]
    user_txt = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_txt = m["content"]
            break
    if not user_txt:
        user_txt = " ".join(m.get("content", "") for m in messages)[-2000:]
    if sys_txt:
        user_txt = f"[ئاراستەی سیستەم: {sys_txt}]\n\n{user_txt}"
    body = {"message": {"content": user_txt, "files": []}, "context": {}, "tools": {},
            "origin": {"name": "ai-chat.chat", "url": "https://quillbot.com"}}
    try:
        r = requests.post(QB_URL + str(_uuid.uuid4()), json=body, timeout=(15, timeout),
                          headers={"User-Agent": _pick_ua(ACT_UAS),
                                   "Origin": "https://quillbot.com",
                                   "Referer": "https://quillbot.com/ai-chat",
                                   "Accept": "text/event-stream",
                                   "platform-type": "webapp"}, stream=True)
    except Exception as e:
        raise EMError(f"qb: {str(e)[:60]}")
    if r.status_code == 403:
        # #94U19 REVIVE: CF چەلەنج → دووبارە بە پرۆکسی (تا ٣)
        try:
            r.close()
        except Exception:
            pass
        for _px in _proxy_get(3):
            try:
                _r2 = requests.post(QB_URL + str(_uuid.uuid4()), json=body, timeout=(15, 60),
                                    headers={"User-Agent": _pick_ua(ACT_UAS),
                                             "Origin": "https://quillbot.com",
                                             "Referer": "https://quillbot.com/ai-chat",
                                             "Accept": "text/event-stream",
                                             "platform-type": "webapp"},
                                    proxies={"http": _px, "https": _px}, stream=True)
                if _r2.status_code == 200:
                    r = _r2
                    print("[QB] ✅ بە پرۆکسی تێپەڕی", flush=True)
                    break
            except Exception:
                continue
    if r.status_code == 403:
        raise EMError("qb: چەلەنجەی Cloudflare (ڕێژە)")
    if r.status_code != 200:
        raise EMError(f"qb: {r.status_code}")
    text = []
    r.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        try:
            d = json.loads(line)
        except Exception:
            continue
        if d.get("type") == "content":
            c = d.get("content", "")
            if c:
                text.append(c)
        elif d.get("type") == "error":
            raise EMError(f"qb: {str(d.get('message', 'error'))[:60]}")
    ans = "".join(text).strip()
    ans = re.sub(r"</?editor-content[^>]*>", "", ans).strip()
    if ans:
        return ans
    raise EMError("qb: وەڵام نەگەڕایەوە")

def qb_servers():
    return [{"id": "qb-gpt-4.1-mini", "name": "GPT 4.1 Mini (QuillBot)",
             "model_id": "gpt-4.1-mini", "kind": "qb"}]

def yl_chat(messages, model_id="yollo-chat", timeout=120):
    """چاتی yollo.ai — مێژوو لە کلایەنتەوە (سیستەم-پرۆمپتی خۆمان) — دەق بێ لیمیت"""
    import time as _t
    if not messages:
        raise EMError("yl: هیچ نامە")
    last = ""
    for m in reversed(messages):
        if m.get("role") == "user" and m.get("content"):
            last = m["content"]
            break
    if not last:
        last = messages[-1].get("content") or ""
    hist = [{"role": m.get("role", "user"), "content": m.get("content") or ""}
            for m in messages if m.get("content")]
    if hist and hist[-1]["role"] == "user" and hist[-1]["content"] == last:
        hist = hist[:-1]
    lasterr = None
    for attempt in range(2):
        try:
            _yl_identity(force=(attempt == 1))
        except Exception as e:
            lasterr = e
            continue
        _sys = _sys_txt(messages)  # #94U25b
        _q = f"[Instructions: {_sys}]\n\n{last}" if _sys else last
        body = {"message": _q, "sessionId": _YL["sid"], "conversationHistory": _sys_keep(hist, 20),
                "userToken": _YL["tok"], "userLocale": "en", "isRegenerate": False,
                "isSafeMode": False, "generateType": 0}
        try:
            r = requests.post(YL_BASE + "/chat-stream", json=body,
                              headers=_yl_headers(_YL["finger"]), timeout=(15, timeout), stream=True)
        except Exception as e:
            lasterr = EMError(f"yl: {str(e)[:60]}")
            continue
        if r.status_code != 200:
            lasterr = EMError(f"yl: {r.status_code}")
            _YL["tok"] = ""
            continue
        out = []
        bad = None
        r.encoding = "utf-8"  # #110U2: latin-1 mojibake guard
        for line in r.text.splitlines():
            line = line.strip()
            if not line.startswith("data:"):
                continue
            p = line[5:].strip()
            if not p:
                continue
            try:
                j = json.loads(p)
            except Exception:
                continue
            ty = j.get("type")
            if ty == "content":
                out.append(j.get("content") or "")
            elif ty == "end":
                break
            elif ty in ("error", "errorMsg") or j.get("error") or "error" in str(ty or "").lower():
                bad = str(j.get("message") or j)[:80]
                break
        ans = "".join(out).strip()
        if ans:
            return ans
        lasterr = EMError(f"yl: {bad or 'وەڵام بەتاڵ'}")
        _YL["sid"] = ""
    raise lasterr or EMError("yl: شکست")

def yl_servers():
    out = []
    for mid in list(MS.get("yl_ok", {}).keys())[:3] or ["yollo-chat"]:
        out.append({"id": "yl-yollo-chat", "name": "Yollo Chat",
                    "model_id": mid, "kind": "yl"})
    return out

def z02_chat(messages, model_id="gemini-2.5-flash-lite", timeout=110):
    """چاتی zerotwo — ٤ مۆدێڵی ڕاییگە؛ ١٥ نامە/ڕۆژ → هەژماری نوێ خۆکار"""
    provider = _Z02_PROVIDERS.get(model_id, "gemini")
    try:
        token = _z02_token()
    except EMError:
        raise
    except Exception as e:
        raise EMError(f"z02: {str(e)[:60]}")
    h = {
        "User-Agent": _pick_ua(ACT_UAS),
        "Origin": "https://app.zerotwo.ai", "Referer": "https://app.zerotwo.ai/",
        "X-ZeroTwo-Platform": "web", "Content-Type": "application/json",
    }
    msgs = _sys_keep([{"role": m["role"], "content": m["content"]}
                        for m in messages if m.get("role") in ("user", "assistant", "system")], 19)
    for attempt in (0, 1):
        if attempt == 1:
            try:
                token = _z02_new_account()
                _Z02_CACHE["token"], _Z02_CACHE["exp"] = token, time.time() + 3300
            except Exception as e:
                raise EMError(f"z02 هەژمار: {str(e)[:50]}")
        try:
            s = requests.Session()
            s.headers.update(h)
            r = s.get(Z02_API + "/api/auth/csrf-token", timeout=(15, 30))
            tok = r.json()["token"]
            r = s.post(Z02_API + "/api/ai/chat/stream",
                       headers={**h, "X-CSRF-Token": tok, "Authorization": f"Bearer {token}"},
                       json={"messages": msgs, "provider": provider, "model": model_id},
                       timeout=(15, timeout))
        except Exception as e:
            if attempt == 0:
                continue
            raise EMError(f"z02: {str(e)[:60]}")
        text, err = [], ""
        for line in r.content.decode("utf-8", "replace").splitlines():
            if not line.startswith("data: "):
                continue
            try:
                d = json.loads(line[6:])
            except Exception:
                continue
            if d.get("entity") == "message.content" and d.get("status") == "delta":
                t = (d.get("v", {}).get("delta") or {}).get("text")
                if t:
                    text.append(t)
            if d.get("status") == "error":
                v = d.get("v", {})
                err = v.get("code") or v.get("message") or "error"
        ans = "".join(text).strip()
        if ans:
            return ans
        if "LIMIT" in err.upper() or "429" in str(err):
            if attempt == 0:
                continue  # هەژماری نوێ
            raise EMError("z02: کواتی ڕۆژانە تەواو")
        if attempt == 0:
            continue
        raise EMError(f"z02: {str(err)[:60] or 'وەڵام نەگەڕایەوە'}")
    raise EMError("z02: وەڵام نەگەڕایەوە")

def z02_servers():
    return [
        {"id": "z02-gemini-flash-lite", "name": "Gemini Flash Lite (ZeroTwo)",
         "model_id": "gemini-2.5-flash-lite", "kind": "z02"},
        {"id": "z02-grok-4.1-fast", "name": "Grok 4.1 Fast (ZeroTwo)",
         "model_id": "grok-4-1-fast-non-reasoning", "kind": "z02"},
        {"id": "z02-gpt-5.6-luna", "name": "GPT 5.6 Luna (ZeroTwo)",
         "model_id": "gpt-5.6-luna", "kind": "z02"},
        {"id": "z02-venice-roleplay", "name": "Venice Roleplay (ZeroTwo)",
         "model_id": "venice-uncensored-role-play", "kind": "z02"},
    ]

class _CxLimit(Exception):
    pass

class _McAuth(Exception):
    pass

class _McHih(Exception):
    pass

class _McLimit(Exception):
    pass

class _PiaLimit(Exception):
    pass

def _act_identity():
    """ناسنامەی نوێ — visitorId نوێ = RSA encrypt
    → (visitorId, vTokenی خاو base64, کوکی percent-encoded)"""
    import urllib.parse as _up
    visitor_id = hashlib.md5(f"fp{time.time()}{random.random()}".encode()).hexdigest()
    from cryptography.hazmat.primitives import serialization as _s, asymmetric as _a
    try:
        pub = _s.load_pem_public_key(ACT_PUBKEY.encode())
        enc = pub.encrypt(visitor_id.encode(), _a.padding.PKCS1v15())
        raw = base64.b64encode(enc).decode()
    except Exception:
        raw = visitor_id
    return visitor_id, raw, _up.quote(raw, safe="")

def _aiml_ensure_key():
    tok = _aiml_login()
    H = {"Authorization": f"Bearer {tok}", "User-Agent": "Mozilla/5.0"}
    if AIML_ST.get("key"):
        return AIML_ST["key"]
    # کیلی هەیە؟
    r = requests.get("https://app.aimlapi.com/v1/keys", headers=H, timeout=(15, 30))
    items = (r.json() or {}).get("items") or []
    if not items:
        r2 = requests.post("https://app.aimlapi.com/v1/keys", headers=H, json={"name": "ta3afi"}, timeout=(15, 30))
        if r2.status_code not in (200, 201):
            raise EMError(f"aiml-key {r2.status_code}")
        items = [r2.json()]
    # تەنها لە کاتی دروستکردندا key تەواو دەدرێت — ئەگەر کۆنەکە نەمانەوە، دووبارە دروست بکە
    full = (items[0] or {}).get("key")
    if not full:
        r3 = requests.post("https://app.aimlapi.com/v1/keys", headers=H, json={"name": "ta3afi"}, timeout=(15, 30))
        if r3.status_code not in (200, 201):
            raise EMError(f"aiml-key {r3.status_code}")
        full = (r3.json() or {}).get("key")
    if not full:
        raise EMError("aiml: هیچ کلیل")
    AIML_ST["key"] = full
    _aiml_save()
    return full

def _aiml_login():
    import time as _t, uuid as _u
    if AIML_ST.get("tok") and _t.time() - AIML_ST.get("tok_t", 0) < 30000:
        return AIML_ST["tok"]
    try:
        r = requests.put("https://auth.aimlapi.com/v1/auth/account",
                         json={"email": AIML_ST["email"], "password": AIML_ST["password"]},
                         headers={"aim-device-id": str(_u.uuid4()), "User-Agent": "Mozilla/5.0",
                                  "Origin": "https://aimlapi.com", "Referer": "https://aimlapi.com/"},
                         timeout=(15, 30))
        if r.status_code != 200:
            raise EMError(f"aiml-login {r.status_code}")
        AIML_ST["tok"] = r.json().get("token")
        AIML_ST["tok_t"] = _t.time()
        return AIML_ST["tok"]
    except EMError:
        raise
    except Exception as e:
        raise EMError(f"aiml: {str(e)[:60]}")

def _aka_session(force=False, px=None):
    """session_token: GET / → GET /api/auth/session → POST refresh (فلۆوی براوزەر)؛ #94U49: px"""
    import time as _t
    if not force and not px and _AKA["ses"] and _t.time() - _AKA["t"] < 43200:
        return _AKA["ses"]
    s = requests.Session()
    s.headers.update(_aka_headers())
    if px:
        s.proxies.update({"http": px, "https": px})
    try:
        s.get(AKA_BASE + "/", timeout=(10, 20))
        r = s.get(AKA_BASE + "/api/auth/session", timeout=(10, 20))
        if r.status_code != 200:
            raise EMError(f"aka: session {r.status_code}")
        s.post(AKA_BASE + "/api/auth/session/refresh/", json={}, timeout=(10, 20))
    except EMError:
        raise
    except Exception as e:
        raise EMError(f"aka: {str(e)[:60]}")
    if not px:
        _AKA["ses"] = s
        _AKA["t"] = _t.time()
    return s

def _cbc_gen_nonce():
    import uuid
    return str(uuid.uuid4())

def _cbc_headers():
    csrf, cookies = _cbc_session()
    return {
        "User-Agent": UA, "X-Requested-With": "XMLHttpRequest", "X-CSRF-TOKEN": csrf,
        "Referer": CBC_BASE + "/", "Origin": CBC_BASE, "Cookie": cookies,
    }

def _cbc_md5(s):
    import hashlib
    return hashlib.md5(s.encode("utf-8")).hexdigest()

def _cbc_stream_read(r, hdrs, payload, timeout, messages):
    """#91CB: خوێندنەوەی ستریم — دەقی تەواو"""
    out = ""
    r.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
    for line in r.iter_lines(decode_unicode=True):
        if not line:
            continue
        body = line[6:] if line.startswith("data: ") else (line[3:] if line.startswith("id: ") else None)
        if not body:
            continue
        try:
            j = json.loads(body)
        except Exception:
            continue
        if j.get("code"):
            raise EMError("cbc: " + str(j.get("code")))
        for ch in j.get("choices") or []:
            for part in ((ch.get("content") or {}).get("parts")) or []:
                t = part.get("text") or ""
                out += t
    if not out:
        raise EMError("cbc: وەڵامی بەتاڵ")
    return out

def _cbc_timestamp(hdrs):
    r = requests.post(CBC_BASE + "/api/get-timestamp",
                      headers={**hdrs, "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8"},
                      data={"href": CBC_BASE + "/"}, timeout=25)
    return r.json()["timestamp"]

def _cbox_new_account():
    """١ داواکاری — ئەکاونتی نوێی ads-کەناڵ (بێ ئیمێڵ، بێ OTP، بێ playwright)"""
    try:
        fp = str(uuid.uuid4())
        r = requests.post(CBOX_API + "/auth/fingerprint", json={},
                          headers={"User-Agent": _CBOX_UA, "Accept": "application/json",
                                   "Origin": "https://chat-box.ai", "Referer": "https://chat-box.ai/app/en",
                                   "X-Device-Fingerprint": fp, "x-device-fingerprint": fp,
                                   "x-user-origin-source": "ads", "Content-Type": "application/json"},
                          timeout=(12, 40))
        if r.status_code not in (200, 201):
            print(f"[CX] fingerprint fail: {r.status_code}", flush=True)
            return None
        d = r.json() or {}
        at, rt = d.get("accessToken"), d.get("refreshToken")
        if not at:
            return None
        today = time.strftime("%Y-%m-%d", time.gmtime())
        acc = {"fp": fp, "at": at, "rt": rt, "day": today, "n": 0, "dead": 0}
        with CBOX_LOCK:
            CBOX_ST.setdefault("accounts", []).append(acc)
            _ca_all = CBOX_ST.get("accounts") or []
            if len(_ca_all) > 1000:  # #94U44: 120؛ #94U47: →1000 (زیندوو 900 + مردوو 100)
                _ca_live = [a for a in _ca_all if not a.get("dead")][-900:]
                _ca_dead = [a for a in _ca_all if a.get("dead")][-100:]
                CBOX_ST["accounts"] = _ca_live + _ca_dead
            sg = CBOX_ST.get("signups") or {"date": "", "n": 0}
            if sg.get("date") != today:
                sg = {"date": today, "n": 0}
            sg["n"] = sg.get("n", 0) + 1
            CBOX_ST["signups"] = sg
            _cbox_save()
        return acc
    except Exception as e:
        print(f"[CX] new-acct: {str(e)[:80]}", flush=True)
        return None

def _cbox_pick():
    accs = _cbox_alive()
    if not accs:
        acc = _cbox_new_account()
        return acc
    n = len(accs)
    for i in range(n):
        a = accs[(CBOX_ST.get("idx", 0) + i) % n]
        CBOX_ST["idx"] = (CBOX_ST.get("idx", 0) + i + 1) % n
        return a
    return accs[0]

def _cbox_refresh(acc):
    """توکنی نوێ بە refreshToken — ئەگەر شکست → ئەکاونت مردوو"""
    try:
        r = requests.post(CBOX_API + "/auth/refresh", json={"refreshToken": acc.get("rt") or ""},
                          headers={"User-Agent": _CBOX_UA, "Accept": "application/json",
                                   "Origin": "https://chat-box.ai", "Referer": "https://chat-box.ai/app/en",
                                   "X-Device-Fingerprint": acc.get("fp") or "", "Content-Type": "application/json"},
                          timeout=(12, 40))
        if r.status_code in (200, 201):
            d = r.json() or {}
            if d.get("accessToken"):
                acc["at"] = d["accessToken"]
                if d.get("refreshToken"):
                    acc["rt"] = d["refreshToken"]
                acc["dead"] = 0
                with CBOX_LOCK:
                    _cbox_save()
                return True
    except Exception:
        pass
    acc["dead"] = 1
    return False

def _cbox_save():
    _json_save(CBOX_ACC_FILE, {"accounts": CBOX_ST.get("accounts") or [],
                               "idx": CBOX_ST.get("idx") or 0,
                               "signups": CBOX_ST.get("signups") or {"date": "", "n": 0}})

def _ct_identity():
    """ناسنامەی میوانی نوێ: visitorId = md5-ڕاندۆم → vtoken + mo_uuid"""
    import hashlib as _hl
    from urllib.parse import quote as _q
    vid = _hl.md5(("ct" + str(time.time_ns()) + str(random.random())).encode()).hexdigest()
    vt = _ct_vtoken(vid)
    mo = _hl.md5(("mo" + vid).encode()).hexdigest()
    hd = {"accept": "text/event-stream,application/json, text/event-stream",
          "content-type": "application/json", "lang": "en", "source": "web",
          "referer": "https://www.chattide.ai/", "origin": "https://www.chattide.ai",
          "sec-ch-ua": '"Not_A Brand";v="8", "Chromium";v="153", "HeadlessChrome";v="153"',
          "sec-ch-ua-mobile": "?0", "sec-ch-ua-platform": '"Windows"',
          "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-site",
          "user-agent": CT_UA, "vtoken": vt}
    ck = {"NEXT_LOCALE": "en", "mo_uuid": mo, "chatTide.visitor.id": _q(vt, safe="")}
    return hd, ck

def _ct_label(mid):
    out = []
    for p in str(mid).split("-"):
        out.append(p if p and p[0].isdigit() else p.capitalize())
    return " ".join(out)

def _ct_quota_ts():
    """نیوەشەوی UTC ی داهاتوو + ٥ خولەک — کاتی نوێبوونەوەی کوانتای ڕۆژانە"""
    return (int(time.time()) // 86400 + 1) * 86400 + 300

def _duck_attempt(model_id, msgs, timeout, px=None):  # #94U49: px
    import json as _j, random as _r, uuid as _u
    s = _duck_session()
    _duck_warm(px)
    _kw = {"proxies": {"http": px, "https": px}} if px else {}
    r = s.get("https://duck.ai/duckchat/v1/status", headers={
        "x-vqd-accept": "1", "Cache-Control": "no-store", "Accept": "*/*"},
        timeout=(15, 25), **_kw)
    if r.status_code != 200:
        raise EMError(f"duck: status {r.status_code}")
    ch = r.headers.get("x-vqd-hash-1")
    if not ch:
        raise EMError("duck: چەلەنجە نەگەڕایەوە")
    h1 = _duck_solve(ch)
    m = [{"role": x.get("role"), "content": [{"type": "text", "text": x.get("content", "")}]}
         for x in msgs]
    payload = {
        "model": model_id,
        "metadata": {"toolChoice": {"NewsSearch": False, "VideosSearch": False,
                                    "LocalSearch": False, "WeatherForecast": False}},
        "messages": m,
        "canUseTools": False,
        "reasoningEffort": "none",
        "canUseApproxLocation": None,
        "canDelegateImageGeneration": None,
        "canShowGreeting": False,
        "durableStream": {"messageId": str(_u.uuid4()), "conversationId": str(_u.uuid4()),
                          "publicKey": _duck_jwk()},
    }
    hdrs = {"Content-Type": "application/json", "Accept": "text/event-stream",
            "x-vqd-hash-1": h1, "x-fe-signals": _duck_signals(),
            "x-fe-version": DUCK_FE_VERSION, "x-ddg-journey-id": _u.uuid4().hex}
    r2 = s.post("https://duck.ai/duckchat/v1/chat", data=_j.dumps(payload),
                headers=hdrs, timeout=(15, timeout), **_kw)
    if r2.status_code != 200:
        raise EMError(f"duck: {r2.status_code}")
    text = []
    r2.encoding = "utf-8"  # #110U: SSE latin-1 mojibake guard
    for line in r2.iter_lines(decode_unicode=True):
        if not line or not line.startswith("data: "):
            continue
        d = line[6:].strip()
        if d == "[DONE]":
            break
        try:
            j = _j.loads(d)
        except Exception:
            continue
        if j.get("action") == "success" and isinstance(j.get("message"), str):
            text.append(j["message"])
        elif j.get("action") == "error":
            raise EMError(f"duck: {str(j.get('type', 'error'))[:50]}")
    ans = "".join(text).strip()
    if not ans:
        raise EMError("duck: وەڵام نەگەڕایەوە")
    return ans

def _g4f_bake_one(uuid, difficulty):
    nonce, hx = _cake_pow(uuid, "0", difficulty)
    if not nonce:
        return 0
    try:
        rb = requests.post(G4F_BASE + "/cake/bake", headers=_g4f_headers(),
                           json={"uuid": uuid, "salt": "0", "nonce": nonce, "hash": hx},
                           timeout=(10, 20))
        if rb.status_code == 200:
            j = rb.json() or {}
            return int(j.get("total_credit_cents") or j.get("credit_cents") or 0)
    except Exception:
        pass
    return 0

def _g4f_status():
    r = requests.get(G4F_BASE + "/cake/status", headers=_g4f_headers(), timeout=(10, 15))
    return r.json() if r.status_code == 200 else {}

def _hf_headers(ct=True):
    hd = {"Authorization": f"Bearer {HF_TOKEN}", "User-Agent": "Mozilla/5.0"}
    if ct:
        hd["Content-Type"] = "application/json"
    return hd

def _hk_headers():
    return {"User-Agent": HK_UA, "Content-Type": "application/json",
            "Origin": "https://heck.ai", "Referer": "https://heck.ai/", "authorization": ""}

def _hk_quota_ts():
    import time as _t
    return (int(_t.time()) // 86400 + 1) * 86400 + 300

def _hk_session(force=False):
    import time as _t
    if not force and _HK["sid"] and _t.time() - _HK["t"] < 3600:
        return _HK["sid"]
    r = requests.post(HK_BASE + "/session/create", json={"title": "chat"},
                      headers=_hk_headers(), timeout=(10, 20))
    sid = (r.json() or {}).get("id")
    if not sid:
        raise EMError(f"hk: session {str(r.text)[:60]}")
    _HK.update(sid=sid, t=_t.time())
    return sid

def _mc_alive():
    today = time.strftime("%Y-%m-%d", time.gmtime())
    out = []
    for a in (MC_ST.get("accounts") or []):
        if a.get("dead"):
            continue
        if a.get("day") != today:
            a["day"], a["n"] = today, 0  # کوانتا ڕۆژانە نوێ دەبێتەوە
        if int(a.get("n") or 0) >= MC_ACC_DAY:
            continue
        out.append(a)
    return out

def _mc_call(acc, model, umsg, timeout):
    """یەک داواکاری چات — کەمترین هێدەر: auth+ct+x-is-human؛ SSE ی ai-sdk v5"""
    tok = _mc_token(acc)
    if not tok:
        raise _McAuth("no-token")
    hih = _mc_hih()
    if not hih:
        raise _McHih("no-hih")
    body = {"operation": "new", "threadId": str(uuid.uuid4()),
            "newUserMessage": {"id": str(uuid.uuid4()),
                               "parts": [{"type": "text", "text": umsg}], "attachments": []},
            "responseMessageId": str(uuid.uuid4()), "streamId": str(uuid.uuid4()),
            "model": model, "convexSessionId": str(uuid.uuid4()),
            "modelParams": {"reasoningEffort": "default", "includeSearch": False, "includeImageGeneration": False},
            "userInfo": {"timezone": "UTC", "languages": ["en-US"], "viewport": "1280x800"},
            "selectedMemoryIds": [], "ephemeral": False}
    r = requests.post(MC_API, json=body,
                      headers={"authorization": f"Bearer {tok}", "content-type": "application/json",
                               "x-is-human": hih},
                      timeout=(12, timeout), stream=True)
    if r.status_code == 429:
        raise _McLimit("429")
    if r.status_code == 401:
        raise _McAuth("401")
    if r.status_code in (402, 403):
        raise _McLimit("sub")
    if r.status_code >= 500:
        raise _McHih("500")
    parts = []
    r.raw.decode_content = True
    for raw in r.iter_lines(chunk_size=None):
        if not raw:
            continue
        ln = raw.decode("utf-8", "ignore").strip() if isinstance(raw, bytes) else str(raw).strip()
        if not ln.startswith("data:"):
            continue
        p = ln[5:].strip()
        if p == "[DONE]":
            break
        try:
            d = json.loads(p)
        except Exception:
            continue
        t = d.get("type") if isinstance(d, dict) else None
        if t == "text-delta":
            parts.append(str(d.get("delta") or ""))
        elif t == "error":
            raise _McLimit(str(d.get("errorText") or "stream-err")[:90])
        elif t == "finish":
            break
    ans = "".join(parts).strip()
    if not ans:
        raise _McLimit("empty")
    return ans

def _mc_hih(force=False):
    """تۆکنی x-is-human — کاش ٤٠خ + فایلی پاشبنەما + مینتەری دەرەکی ئارەزوومەندانە"""
    now = time.time()
    if not force and _MC_HIH.get("tok") and now - float(_MC_HIH.get("ts") or 0) < 2400:
        return _MC_HIH["tok"]
    mu = os.environ.get("MC_MINTER_URL") or ""
    if mu:
        try:
            r = requests.get(mu.rstrip("/") + "/hih", params={"key": os.environ.get("MC_MINTER_KEY") or ""},
                             timeout=(8, 15))
            if r.status_code == 200 and (r.json() or {}).get("x-is-human"):
                _MC_HIH["tok"], _MC_HIH["ts"] = r.json()["x-is-human"], now
                _json_save(MC_HIH_FILE, {"tok": _MC_HIH["tok"], "ts": now})
                return _MC_HIH["tok"]
        except Exception:
            pass
    d = _json_load_safe(MC_HIH_FILE) or {}
    t = d.get("tok")
    if t and now - float(d.get("ts") or 0) < 7200:
        _MC_HIH["tok"], _MC_HIH["ts"] = t, float(d.get("ts") or 0)
        return t
    return _MC_HIH.get("tok") or ""

def _mc_load():
    d = _json_load_safe(MC_ACC_FILE) or {}
    MC_ST["accounts"] = d.get("accounts") or []
    MC_ST["idx"] = int(d.get("idx") or 0)
    MC_ST["signups"] = d.get("signups") or {"date": "", "n": 0}
    if not _MC_HIH.get("tok"):
        d2 = _json_load_safe(MC_HIH_FILE) or {}
        if d2.get("tok"):
            _MC_HIH["tok"], _MC_HIH["ts"] = d2["tok"], float(d2.get("ts") or 0)

def _mc_pick():
    accs = [a for a in _mc_alive() if time.time() >= float(a.get("cool") or 0)]
    if not accs:
        return None
    a = accs[MC_ST.get("idx", 0) % len(accs)]
    MC_ST["idx"] = (MC_ST.get("idx", 0) + 1) % max(1, len(accs))
    return a

def _mc_refresh(acc):
    """نوێکردنەوەی JWT بە refreshToken — Convex auth:signIn"""
    a = _mc_convex([{"refreshToken": acc.get("rt") or ""}])
    t = (a.get("value") or {}) if isinstance(a, dict) else {}
    t = t.get("tokens") or t
    if isinstance(t, dict) and t.get("token"):
        acc["tok"] = t["token"]
        acc["ts"] = time.time()
        if t.get("refreshToken"):
            acc["rt"] = t["refreshToken"]
        with MC_LOCK:
            _mc_save()
        return acc["tok"]
    return None

def _mc_save():
    _json_save(MC_ACC_FILE, {"accounts": MC_ST.get("accounts") or [],
                             "idx": MC_ST.get("idx") or 0,
                             "signups": MC_ST.get("signups") or {"date": "", "n": 0}})

def _pi_headers():
    return {"Origin": PI_BASE, "Referer": PI_BASE + "/talk", "x-api-version": "5",
            "x-client-timezone": "UTC", "User-Agent": PI_UA}

def _pi_session():
    """نشستی curl_cffi — بەکارهێنەری نەناسراو (chat/start + legal-accept)"""
    from curl_cffi import requests as _cr
    import uuid as _u
    s = _cr.Session(impersonate="chrome")
    did = str(_u.uuid4())
    r = s.post(PI_BASE + "/api/chat/start",
               json={"distinctId": did, "deviceFingerprint": "pnjfnj"},
               headers=_pi_headers(), timeout=(15, 30))
    if r.status_code != 200:
        raise EMError(f"pi: start {r.status_code}")
    r2 = s.post(PI_BASE + "/api/user/legal-accept",
                json={"name": "Yusf", "ageVerified": True,
                      "useDataToImproveModelsConsent": True,
                      "useEmotionRecognitionOnVoiceConsent": True},
                headers=_pi_headers(), timeout=(15, 30))
    PI_STATE["s"] = s
    PI_STATE["did"] = did
    return s, did

def _pia_mark(acc, agent_id, err):
    lm = PIA_ST.setdefault("limits", {}).setdefault(acc.get("email") or "?", {})
    today = time.strftime("%Y-%m-%d", time.gmtime())
    lm[agent_id] = today
    low = str(err).lower()
    if any(w in low for w in ("subscription", "upgrade", "quota", "limit", "frequent", "credit", "balance", "exceed")):
        lm["*"] = today
        _replace_dead_soon("pia")  # #94U24: مردنی گشتی → نوێ لە جێی
    _pia_save_acc()

def _pia_pick(agent_id):
    accs = PIA_ST.get("accounts") or []
    if not accs:
        return None
    today = time.strftime("%Y-%m-%d", time.gmtime())
    lim = PIA_ST.get("limits") or {}
    n = len(accs)
    for i in range(n):
        a = accs[(PIA_ST.get("idx", 0) + i) % n]
        L = lim.get(a.get("email") or "?") or {}
        if L.get("*") == today or L.get(agent_id) == today:
            continue
        PIA_ST["idx"] = (PIA_ST.get("idx", 0) + i + 1) % n
        return a
    return None

def _pick_ua(pool, win=600):
    """#91ID: IDENTITY-LOCK — هەمان UA بۆ ١٠ خولەک (وەک وێبگەڕی ڕاستەقینە).
       پێشتر: هەر داواکارییەک UA ی نوێ = same-session identity flip = دەستنیشانکردن!"""
    try:
        k = id(pool)
        now = time.time()
        v = _UA_STICK.get(k)
        if not v or now - v[0] > win:
            v = (now, random.choice(pool))
            _UA_STICK[k] = v
            if len(_UA_STICK) > 50:
                _UA_STICK.pop(next(iter(_UA_STICK)), None)
        return v[1]
    except Exception:
        return random.choice(pool) if pool else "Mozilla/5.0"

def _yl_headers(finger, tok=None, ct=True):
    hd = {"User-Agent": YL_UA, "x-platform": "web", "x-version": "999.0.0",
          "x-finger": finger, "x-language": "en", "Origin": YL_BASE,
          "Referer": YL_BASE + "/ar/chat"}
    if ct:
        hd["Content-Type"] = "application/json"
    if tok:
        hd["x-auth-token"] = tok
    return hd

def _yl_identity(force=False):
    """میوانی نوێ: createGuest → loginByGuest (JWT ٣٠ ڕۆژ) → createSession — بێ captcha"""
    import time as _t
    import hashlib as _hl
    if not force and _YL["tok"] and _YL["sid"] and _t.time() - _YL["t"] < 4 * 86400:
        return
    finger = _hl.md5(("yl" + str(_t.time_ns()) + str(random.random())).encode()).hexdigest()
    g = requests.post(YL_BASE + "/api/auth/createGuest", headers=_yl_headers(finger, ct=False), timeout=(10, 20)).json()
    d = g.get("data") or {}
    if not d.get("guestUid"):
        raise EMError(f"yl: createGuest {str(g)[:60]}")
    r2 = requests.post(YL_BASE + "/api/auth/loginByGuest", headers=_yl_headers(finger), json=d, timeout=(10, 20)).json()
    tok = (r2.get("data") or {}).get("idToken")
    if not tok:
        raise EMError(f"yl: login {str(r2)[:60]}")
    r3 = requests.post(YL_BASE + "/api/msg/createSession", params={"botId": YL_BOT},
                       headers=_yl_headers(finger, tok=tok, ct=False), timeout=(10, 20)).json()
    sid = (r3.get("data") or {}).get("id")
    if not sid:
        raise EMError(f"yl: session {str(r3)[:60]}")
    _YL.update(tok=tok, sid=str(sid), finger=finger, t=_t.time())

def _z02_new_account():
    """هەژماری نوێ: mail.tm → supabase signup → confirm → access_token"""
    import uuid as _uuid
    ms = requests.Session()
    ms.headers.update({"User-Agent": ACT_UAS[random.randrange(len(ACT_UAS))]})
    r = ms.get("https://api.mail.tm/domains", timeout=(15, 30))
    dom = r.json()["hydra:member"][0]["domain"]
    email = f"z02x{int(time.time())}{random.randrange(100, 999)}@{dom}"
    pw = "Xk9!mQ2#vLp8$zRw"
    r = ms.post("https://api.mail.tm/accounts", json={"address": email, "password": pw}, timeout=(15, 30))
    if r.status_code not in (200, 201):
        raise EMError(f"z02 mail: {r.status_code}")
    r = ms.post("https://api.mail.tm/token", json={"address": email, "password": pw}, timeout=(15, 30))
    mtok = r.json()["token"]
    h = {"apikey": Z02_KEY, "Authorization": f"Bearer {Z02_KEY}", "Content-Type": "application/json"}
    r = requests.post(f"{Z02_SB}/auth/v1/signup", json={"email": email, "password": pw},
                      headers=h, timeout=(15, 40))
    if r.status_code != 200:
        raise EMError(f"z02 signup: {r.status_code}")
    # چاوەڕوانی نامەی confirm (SendGrid — quoted-printable decode)
    link = None
    import quopri as _qp
    for _ in range(8):
        time.sleep(3.5)
        try:
            r = ms.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {mtok}"},
                       timeout=(15, 30))
            msgs = r.json().get("hydra:member", [])
            if not msgs:
                continue
            mid = msgs[0]["id"]
            r = ms.get(f"https://api.mail.tm/messages/{mid}",
                       headers={"Authorization": f"Bearer {mtok}"}, timeout=(15, 30))
            d = r.json()
            html = d.get("html")
            html = html[0] if isinstance(html, list) else str(html)
            try:
                html = _qp.decodestring(html.encode()).decode("utf-8", "replace")
            except Exception:
                pass
            m = re.search(r'https://u[0-9a-z]+\.ct\.sendgrid\.net/ls/click\?[^"\'\s<>]+', html)
            if m:
                link = m.group(0)
                break
        except Exception:
            continue
    if not link:
        raise EMError("z02: نامەی confirm نەگەیشت")
    r = requests.get(link, allow_redirects=True, timeout=(15, 40),
                     headers={"User-Agent": ACT_UAS[0]})
    m = re.search(r'access_token=(eyJ[A-Za-z0-9_.-]+)', r.url)
    if not m:
        raise EMError("z02: access_token لە ڕیدایرێکت نییە")
    return m.group(1)

def _z02_token():
    """access_token ی زیندوو — ئەگەر کۆن بوو یان مردوو بوو نوێی دروست دەکات"""
    if _Z02_CACHE["token"] and time.time() < _Z02_CACHE["exp"]:
        return _Z02_CACHE["token"]
    tok = _z02_new_account()
    _Z02_CACHE["token"] = tok
    _Z02_CACHE["exp"] = time.time() + 3300  # JWT = 1 کاتژمێر
    return tok

def norm_model(mid):
    """کلیلێکی یەکگر بۆ ناسینی هەمان مۆدێڵ لە سەرچاوەی جیاواز"""
    s = str(mid).lower().strip()
    if "/" in s:
        s = s.split("/")[-1]
    s = s.replace("_", "-").replace(".", "-")
    for suf in _MERGE_SUFFIXES:
        if s.endswith(suf):
            s = s[:-len(suf)]
    return s

def _aiml_save():
    import json as _j
    try:
        _j.dump({"key": AIML_ST.get("key")}, open(AIML_ACC_FILE, "w", encoding="utf-8"), ensure_ascii=False)
    except Exception:
        pass

def _aka_headers():
    return {"User-Agent": AKA_UA, "Accept": "*/*", "Accept-Language": "en-US,en;q=0.9",
            "Origin": AKA_BASE, "Referer": AKA_BASE + "/",
            "sec-fetch-dest": "empty", "sec-fetch-mode": "cors", "sec-fetch-site": "same-origin"}

def _cake_pow(uuid, salt, difficulty, max_nonce=120_000_000, deadline_s=25):
    """PoW: sha256(uuid:salt:nonce) ≥ difficulty بتی سیفر لە سەرەتا"""
    import hashlib as _hl
    import time as _t
    pre = f"{uuid}:{salt}:".encode()
    thr = (1 << (32 - difficulty)) if 0 < difficulty < 32 else 1
    n = 0
    digest = _hl.sha256
    t0 = _t.time()
    while n < max_nonce:
        end = n + 200000
        for nn in range(n, end):
            d = digest(pre + str(nn).encode()).digest()
            if int.from_bytes(d[:4], "big") < thr:
                return nn, d.hex()
        n = end
        if _t.time() - t0 > deadline_s:
            return None, None
    return None, None

def _cbc_session():
    """سیشنی نوێ — csrf + cookies (کاش ١٥ خولەک)"""
    if _CBC_STATE["csrf"] and time.time() - _CBC_STATE["t"] < 900:
        return _CBC_STATE["csrf"], _CBC_STATE["cookies"]
    r = requests.get(CBC_BASE + "/", headers={"User-Agent": UA}, timeout=25)
    m = re.search(r'name="csrf-token" content="([^"]+)"', r.text)
    if not m:
        raise EMError("cbc: csrf نەدۆزرایەوە")
    jar = {}
    for sc in r.raw.headers.getlist("Set-Cookie") if hasattr(r.raw, "headers") else [r.headers.get("Set-Cookie") or ""]:
        if not sc:
            continue
        kv = sc.split(";")[0]
        k = kv.split("=")[0].strip()
        from urllib.parse import unquote
        jar[k] = unquote(kv.split("=", 1)[1])
    cookie_header = "; ".join(f"{k}={v}" for k, v in jar.items())
    _CBC_STATE["csrf"], _CBC_STATE["cookies"], _CBC_STATE["t"] = m.group(1), cookie_header, time.time()
    return _CBC_STATE["csrf"], _CBC_STATE["cookies"]

def _cbox_alive():
    today = time.strftime("%Y-%m-%d", time.gmtime())
    out = []
    for a in (CBOX_ST.get("accounts") or []):
        if a.get("dead"):
            continue
        if a.get("day") == today and int(a.get("n") or 0) >= CBOX_DAY_CAP:
            continue
        out.append(a)
    return out

def _ct_vtoken(vid):
    """vtoken = base64(RSA-PKCS1v15-pub(vid)) — تەنها stdlib (پادینی تایپ-٢ ڕاندۆم)"""
    import base64 as _b64
    import secrets as _sc
    ps_len = 128 - 3 - len(vid)
    ps = bytearray()
    while len(ps) < ps_len:
        b = _sc.token_bytes(1)
        if b != b"\x00":
            ps += b
    em = b"\x00\x02" + bytes(ps) + b"\x00" + vid.encode()
    return _b64.b64encode(pow(int.from_bytes(em, "big"), _CT_E, _CT_N).to_bytes(128, "big")).decode()

def _duck_jwk():
    if DUCK_JWK[0] is None:
        from cryptography.hazmat.primitives.asymmetric import rsa
        k = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        n = k.public_key().public_numbers().n
        nb = n.to_bytes((n.bit_length() + 7) // 8, "big")
        DUCK_JWK[0] = {"alg": "RSA-OAEP-256", "e": _duck_b64u((65537).to_bytes(3, "big")),
                       "ext": True, "key_ops": ["encrypt"], "kty": "RSA",
                       "n": _duck_b64u(nb), "use": "enc"}
    return DUCK_JWK[0]

def _duck_session():
    global DUCK_SESSION
    if DUCK_SESSION is None:
        DUCK_SESSION = requests.Session()
        DUCK_SESSION.headers.update({
            "User-Agent": DUCK_UA, "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://duck.ai/", "Origin": "https://duck.ai",
            "Sec-Fetch-Dest": "empty", "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"})
    return DUCK_SESSION

def _duck_signals():
    import base64 as _b, json as _j, random as _r
    now = int(time.time() * 1000)
    t = _r.randint(80, 180)
    ev = [{"name": "onboarding_impression_1", "delta": t}]
    t += _r.randint(120, 260)
    ev.append({"name": "onboarding_impression_2", "delta": t})
    t += _r.randint(200, 500)
    ev.append({"name": "startNewChat", "delta": t})
    for _ in range(_r.randint(6, 14)):
        t += _r.randint(40, 180)
        ev.append({"name": "user_input", "delta": t})
    t += _r.randint(120, 350)
    ev.append({"name": "user_submit", "delta": t})
    p = {"start": now - 8000, "events": ev, "end": t + _r.randint(20, 90)}
    return _b.b64encode(_j.dumps(p, separators=(",", ":")).encode("utf-8")).decode("ascii")

def _duck_solve(challenge_b64):
    """چەلەنجەی JS ی سێرڤەر لە V8 چارە دەکات + wrapper ی FE (origin/stack/duration)"""
    import base64 as _b, json as _j, random as _r
    from py_mini_racer import MiniRacer
    js = _b.b64decode(challenge_b64).decode("utf-8", errors="replace")
    with DUCK_LOCK:
        ctx = MiniRacer()
        try:
            ctx.eval(DUCK_STUBS_JS.replace("__DDG_REAL_UA__", _j.dumps(DUCK_UA))
                                    .replace("__DDG_HTML_LOOKUP__", "{}"))
            ctx.eval("(%s).then(function(v){__R=v;}).catch(function(e){__E=String((e&&e.stack)||e);});" % js)
            for _ in range(100):
                if ctx.execute("__R !== null || __E !== null"):
                    break
                time.sleep(0.02)
            err = ctx.execute("__E")
            if err:
                raise RuntimeError(str(err)[:120])
            res = ctx.execute("__R")
        finally:
            try:
                del ctx
            except Exception:
                pass
    if not isinstance(res, dict) or not res.get("client_hashes"):
        raise RuntimeError("duck: چەلەنجە بەتاڵ")
    ch = list(res["client_hashes"])
    ch[0] = DUCK_UA
    res["client_hashes"] = [_duck_b64sha(x) for x in ch]
    res.setdefault("meta", {})
    res["meta"]["origin"] = "https://duck.ai"
    res["meta"]["stack"] = "Error\n    at https://duck.ai/dist/duckai-dist/entry.duckai.js:2:123456"
    res["meta"]["duration"] = str(_r.randint(40, 250))
    return _b.b64encode(_j.dumps(res, separators=(",", ":")).encode("utf-8")).decode("ascii")

def _duck_warm(px=None):  # #94U49: px
    if DUCK_WARMED[0]:
        return
    with DUCK_LOCK:
        if DUCK_WARMED[0]:
            return
        try:
            _kw = {"proxies": {"http": px, "https": px}} if px else {}
            _duck_session().get("https://duck.ai/", headers={
                "Accept": "text/html", "Upgrade-Insecure-Requests": "1"}, timeout=(15, 20), **_kw)
        except Exception:
            pass
        DUCK_WARMED[0] = True

def _mc_convex(args, px=None):
    """داواکاری Convex action — auth:signIn flow ەکان"""
    _kw = {"json": {"path": "auth:signIn", "format": "json", "args": args},
           "headers": {"Content-Type": "application/json", "Convex-Client": "npm-1.25.4"},
           "timeout": (12, 30)}
    if px:
        _kw["proxies"] = {"http": px, "https": px}
    r = requests.post(MC_CONVEX, **_kw)
    try:
        return r.json()
    except Exception:
        return {}


def _mc_convex_dual(args, px):
    """#119b: convex via proxy, direct retry (proxies often bot-walled)"""
    try:
        r = _mc_convex(args, px)
        if isinstance(r, dict) and r.get("status") == "success":
            return r
    except Exception:
        r = {}
    try:
        return _mc_convex(args)
    except Exception:
        return r

def _mc_token(acc):
    """توکنی دروست — JWT ی ١ کاتژمێر: نوێکردنەوە پێش بەسەڕچوون"""
    tok = acc.get("tok") or ""
    if tok:
        try:
            pl = tok.split(".")[1]
            pl += "=" * (-len(pl) % 4)
            exp = (json.loads(base64.urlsafe_b64decode(pl)) or {}).get("exp") or 0
            if exp - time.time() > 300:
                return tok
        except Exception:
            pass
    return _mc_refresh(acc)

def _duck_b64sha(s):
    import base64 as _b, hashlib as _h
    return _b.b64encode(_h.sha256(s.encode("utf-8")).digest()).decode("ascii")

def _duck_b64u(b):
    import base64 as _b
    return _b.urlsafe_b64encode(b).decode().rstrip("=")

def _mc_signup_new(force=False):
    """ساینئەپی تەواوی multichats.ai — mail.tm → convex signUp → ٨-ژمارە → email-verification (~١٥چ)"""
    today = time.strftime("%Y-%m-%d", time.gmtime())
    with MC_LOCK:
        sg = MC_ST.get("signups") or {"date": "", "n": 0}
        if sg.get("date") != today:
            sg = {"date": today, "n": 0}
        if not force and int(sg.get("n") or 0) >= MC_DAILY_CAP:
            return None
    sess = requests.Session()
    _mpxs = _proxy_signup_best(4) + [None]  # #119: proxy-first
    _mpx = _mpxs[0]
    if _mpx:
        sess.proxies.update({"http": _mpx, "https": _mpx})
    em, pw, mtok = _mc_mail_new(sess)
    if not mtok:  # #119b: proxy may break mail.tm → one direct retry
        try:
            sess.proxies.clear()
        except Exception:
            pass
        _mpx = None
        em, pw, mtok = _mc_mail_new(sess)
    if not mtok:
        return None
    V = base64.urlsafe_b64encode(os.urandom(64)).rstrip(b"=").decode()
    try:
        _mc_convex_dual([{"provider": "password", "params": {"email": em, "password": pw, "flow": "signUp"}, "verifier": V}], _mpx)
    except Exception:
        pass
    code = None
    _rounds = 8
    if isinstance(mtok, str) and mtok.startswith("guerr:"):  # #119: guerrilla inbox
        _gsid = mtok.split(":", 1)[1]
        for _ in range(8):
            time.sleep(5)
            _gm = re.search(r"\b(\d{8})\b", _guerr_body(_gsid) or "")
            if _gm:
                code = _gm.group(1)
                break
        _rounds = 0  # skip mail.tm loop below
        if not code:
            print("[MC] guerrilla code timeout", flush=True)
            return None
    for _ in range(_rounds):  # mail.tm wait (skipped for guerrilla)
        time.sleep(5)
        try:
            ms = sess.get("https://api.mail.tm/messages", headers={"Authorization": f"Bearer {mtok}"}, timeout=(12, 30))
            for it in (ms.json() or {}).get("hydra:member", []) if ms.status_code == 200 else []:
                try:
                    md = sess.get(f"https://api.mail.tm/messages/{it.get('id')}", headers={"Authorization": f"Bearer {mtok}"}, timeout=(12, 30))
                    mm = re.search(r"\b(\d{8})\b", md.text or "")
                    if mm:
                        code = mm.group(1)
                        break
                except Exception:
                    continue
            if code:
                break
        except Exception:
            continue
    if not code:
        print("[MC] کۆدەکە نەگەیشت", flush=True)
        return None
    try:
        a2 = _mc_convex_dual([{"provider": "password", "params": {"email": em, "password": pw, "flow": "email-verification", "code": code}, "verifier": V}], _mpx)
    except Exception as e:
        print(f"[MC] verify: {str(e)[:60]}", flush=True)
        return None
    toks = ((a2.get("value") or {}).get("tokens") or {}) if isinstance(a2, dict) else {}
    rt = toks.get("refreshToken")
    if not rt:
        print(f"[MC] verify بێ توکن: {str(a2)[:80]}", flush=True)
        return None
    acc = {"email": em, "pw": pw, "rt": rt, "tok": toks.get("token") or "", "ts": time.time(),
           "n": 0, "day": today, "cool": 0, "dead": 0, "made": time.time()}
    with MC_LOCK:
        MC_ST["accounts"].append(acc)
        sg = MC_ST.get("signups") or {"date": today, "n": 0}
        if sg.get("date") != today:
            sg = {"date": today, "n": 0}
        sg["n"] = int(sg.get("n") or 0) + 1
        MC_ST["signups"] = sg
        _mc_save()
        try:
            _mc_save_acc()  # #119: gist persist (was file-only → evaporated, stuck at 800)
        except Exception:
            pass
        alive = len(_mc_alive())
    if sg["n"] % 25 == 0 or alive in (1, 5, 10, 50, 100, 250, 500, 750, 1000):
        print(f"[MC] حەوز: {alive} زیندوو | ئەمڕۆ {sg['n']} ساینئەپ", flush=True)
    return acc

def _mc_mail_new(sess):
    """ئیمەیڵی کاتی mail.tm — 429 → خستنەوە"""
    em = "mchat" + uuid.uuid4().hex[:10] + "@uberip.com"
    pw = "Xq" + uuid.uuid4().hex[:12] + "A!"
    for i in range(3):
        try:
            sess.post("https://api.mail.tm/accounts", json={"address": em, "password": pw}, timeout=(12, 30))
            time.sleep(3 if i == 0 else 1)
            for j in range(2):
                rt = sess.post("https://api.mail.tm/token", json={"address": em, "password": pw}, timeout=(12, 30))
                if rt.status_code == 200 and (rt.json() or {}).get("token"):
                    return em, pw, rt.json()["token"]
                time.sleep(25 if rt.status_code == 429 else 4)
            return em, pw, None
        except Exception as e:
            if i == 2:
                print(f"[MC] mail: {str(e)[:70]}", flush=True)
            time.sleep(5)
    try:  # #119: mail.tm failed → guerrilla fallback (proven by ach)
        em1, sid1 = _guerr_new()
        if em1:
            print(f"[MC] mail: guerrilla fallback ✅ {em1[:20]}", flush=True)
            return em1, pw, "guerr:" + sid1
    except Exception:
        pass
    return em, pw, None

def _proxy_check(pxs, cap=18):
    """#91H کڕاک: شەپۆلی خێرا → ڕیزکردن بەپێی خێرایی — دوو شەپۆل تا پڕ ببێت"""
    res = _proxy_screen(pxs[:min(180, cap * 8)])
    if len(res) < cap and len(pxs) > 180:
        res += _proxy_screen(pxs[180:360])
    res.sort()
    return [p for _, p in res[:cap]]

def _proxy_fetch_all():
    """#91P: هەموو سەرچاوە بەقوەتەکان — لیستە ئاشکراکان + API ەکان (هەندان+وێبشەیر ئەگەر تۆکەن هەبێت)"""
    raw = []
    urls = [
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt",
        "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&timeout=8000",
        "https://proxylist.geonode.com/api/proxy-list?limit=500&page=1&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",  # #95U7: google-passed (کەمتر-flagged)
        "https://proxylist.geonode.com/api/proxy-list?limit=500&page=2&sort_by=lastChecked&sort_type=desc&protocols=http%2Chttps",  # #95U7
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-LIST/master/http.txt",
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
        "https://raw.githubusercontent.com/vakhov/fresh-proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/clarketm/proxy-list/master/proxy-list-raw.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
        "https://www.proxy-list.download/api/v1/get?type=http",
        "https://proxyspace.pro/http.txt",
        "https://openproxylist.xyz/http.txt",
        "https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/http_proxies.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/http.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-http.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/https/data.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/http.txt",
        "https://raw.githubusercontent.com/zloi-user/hideip.me/main/https.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/http.txt",
        "https://raw.githubusercontent.com/mmpx12/proxy-list/master/https.txt",
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/http/data.txt",
        "https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/https.txt",
        "https://raw.githubusercontent.com/jetkai/proxy-list/main/online-proxies/txt/proxies-https.txt",
        "https://raw.githubusercontent.com/roosterkid/openproxylist/main/HTTPS_RAW.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/http/http.txt",
    ]  # #94U39: +3 (17 HTTP)؛ #94U41: +9 (26 HTTP)
    def _pull(u):
        try:
            r = requests.get(u, timeout=(8, 16))
            if r.status_code == 200:
                return [x.strip() for x in r.text.split() if 6 < len(x.strip()) < 60]
        except Exception:
            pass
        return []
    ths = [threading.Thread(target=lambda u=u: raw.extend(_pull(u))) for u in urls]
    for t in ths:
        t.start()
    for t in ths:
        t.join(20)
    # Geonode API — JSON، گەورەترین سەرچاوە (HTTP + HTTPS)
    try:
        r = requests.get("https://proxylist.geonode.com/api/proxy-list?protocols=http%2Chttps&limit=500&sort_by=lastChecked&sort_type=desc", timeout=(8, 16))
        if r.status_code == 200:
            for x in (r.json() or {}).get("data") or []:
                raw.append(f"{x.get('ip')}:{x.get('port')}")
    except Exception:
        pass
    # #91K: سۆکسی — SOCKS5 + SOCKS4 (کەمتر بلۆک دەکرێن — پارێزراو) — بە تاگی scheme
    socks_raw = []
    for u, sch in (("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks5.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks5.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/zloi-user/hideip.me/main/socks5.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/socks4.txt", "socks4://"),
                   ("https://raw.githubusercontent.com/TheSpeedX/SOCKS-List/master/socks4.txt", "socks4://"),
                   ("https://raw.githubusercontent.com/hookzof/socks5_list/master/proxy.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks5.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/saschazesiger/Free-Proxies/master/proxies/socks4.txt", "socks4://"),
                   ("https://raw.githubusercontent.com/mmpx12/proxy-list/master/socks5.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks5/data.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/socks5_proxies.txt", "socks5://"),
                   ("https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=socks5&timeout=8000", "socks5://"),
                   ("https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/protocols/socks4/data.txt", "socks4://"),
                   ("https://raw.githubusercontent.com/sunny9577/proxy-scraper/master/generated/socks4_proxies.txt", "socks4://"),
                   ("https://raw.githubusercontent.com/roosterkid/openproxylist/main/SOCKS5_RAW.txt", "socks5://"),
                   ("https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/socks5/socks5.txt", "socks5://")):  # #94U39: +7؛ #94U41: +4 (15 SOCKS)
        try:
            r = requests.get(u, timeout=(8, 14))
            if r.status_code == 200:
                for x in r.text.split():
                    x = x.strip()
                    if 6 < len(x) < 60 and ":" in x:
                        socks_raw.append(sch + x)
        except Exception:
            pass
    try:
        r = requests.get("https://proxylist.geonode.com/api/proxy-list?protocols=socks4%2Csocks5&limit=500&sort_by=lastChecked&sort_type=desc", timeout=(8, 16))
        if r.status_code == 200:
            for x in (r.json() or {}).get("data") or []:
                socks_raw.append("socks5://" + f"{x.get('ip')}:{x.get('port')}")
    except Exception:
        pass
    # #91R: منزلی/elite — گەورەترین ئەگەری منزلی + elite-anonymous
    extra = []
    for u in ("https://raw.githubusercontent.com/zevtyardt/proxy-list/main/all.txt",
              "https://api.proxyscrape.com/v3/free-proxy-list/get?request=displayproxies&protocol=http&anonymity=elite&timeout=8000",
              "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt"):
        try:
            r = requests.get(u, timeout=(8, 16))
            if r.status_code == 200:
                for x in r.text.split():
                    x = x.strip()
                    if 6 < len(x) < 80 and (":" in x) and ("//" not in x.split(":")[0][-1:] or "://" in x):
                        extra.append(x)
        except Exception:
            pass
    # #91R: تێکەڵکردنی گشتی — HTTP · SOCKS · منزلی/elite
    mixed, si, si2 = [], 0, 0
    for x in raw:
        mixed.append(x)
        if len(mixed) % 6 == 0:
            if si < len(socks_raw):
                mixed.append(socks_raw[si]); si += 1
            elif si2 < len(extra):
                mixed.append(extra[si2]); si2 += 1
    mixed.extend(socks_raw[si:])
    mixed.extend(extra[si2:])
    raw = list(dict.fromkeys(mixed))
    if len(raw) > 40000:
        random.shuffle(raw)
        raw = raw[:15000]  # #91R+#94U15: سنووری ڕاو 15k — کەمکردنەوەی بیرگە/CPU دژە-OOM
    # #91W: وێبشەیر — ئەگەر تۆکەن هەبێت → هەموو جۆرەکانی (پرێمیۆم + داتاسنتر + منزلی) — خۆکارانە
    try:
        ws = json.load(open(os.path.join(DATA_DIR, "webshare.json")))
        tk = (ws or {}).get("token")
        if tk:
            _got = 0
            for _mode in ("residential", "datacenter"):
                try:
                    r = requests.get(f"https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page_size=25&type={_mode}",
                                     headers={"Authorization": "Token " + tk}, timeout=(8, 16))
                    if r.status_code == 200:
                        _res = (r.json() or {}).get("results") or []
                        for x in _res:
                            raw.append(f"{x.get('proxy_address')}:{x.get('port')}")
                        _got += len(_res)
                        if _res:
                            print(f"[PROXY-WS] وێبشەیر {_mode}: {len(_res)}", flush=True)
                except Exception:
                    pass
            if _got:
                print(f"[PROXY-WS] کۆی گشتی وێبشەیر: {_got}", flush=True)
    except Exception:
        pass
    return list(dict.fromkeys([x for x in raw if x]))

def sync_ac_models(force=False):
    """ئۆتۆ-ئەپدێتی AskAI: نەخشەی مۆدێڵەکان لە HTML — ٦ کاتژمێر (هەمان پارسەری Nuxt)"""
    import time as _t
    if not force and _t.time() - _AC_SYNC["t"] < 21600:
        return
    _AC_SYNC["t"] = _t.time()
    try:
        r = requests.get(AC_BASE + "/chat", headers={"User-Agent": AC_UA, "Accept": "text/html",
                                                     "Referer": AC_BASE + "/"}, timeout=(15, 40))
        if r.status_code != 200:
            print(f"[AC-SYNC] HTML {r.status_code}", flush=True)
            return
        models = _ca_extract_models(r.text)
        if not models:
            print("[AC-SYNC] نەخشە نەدۆزرایەوە — کاتی کۆن دەمێنێتەوە", flush=True)
            return
        ok = {}
        for k, v in models.items():
            try:
                if not (v or {}).get("is_active"):
                    continue
                # تەنها ئەوانەی سنووری خۆڕاییان هەیە — ئەوانی تر پرۆن و هەمیشە شکست دەخۆن
                if not (v.get("free_lifetime_message_limit") or 0) > 0:
                    continue
                ok[k] = {"version": v.get("version") or k, "label": v.get("display_name") or k}
            except Exception:
                continue
        if len(ok) >= 1:
            MS["ac_ok"] = ok
            _ms_save()
            print(f"[AC-SYNC] کاتالۆگ {len(ok)} مۆدێڵی خۆڕایی", flush=True)
    except Exception as e:
        print(f"[AC-SYNC] {str(e)[:80]}", flush=True)

def sync_aiml_models(force=False):
    """تۆمارکردنی کاتالۆگی AI/ML — ٦ کاتژمێر — tier=x"""
    import time as _t
    if not force and _t.time() - _AIML_SYNC["t"] < 21600:
        return
    _AIML_SYNC["t"] = _t.time()
    MS["aiml_ok"] = {}
    _ms_save()
    print("[AIML-SYNC] پاشکراوە — تەنها بە فەندز چالاک دەبێت", flush=True)

def sync_ak_models(servers):
    """anakin — مۆدێڵی نوێی لیستی گشتی → پڕۆب ی بچووک؛ تەنها ئەوەی میوان کاری دەکات زیاد دەکرێت"""
    if time.time() - MS_T["ak"] < 3600:
        return
    with MS_LOCK:
        if time.time() - MS_T["ak"] < 3600:
            return
        MS_T["ak"] = time.time()
    try:
        r = requests.get("https://api.anakin.ai/api/v1/ai-models?locale=en-US",
                         headers={"User-Agent": DUCK_UA, "Origin": "https://app.anakin.ai",
                                  "Referer": "https://app.anakin.ai/", "x-client-mode": "web"},
                         timeout=(15, 25))
        data = r.json().get("data") or []
        cands = []
        for x in data:
            if not isinstance(x, dict):
                continue
            mid = x.get("modelId")
            types = x.get("types") or []
            label = str(x.get("label") or "")
            if not mid or int(mid) in (308, 309) or "chat" not in types:
                continue
            if x.get("comingSoon") or x.get("legacy"):
                continue
            if re.search(r'flex|thinking|high|low|minimal', label, re.I):
                continue
            if str(mid) in MS["ak_ok"] or str(mid) in MS["ak_block"]:
                continue
            cands.append((int(mid), label))
        cands.sort(reverse=True)  # نوێترین پێشتر
        if not cands:
            return
        # سەرەتا پشکنینی تەندروستی — ٣٠٩ دەبێت کار بکات، ئەگینا IP لە cooldown ە و پڕۆب ڕاست ناکات
        def _probe(mid, content="hi"):
            payload = json.dumps({"app_id": 19510, "model_id": int(mid),
                                  "messages": [{"role": "user", "content": content}]})
            p = subprocess.run([NODE_BIN, AK_CLIENT], input=payload.encode("utf-8"),
                               capture_output=True, timeout=60)
            lines = [l for l in (p.stdout or b"").decode("utf-8", "replace").strip().splitlines() if l.strip()]
            return json.loads(lines[-1]) if lines else {}
        chk = _probe(309)
        if not (chk.get("ok") and chk.get("answer")):
            print("[SYNC] ak: ٣٠٩ وەڵام نەدایەوە — IP لە cooldown ە، پڕۆب دوادەخرێت", flush=True)
            return
        mid, label = cands[0]
        res = _probe(mid, "Say exactly: OK")
        if res.get("ok") and res.get("answer"):
            MS["ak_ok"][str(mid)] = {"label": label, "t": time.time()}
            print(f"[SYNC] ak: مۆدێڵی نوێی میوان ✅ {mid} {label}", flush=True)
        else:
            MS["ak_block"][str(mid)] = {"label": label, "t": time.time()}
            print(f"[SYNC] ak: {mid} {label} بۆ میوان کراوە نییە", flush=True)
        _ms_save()
    except Exception as e:
        print(f"[SYNC] ak هەڵە: {str(e)[:80]}", flush=True)

def sync_akash_models(force=False):
    """ئۆتۆ-ئەپدێتی akash: /api/models گشتی — تەنها دەقی (AkashGen/وێنە دەرباز)؛
       لابراوەکان لە کاتالۆگ خۆکارانە لابرددرێن (یاسای بەکارهێنەر)"""
    import time as _t
    if not force and _t.time() - MS_T.get("aka", 0.0) < 21600:
        return
    MS_T["aka"] = _t.time()
    try:
        r = requests.get(AKA_BASE + "/api/models", headers=_aka_headers(), timeout=(10, 20))
        items = r.json() or []
    except Exception as e:
        print(f"[AKA-SYNC] هەڵە: {str(e)[:70]}", flush=True)
        return
    text_models = {m.get("id") for m in items
                   if m.get("id") and m.get("api_id") and "gen" not in str(m.get("id", "")).lower()
                   and "image" not in str(m.get("description", "")).lower()}
    removed = [mid for mid in list(MS.get("aka_ok", {}).keys()) if mid not in text_models]
    for mid in removed:
        MS["aka_ok"].pop(mid, None)
        print(f"[AKA-SYNC] لابرا: {mid}", flush=True)
    added = 0
    for mid in text_models:
        if mid not in MS.get("aka_ok", {}) and mid not in MS.get("aka_bad", {}):
            try:
                code, ans = (None, None)
                s = _aka_session()
                cid = "".join(random.choices(_AKA_CHARS, k=12))
                body = {"id": cid, "messages": [{"role": "user", "content": "Reply: OK", "parts": [{"type": "text", "text": "Reply: OK"}]}],
                        "model": mid, "system": _AKA_NEUTRAL, "temperature": 0.6, "topP": 0.95, "context": []}
                rr = s.post(AKA_BASE + "/api/chat/", json=body, timeout=(10, 40), stream=True)
                if rr.status_code == 200:
                    MS.setdefault("aka_ok", {})[mid] = {"t": time.time()}
                    added += 1
                    print(f"[AKA-SYNC] نوێ ✅ {mid}", flush=True)
                elif rr.status_code == 429:
                    AKA_LIMIT["until"] = time.time() + 900
                    break
                else:
                    MS.setdefault("aka_bad", {})[mid] = {"code": rr.status_code, "t": time.time()}
            except Exception as e:
                MS.setdefault("aka_bad", {})[mid] = {"err": str(e)[:50], "t": time.time()}
    if added or removed:
        _ms_save()
    print(f"[AKA-SYNC] کاتالۆگ={len(text_models)} | نوێ={added} | لابرا={len(removed)} | aka_ok={len(MS.get('aka_ok', {}))}", flush=True)

def sync_al_models(force=False):
    """تۆمارکردنی کاتالۆگی AL — ٦ کاتژمێر (لیستی ناو-کۆد — لە چانکەکانی فرۆنتئێند دەرهێنراوە)"""
    import time as _t
    if not force and _t.time() - _AL_SYNC["t"] < 21600:
        return
    _AL_SYNC["t"] = _t.time()
    MS["al_ok"] = {}
    _ms_save()
    print("[AL-SYNC] پاشکراوە — تەنها بە سەبسکریپشن چالاک دەبێت", flush=True)

def sync_ca_models(force=False):
    """ئۆتۆ-ئەپدێتی ChatbotAI: نەخشەی مۆدێڵەکان لە HTML ی /chat — ٦ کاتژمێر"""
    import time as _t
    if not force and _t.time() - _CA_SYNC["t"] < 21600:
        return
    _CA_SYNC["t"] = _t.time()
    try:
        r = requests.get(CA_BASE + "/chat", headers={"User-Agent": CA_UA, "Accept": "text/html",
                                                     "Referer": CA_BASE + "/"}, timeout=(15, 40))
        if r.status_code != 200:
            print(f"[CA-SYNC] HTML {r.status_code}", flush=True)
            return
        models = _ca_extract_models(r.text)
        if not models:
            print("[CA-SYNC] نەخشە نەدۆزرایەوە — کاتی کۆن دەمێنێتەوە", flush=True)
            return
        ok = {}
        for k, v in models.items():
            try:
                if not (v or {}).get("is_active"):
                    continue
                ok[k] = {"version": v.get("version") or k, "label": v.get("display_name") or k}
            except Exception:
                continue
        if len(ok) >= 5:
            MS["ca_ok"] = ok
            _ms_save()
            print(f"[CA-SYNC] کاتالۆگ {len(ok)} مۆدێڵ", flush=True)
    except Exception as e:
        print(f"[CA-SYNC] {str(e)[:80]}", flush=True)

def sync_cb_models(force=False):
    """ئۆتۆ-ئەپدێتی ChatbotApp: کاتالۆگی webcms (٦ کاتژمێر) — تەنها دەقی بە botId"""
    import time as _t
    if not force and _t.time() - _CB_SYNC["t"] < 21600:
        return
    _CB_SYNC["t"] = _t.time()
    try:
        r = requests.get(CB_CMS, headers={"User-Agent": CB_UA, "Origin": "https://chat.chatbotapp.ai",
                                          "Referer": "https://chat.chatbotapp.ai/"}, timeout=(10, 40))
        if r.status_code != 200:
            print(f"[CB-SYNC] catalog {r.status_code}", flush=True)
            return
        items = (r.json() or {}).get("data") or []
        ok = {}
        for m in items:
            k = (m or {}).get("modelKey") or ""
            if not k or k in CB_SKIP_KEYS:
                continue
            if (m.get("type") or "") != "text":
                continue
            b = m.get("botId")
            if not isinstance(b, int) or b <= 0 or b in CB_HTTP400_BOTS:
                continue
            # #76: تەنها بۆتە بەخۆڕاییەکان (CB_FREE_BOTS) — heavy/پارەدار لە مێنیو لابردن
            if b not in CB_FREE_BOTS:
                continue
            tier = "f"
            lbl = CB_FREE_BOTS.get(b) or m.get("title") or k
            if lbl.startswith("models."):
                lbl = k
            ok[k] = {"botId": b, "label": lbl, "tier": tier}
        MS["cb_ok"] = ok
        _ms_save()
        print(f"[CB-SYNC] کاتالۆگ {len(items)} → تۆمارکراو {len(ok)}", flush=True)
    except Exception as e:
        print(f"[CB-SYNC] {str(e)[:80]}", flush=True)

def sync_ct_models(force=False):
    """ئۆتۆ-ئەپدێتی chattide: لیستی مۆدێڵە زیندووەکان لە چەرەکەکانی Next.js (TTL ٦ کاتژمێر).
       هیچ شتێک ناسڕدرێتەوە — تەنها زیادکردن (یاسای ڕاگرتنی هەموو مۆدێڵەکان)"""
    import time as _t
    if not force and _t.time() - _CT_SYNC["t"] < 21600:
        return
    _CT_SYNC["t"] = _t.time()
    found = {}

    def _scan(js):
        if 'value:"' not in js:
            return
        for arr in _CT_ARR_RE.findall(js):
            for _nm, val in _CT_VAL_RE.findall(arr):
                if _ct_is_model(val):
                    found[val] = True

    try:
        h = {"User-Agent": CT_UA}
        html = requests.get("https://www.chattide.ai/chat/", headers=h, timeout=(10, 20)).text
        chunks = set(re.findall(r'/_next/static/chunks/[a-zA-Z0-9/_.\-]+\.js', html))
        for cu in list(chunks)[:6]:
            try:
                js = requests.get("https://www.chattide.ai" + cu, headers=h, timeout=(10, 15)).text
                _scan(js)
                chunks |= set(re.findall(r'/_next/static/chunks/[a-zA-Z0-9/_.\-]+\.js', js))
            except Exception:
                continue
        for cu in list(chunks)[:30]:
            try:
                js = requests.get("https://www.chattide.ai" + cu, headers=h, timeout=(10, 15)).text
            except Exception:
                continue
            _scan(js)
    except Exception as e:
        print(f"[CT-SYNC] هەڵە: {str(e)[:80]}", flush=True)
        return
    added = 0
    for mid in found:
        if mid not in MS.get("ct_ok", {}) and mid not in MS.get("ct_bad", {}):
            MS.setdefault("ct_ok", {})[mid] = {"t": time.time()}
            added += 1
            print(f"[CT-SYNC] مۆدێڵی نوێ: {mid}", flush=True)
    if added:
        _ms_save()
    print(f"[CT-SYNC] chattide: {len(found)} دۆزرا، {added} زیادکرا، ct_ok={len(MS.get('ct_ok', {}))}", flush=True)

def sync_duck_models(servers):
    """لیستی مۆدێڵە ڕاییگەکانی duck.ai ڕاستەوخۆ لە bundle ی فەرمی — هەر ٣٠ خولەک"""
    if time.time() - MS_T["duck"] < 1800:
        return
    with MS_LOCK:
        if time.time() - MS_T["duck"] < 1800:
            return
        MS_T["duck"] = time.time()
    try:
        s = _duck_session()
        r = s.get("https://duck.ai/", headers={"Accept": "text/html", "Upgrade-Insecure-Requests": "1"},
                  timeout=(15, 25))
        m = re.search(r'(/dist/duckai-dist/entry\.duckai\.[A-Za-z0-9]+\.js)', r.text)
        if not m:
            print("[SYNC] duck: bundle نەدۆزرایەوە", flush=True)
            return
        r2 = s.get("https://duck.ai" + m.group(1), timeout=(15, 40))
        js = r2.text
        found = {}
        for mo in re.finditer(r'\{model:"([a-z0-9./\-]+)",modelName:"[^"]*",modelVariant:"([^"]*)",'
                              r'modelShortName:"([^"]*)".{0,600}?availableTo:\[([^\]]*)\]', js):
            mid, variant, short, avail = mo.group(1), mo.group(2), mo.group(3), mo.group(4)
            if "Free" not in avail:
                continue
            found[mid] = short or variant or mid
        for mo in re.finditer(r'\{model:"([a-z0-9./\-]+)",upgradeModel:"[^"]+"\}', js):
            found.pop(mo.group(1), None)  # مردووەکان لاببە
        newd = {}
        for mid, short in found.items():
            slug = re.sub(r'[^a-z0-9.]+', '-', mid.lower()).strip('-')
            newd[mid] = {"id": f"duck-{slug}", "name": f"{short} (Duck)",
                         "model_id": mid, "kind": "duck"}
        old_ids = set(MS.get("duck", {}).keys())
        MS["duck"] = newd
        _ms_save()
        extras = [k for k in newd if not _ms_dup(servers, k)]
        print(f"[SYNC] duck: {len(newd)} مۆدێڵی ڕاییگە ({','.join(newd)}) | نوێ: {extras}", flush=True)
    except Exception as e:
        print(f"[SYNC] duck هەڵە: {str(e)[:80]}", flush=True)

def sync_giz_models(force=False):
    """ئۆتۆ-ئەپدێتی GizAI: کاتالۆگی CDN (٦ کاتژمێر) — بێ probe (کوانتا نەسوتێت)؛
    فیلتەر: gateway/* (پارەدار) و free-limit-0 و شاراوە دەر دەکرێن"""
    import time as _t
    if not force and _t.time() - _GZ_SYNC["t"] < 21600:
        return
    try:
        r = requests.get(GZ_CDN, headers={"User-Agent": GZ_UA}, timeout=(10, 40))
        if r.status_code != 200:
            print(f"[GZ-SYNC] catalog {r.status_code}", flush=True)
            return
        cands = _gz_parse_catalog(r.text)
        if not cands:
            print("[GZ-SYNC] parse شکستی هێنا — کاتالۆگی کۆن دەمێنێتەوە", flush=True)
            return
        cat = {}
        for c in cands:
            v = c["value"]
            if v in GZ_SKIP or v.startswith("gateway/") or c.get("free0"):
                continue
            cat[v] = c["label"]
        # #91A12: NEVER-SHRINK — ئەگەر نوێ < 70% ی کۆن → کۆن بمێنێتەوە (flake ی سایت)
        _oldc = _GZ_SYNC.get("catalog") or {}
        if _oldc and len(cat) < len(_oldc) * 0.7:
            print(f"[GZ-SYNC] ⚠️ نوێ زۆر بچووکە ({len(cat)} < 70% ی {len(_oldc)}) — کۆن پارێزرا", flush=True)
            return
        _GZ_SYNC["catalog"] = cat
        _GZ_SYNC["t"] = _t.time()
        print(f"[GZ-SYNC] کاتالۆگ {len(cands)} → تۆمارکراو {len(cat)}", flush=True)
    except Exception as e:
        print(f"[GZ-SYNC] {str(e)[:80]}", flush=True)

def sync_gk_models(force=False):
    """ئۆتۆ-ئەپدێتی gadegetkit: پشکنینی زیندوو (٦ کاتژمێر)"""
    import time as _t
    if not force and _t.time() - _GK_SYNC["t"] < 21600:
        return
    _GK_SYNC["t"] = _t.time()
    try:
        a = gk_chat([{"role": "user", "content": "Reply with: OK"}], timeout=60)
        if a:
            if "glm-4-flash" not in MS.get("gk_ok", {}):
                MS.setdefault("gk_ok", {})["glm-4-flash"] = {"t": _t.time()}
                _ms_save()
            print("[GK-SYNC] gadegetkit زیندووە ✅", flush=True)
    except Exception as e:
        print(f"[GK-SYNC] {str(e)[:70]}", flush=True)

def sync_hb_models(force=False):
    """ئۆتۆ-ئەپدێتی hotbot: پشکنینی زیندوو (٦ کاتژمێر) — مۆدێڵی تاک"""
    import time as _t
    if not force and _t.time() - _HB_SYNC["t"] < 21600:
        return
    _HB_SYNC["t"] = _t.time()
    try:
        a = hb_chat([{"role": "user", "content": "Reply with: OK"}], timeout=45)
        if a:
            if "hotbot-chat" not in MS.get("hb_ok", {}):
                MS.setdefault("hb_ok", {})["hotbot-chat"] = {"t": _t.time()}
                _ms_save()
            print("[HB-SYNC] hotbot زیندووە ✅", flush=True)
    except Exception as e:
        print(f"[HB-SYNC] {str(e)[:70]}", flush=True)

def sync_hf_models(force=False):
    """ڕاکێشانی ئۆتۆماتیکی مۆدێڵەکانی HF:
       - کاتالۆگی زیندوو لە /v1/models (لابردنی ئەوانەی HF لابراون — یاسای بەکارهێنەر)
       - پشکنینی نوێیەکان (١٠/خول) → هەر کامێک وەڵام دا بگاتە hf_ok
       - مردووەکان (پشکنین/چات شکات) → hf_bad (دووبارە ٢٤ کاتژمێر)
       خول: ٦ کاتژمێر"""
    import time as _t
    if not force and _t.time() - _HF_SYNC["t"] < 21600:
        return
    _HF_SYNC["t"] = _t.time()
    try:
        r = requests.get(HF_BASE + "/models", headers={"User-Agent": "Mozilla/5.0"}, timeout=(10, 30))
        items = r.json().get("data") or []
    except Exception as e:
        print(f"[HF-SYNC] کاتالۆگ هەڵە: {str(e)[:70]}", flush=True)
        return
    catalog = {m.get("id") for m in items if m.get("id")}
    # ١) لابردنی ئەوانەی لە کاتالۆگ نەماون (مردوو/لابراو لەلایەن HF)
    removed = [mid for mid in list(MS.get("hf_ok", {}).keys()) if mid not in catalog]
    for mid in removed:
        MS["hf_ok"].pop(mid, None)
        print(f"[HF-SYNC] لابرا لە کاتالۆگ: {mid}", flush=True)
    # ٢) زیندووکردنەوەی bad ە کۆن (٢٤ کاتژمێر)
    for mid in list(MS.get("hf_bad", {}).keys()):
        if _t.time() - float(MS["hf_bad"][mid].get("t") or 0) > 86400:
            MS["hf_bad"].pop(mid, None)
    # ٣) پشکنینی نوێیەکان (١٠/خول)
    probed = 0
    added = 0
    for mid in catalog:
        if mid in MS.get("hf_ok", {}) or mid in MS.get("hf_bad", {}) or probed >= 10:
            continue
        probed += 1
        try:
            rr = requests.post(HF_BASE + "/chat/completions",
                               json={"model": mid, "messages": [{"role": "user", "content": "Reply: OK"}], "max_tokens": 8},
                               headers=_hf_headers(), timeout=(10, 40))
            if rr.status_code == 200 and (rr.json().get("choices") or [{}])[0].get("message", {}).get("content"):
                MS.setdefault("hf_ok", {})[mid] = {"t": _t.time()}
                added += 1
                print(f"[HF-SYNC] نوێ ✅ {mid}", flush=True)
            elif rr.status_code == 402:
                import calendar as _cal
                g = _t.gmtime(_t.time())
                nxt = (g.tm_year + (1 if g.tm_mon == 12 else 0), 1 if g.tm_mon == 12 else g.tm_mon + 1, 1)
                HF_LIMIT["until"] = _cal.timegm(nxt + (0, 0, 0)) + 300
                if MS.get("hf_ok"):
                    MS["hf_ok"].clear()
                    print("[HF-SYNC] کرێتی مانگانە تەواو — hf_ok پاککرایەوە", flush=True)
                _ms_save()
                break
            else:
                MS.setdefault("hf_bad", {})[mid] = {"code": rr.status_code, "t": _t.time()}
        except Exception as e:
            MS.setdefault("hf_bad", {})[mid] = {"err": str(e)[:60], "t": _t.time()}
        _t.sleep(0.6)
    if added or removed:
        _ms_save()
    print(f"[HF-SYNC] کاتالۆگ={len(catalog)} | نوێ={added} | لابرا={len(removed)} | hf_ok={len(MS.get('hf_ok', {}))}", flush=True)

def sync_hk_models(force=False):
    """ئۆتۆ-ئەپدێتی heck: پشکنینی زیندوو — ٤٠٢ (کرێکی بەتاڵ) → هیچ؛ سەرکەوتن → هەموو کاتالۆگەکە ✅
       نیو کاتژمێر لە کاتی مردوودا (زیندووبوونەوەی خێرا)، ٦ کاتژمێر لە کاتی زیندوودا"""
    import time as _t
    ok_now = bool(MS.get("hk_ok"))
    ttl = 21600 if ok_now else 1800
    if not force and _t.time() - MS_T.get("hk", 0.0) < ttl:
        return
    MS_T["hk"] = _t.time()
    probe = "deepseek/deepseek-v4-flash"
    try:
        a = hk_chat([{"role": "user", "content": "Reply with exactly: OK"}], probe, timeout=45)
        alive = bool(a)
    except Exception as e:
        alive = False
        msg = str(e)[:70]
        if "402" in msg or "credit" in msg.lower():
            print(f"[HK-SYNC] کرێکی سەرەوە بەتاڵە ({msg}) — چاوەڕوانی پڕکردنەوە", flush=True)
        else:
            print(f"[HK-SYNC] پشکنین شکات: {msg}", flush=True)
    if alive:
        added = 0
        for mid, _lbl in HK_CATALOG:
            if mid not in MS.get("hk_ok", {}):
                MS.setdefault("hk_ok", {})[mid] = {"t": _t.time()}
                added += 1
        for mid in list(MS.get("hk_bad", {}).keys()):
            MS["hk_bad"].pop(mid, None)
        if added or not ok_now:
            _ms_save()
        print(f"[HK-SYNC] heck زیندووە ✅ {added} مۆدێڵ چالاک بوون (hk_ok={len(MS['hk_ok'])})", flush=True)
    elif ok_now and not MS.get("hk_ok"):
        _ms_save()

def sync_l7_models():
    """ئۆتۆ-سینکی llm7 — turbo ی کۆمەڵگە + پشکنینی نوێیەکان (٣ لە خولێکدا) — هەر ٣٠ خولەک"""
    import time as _t
    if _t.time() - MS_T["l7"] < 1800:
        return
    try:
        r = requests.get(L7_BASE + "/models", headers={"User-Agent": ACT_UAS[0]},
                         timeout=(10, 20))
        items = (r.json() or {}).get("data") or []
    except Exception:
        return
    MS_T["l7"] = _t.time()
    cands = [m["id"] for m in items
             if m.get("tier") == "turbo" and m.get("model_type", "chat") == "chat"]
    # تێبینی: ok تەنها کاتێک لابردرێت کە چاتەکەی خۆی شکست بخوات (ل7 catalogs بەپێی ناوچە دەگۆڕدرێت)
    # bad ی کۆن دووبارە تاقی بکەوە (٢٤ کاتژمێر)
    for mid in list(MS["l7_bad"].keys()):
        if _t.time() - float(MS["l7_bad"][mid].get("t") or 0) > 86400:
            del MS["l7_bad"][mid]
    probed = 0
    for mid in cands:
        if mid in MS["l7_ok"] or mid in MS["l7_bad"] or probed >= 3:
            continue
        probed += 1
        try:
            rr = requests.post(L7_BASE + "/chat/completions",
                               json={"model": mid, "messages": [{"role": "user", "content": "Reply with: OK"}],
                                     "max_tokens": 8},
                               headers={"User-Agent": ACT_UAS[0], "Content-Type": "application/json"},
                               timeout=(10, 45))
            if rr.status_code == 200 and (rr.json().get("choices") or [{}])[0].get("message", {}).get("content"):
                MS["l7_ok"][mid] = {"t": _t.time()}
                print(f"[SYNC] l7: نوێی بێ-کلیل ✅ {mid}", flush=True)
            else:
                MS["l7_bad"][mid] = {"code": rr.status_code, "t": _t.time()}
        except Exception as e:
            MS["l7_bad"][mid] = {"err": str(e)[:60], "t": _t.time()}
        _ms_save()
        _t.sleep(1.5)

def sync_nv_models(force=False):
    """ئۆتۆ-ئەپدێتی Nova: کاتالۆگی webcms — تەنها مۆدێڵی هەرزان (botId ∈ NV_FREE_BOTS)"""
    import time as _t
    if not force and _t.time() - _NV_SYNC["t"] < 21600:
        return
    _NV_SYNC["t"] = _t.time()
    try:
        r = requests.get(NV_CMS, headers={"User-Agent": NV_UA, "Origin": "https://chat.novaapp.ai",
                                          "Referer": "https://chat.novaapp.ai/"}, timeout=(10, 40))
        if r.status_code != 200:
            print(f"[NV-SYNC] catalog {r.status_code}", flush=True)
            return
        items = (r.json() or {}).get("data") or []
        ok = {}
        for m in items:
            k = (m or {}).get("modelKey") or ""
            b = m.get("botId")
            if not k or k in NV_SKIP_KEYS or b is None:
                continue
            if (m.get("type") or "") != "text":
                continue
            # تەنها خۆڕاییەکان لە مینیو — پرێمیۆم/نەناسراو لادەبرێن (پارەدار)
            if b not in NV_FREE_BOTS:
                continue
            lbl = m.get("title") or k
            if lbl.startswith("models."):
                lbl = (NV_FREE_BOTS.get(b) or k)
            ok[k] = {"botId": b, "label": lbl, "tier": "f"}
        if ok:
            MS["nv_ok"] = ok
            _ms_save()
            print(f"[NV-SYNC] کاتالۆگ {len(items)} → تۆمارکراو {len(ok)}", flush=True)
    except Exception as e:
        print(f"[NV-SYNC] {str(e)[:80]}", flush=True)

def sync_pi_models(force=False):
    """ئۆتۆ-ئەپدێتی Pi: چاتی تاقیکردنەوە (٦ کاتژمێر) — بەکارهێنەری نوێ = کوانتای نوێ"""
    import time as _t
    if not force and _t.time() - _PI_SYNC["t"] < 21600:
        return
    _PI_SYNC["t"] = _t.time()
    try:
        PI_STATE["s"] = None  # نشستی نوێ = بەکارهێنەری نوێ
        a = pi_chat([{"role": "user", "content": "Reply with: OK"}], timeout=60)
        if a:
            if "pi-chat" not in MS.get("pi_ok", {}):
                MS.setdefault("pi_ok", {})["pi-chat"] = {"t": _t.time()}
                _ms_save()
            print("[PI-SYNC] pi زیندووە ✅", flush=True)
    except Exception as e:
        print(f"[PI-SYNC] {str(e)[:70]}", flush=True)

def sync_yl_models(force=False):
    """ئۆتۆ-ئەپدێتی yollo: پشکنینی زیندووی فلۆوی میوان (٦ کاتژمێر) — مۆدێڵی چات لە سێرڤەرەوە شاراوەیە"""
    import time as _t
    if not force and _t.time() - MS_T.get("yl", 0.0) < 21600:
        return
    MS_T["yl"] = _t.time()
    try:
        r = requests.get(YL_BASE + f"/api/bot?botId={YL_BOT}",
                         headers={"User-Agent": YL_UA}, timeout=(10, 20))
        if r.status_code != 200:
            print(f"[YL-SYNC] بۆت ڕێک نەگەیشت: {r.status_code}", flush=True)
            return
        MS.setdefault("yl_ok", {})["yollo-chat"] = {"t": _t.time()}
        _ms_save()
        print("[YL-SYNC] yollo زیندووە — yollo-chat ئامادە", flush=True)
    except Exception as e:
        print(f"[YL-SYNC] هەڵە: {str(e)[:80]}", flush=True)

def _ca_extract_models(html):
    """#91A6: safe-wrapper — parser هەرگیز sync ەک ناکوژێنێت"""
    try:
        return _ca_extract_models__raw(html)
    except Exception:
        return None

def _ct_is_model(val):
    v = str(val)
    if not re.match(r'^(gpt|claude|gemini|grok|llama|qwen|deepseek|mistral|glm|kimi|minimax|o[1-9])[\w.\-]*$', v):
        return False
    return not any(w in v for w in ("whisper", "tts", "embed", "image", "flux", "video", "music", "guard"))

def _ms_dup(servers, model_id):
    """ئایا ئەم مۆدێڵە پێشتر لە سەرچاوەیەکی تر هەیە؟ — دژە-دووبارە"""
    n = norm_model(model_id)
    if not n:
        return True
    for x in servers:
        if n in norm_model(x["id"]) or n in norm_model(str(x.get("model_id", ""))):
            return True
    return False

def _proxy_screen(batch, tmo=8):
    """#91H: شەپۆلێک تاقیکردنەوەی خێرا — سنوردارکردنی تڕێدەکان بە ThreadPoolExecutor بۆ پاراستنی یادگە لە OOM"""
    res = []
    _lk = threading.Lock()

    def _one(px):
        try:
            t0 = time.time()
            if px.startswith("socks4://") or px.startswith("socks5://"):
                pr = {"http": px.replace("socks5://", "socks5h://"), "https": px.replace("socks5://", "socks5h://")}
            else:
                pr = {"http": px, "https": px}
            r = requests.get("http://www.google.com/generate_204", proxies=pr, timeout=tmo)
            if r.status_code < 500:
                with _lk:
                    res.append((time.time() - t0, px))
        except Exception:
            pass

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:  # #94U15: 20→10 دژە-OOM
        futs = [executor.submit(_one, px) for px in batch]
        concurrent.futures.wait(futs, timeout=tmo + 4)
    return res

def _ca_extract_models__raw(html):
    """نەخشەی مۆدێڵەکان لە payload ی Nuxt ی HTML — کۆنفیگی multi_language (idMap: نرخ لە شوێنی تر)"""
    i = 0
    while True:
        j = -1
        for pat in ('{\\\\"is_active', '{\\"is_active', '{"is_active'):
            j = html.find(pat, i)
            if j >= 0:
                break
        if j < 0:
            return None
        k = html.rfind('"', max(0, j - 8), j)
        if k < 0:
            i = j + 1
            continue
        out = []
        esc = False
        pos = k + 1
        while pos < len(html):
            ch = html[pos]
            if esc:
                out.append(ch)
                esc = False
            elif ch == "\\":
                out.append(ch)
                esc = True
            elif ch == '"':
                break
            else:
                out.append(ch)
            pos += 1
        i = pos + 1
        try:
            inner = json.loads('"' + "".join(out) + '"')
            cfg = json.loads(inner)
        except Exception:
            continue
        if isinstance(cfg, dict) and isinstance(cfg.get("models"), dict) and len(cfg["models"]) >= 3:
            return cfg["models"]
    return None

def _fb_signup(key, email, pw, ua):
    """#94U31: signUp بە پرۆکسی-یەکەم (8 باشترین: منزلی→کەم-هەڵە→خێرا)؛ ڕاستەوخۆ تەنها دوایین چارەسەر"""
    def _call(px=None):
        kw = {"json": {"email": email, "password": pw, "returnSecureToken": True},
              "headers": {"User-Agent": ua}, "timeout": (8, 16) if px else (10, 25)}
        if px:
            kw["proxies"] = {"http": px, "https": px}
        r = requests.post("https://identitytoolkit.googleapis.com/v1/accounts:signUp?key=" + key, **kw)
        if r.status_code == 200:
            j = r.json() or {}
            tok = j.get("idToken")
            if not tok:
                return None
            return tok, j.get("localId") or ""
        try:
            msg = (r.json() or {}).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        return ("BLOCKED", msg) if msg in _FB_BLOCK else None
    _today = time.strftime("%Y-%m-%d", time.gmtime())
    _direct_bad = _FB_DIRECT_BAD.get(key) == _today
    _saw_blocked = False  # #94U34
    for px in _proxy_signup_best(8):  # #94U31: هەمیشە پرۆکسی یەکەم — IP ڕاستەوخۆ مەخەرە مەترسییەوە
        try:
            r2 = _call(px)
        except Exception:
            _proxy_mark_bad(px)  # پرۆکسی مردووە — لاببرێت
            continue
        if r2 and r2[0] == "BLOCKED":
            _saw_blocked = True
        _pool = PROXY_ST.get("pool") or {}
        _pe = _pool.get(px) or _pool.get(px.split("://", 1)[-1])
        if r2 and r2[0] != "BLOCKED":
            try:
                if _pe is not None:
                    _pe["sg_ok"] = time.time()
                    _pe["sg_bad"] = 0
                    (PROXY_ST.get("strikes") or {}).pop(px.split("://", 1)[-1], None)  # #94U39b: سەرکەوتن = سفرکردنەوەی زەبرەکان
            except Exception:
                pass
            print(f"[FB] signUp بە پرۆکسی ✅ {px[:28]}", flush=True)
            _sg_breaker_hit(key, True)
            return r2
        try:
            if _pe is not None:
                _pe["sg_bad"] = (_pe.get("sg_bad") or 0) + 1
        except Exception:
            pass
        # BLOCKED لەڕێی پرۆکسییەوە = IP ـەکە لای Firebase فلەگە — بۆ ساینئەپ بەکارمەهێنە بەڵام مەیسڕە (بۆ کاری تر باشە)
    # #94U31: دوایین هەوڵ: ڕاستەوخۆ (تەنها ئەگەر پرۆکسییەکان نەبوون/شکستخواردن)
    try:
        r = _call()
        if r and r[0] != "BLOCKED":
            _FB_DIRECT_BAD.pop(key, None)
            _sg_breaker_hit(key, True)
            return r
        if r and r[0] == "BLOCKED":
            _FB_DIRECT_BAD[key] = _today
            _saw_blocked = True
    except Exception:
        pass
    if _saw_blocked:  # #94U34: تەنها throttle ژمارە — collision (EMAIL_EXISTS) نەخەرە ئەستۆی کلیل
        _sg_breaker_hit(key, False)
    print(f"[FB] signUp fail (blocked_seen={_saw_blocked})", flush=True)  # #119: visible diag
    return None

def _proxy_signup_best(n=6):
    """#94U18: باشترین پرۆکسی بۆ ساینئەپ — منزلی یەکەم، کەم-هەڵە، خێرا؛ #94U33: شەفڵ لەناو هەر چینێک (بڵاوکردنەوە لەسەر چەند IP)"""
    pool = PROXY_ST.get("pool") or {}
    bad = PROXY_ST.get("bad") or set()
    cands = []
    for k, v in pool.items():
        if k in bad:
            continue
        v = v or {}
        if (v.get("sg_bad") or 0) >= 3:
            continue
        cands.append((0 if v.get("res") else 1, v.get("sg_bad") or 0, v.get("lat", 9), k))
    cands.sort()
    top = cands[:n]
    _res = [k for r, _, _, k in top if r == 0]
    _oth = [k for r, _, _, k in top if r != 0]
    random.shuffle(_res)
    random.shuffle(_oth)
    out = [(k if "://" in k else "http://" + k) for k in (_res + _oth)]
    if len(out) < n:
        try:
            for p in _proxy_get(n):
                if p not in out:
                    out.append(p)
                if len(out) >= n:
                    break
        except Exception:
            pass
    return out

def _sg_breaker_hit(key, ok):
    """#94U34: تۆماری ئەنجام — سەرکەوتن ڕیسیت، شکستی throttle ژمارە + trip لە 10؛ #94U38: backoff 15m→120m"""
    try:
        with _SG_BREAKER_LK:
            b = _SG_BREAKER.setdefault(key, {"fail": 0, "until": 0, "trips": 0})
            if ok:
                b["fail"] = 0
                b["trips"] = 0
                return
            b["fail"] = b.get("fail", 0) + 1
            if b["fail"] >= 10 and b.get("until", 0) <= time.time():
                t = b.get("trips", 0)
                pause = min(900 * (2 ** t), 7200)  # 15m → 30m → 60m → 120m cap
                b["until"] = time.time() + pause
                b["fail"] = 0
                b["trips"] = t + 1
                print(f"[BREAKER-{_sg_key_name(key)}] ⏸ پشووی {int(pause // 60)}m (10 throttle — پاراستنی کلیل)", flush=True)
    except Exception:
        pass

def _sg_key_name(key):
    """#94U38: ناوی حەوز بۆ لۆگ (کلیلەکە خۆی چاپ مەکە)"""
    global _SG_KEY_NAMES
    try:
        if _SG_KEY_NAMES is None:
            _SG_KEY_NAMES = {CA_KEY: "CA", CB_KEY: "CB", NV_KEY: "NV", AC_KEY: "AC"}
        return _SG_KEY_NAMES.get(key, "?")
    except Exception:
        return "?"

