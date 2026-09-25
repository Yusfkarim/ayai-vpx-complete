"""GET /api/cron — pool top-up + proxy harvest + catalog sync + probes. NO Fly.
V10: fits 55s Hobby wall — stages rotate across runs, flush after EVERY stage."""
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import providers
import usage
import kb


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
        want = providers.CRON_SECRET
        if not want:
            return True
        got = (self.headers.get("Authorization") or "").strip()
        if got == "Bearer " + want:
            return True
        try:
            q = parse_qs(urlparse(self.path).query)
            return (q.get("secret") or [""])[0] == want
        except Exception:
            return False

    def _flush(self):
        try:
            providers.kv.gist_flush(force=True)
        except Exception:
            pass

    def _flush_if_slow(self, t0):
        # #103: skip intermediate flush on fast runs (fewer GitHub PATCHes → fewer bans);
        # force only if the run drags past 90s. Final flush always persists everything.
        try:
            if time.time() - t0 > 90:
                providers.kv.gist_flush(force=True)
        except Exception:
            pass

    def do_GET(self):
        _ip = providers._sec_ip(self)
        if providers._ip_blocked(_ip):
            return self._send(429, {"error": "blocked"})
        if not self._auth():
            providers._note_badkey(_ip)
            return self._send(401, {"error": "bad cron secret"})
        t0 = time.time()
        budget = 40  # Hobby wall ~60s incl. ~10s cold import — stay well under
        out = {}
        try:
            _prev_cl = providers.kv.kv_jget("vpx:cron_last") or {}
        except Exception:
            _prev_cl = {}
        try:
            _lk = providers.kv.kv_jget("vpx:cron_lock") or {}
            if time.time() - float(_lk.get("t", 0)) < 90:
                return self._send(200, {"ok": True, "skipped": "overlap",
                                        "ago": round(time.time() - float(_lk.get("t", 0)), 1)})
            providers.kv.kv_jset("vpx:cron_lock", {"t": time.time()})
        except Exception:
            pass
        try:
            _n = int((providers.kv.kv_jget("vpx:cron_n") or {}).get("n", 0)) + 1
            providers.kv.kv_jset("vpx:cron_n", {"n": _n})
            self._flush()
        except Exception:
            _n = 1
        out["run"] = _n
        left = lambda: budget - (time.time() - t0)
        # every run maintains everything (only 2 runs/day on Hobby) — each stage
        # is budget-guarded + flushed, so a 60s kill never loses progress
        if _n % 4 == 0:
            # #119: MC top-up (heavy ~40s signup; overlap lock keeps 1 door running it)
            try:
                providers._seed_load()
                _mc_n = len(providers.R._mc_alive())
                if _mc_n < 1000 and left() > 20:
                    out["mint_mc"] = {"ok": bool(providers.R._mc_signup_new()),
                                      "total": len(providers.R._mc_alive())}
                else:
                    out["mint_mc"] = {"skipped": "full-or-busy", "total": _mc_n}
            except Exception as e:
                out["mint_mc"] = {"err": str(e)[:60]}
            self._flush_if_slow(t0)
        if left() > 30:
            try:
                out["sync"] = providers.sync_all(budget_s=min(10, left() - 16))
            except Exception as e:
                out["sync"] = {"err": str(e)[:80]}
            self._flush_if_slow(t0)
        if left() > 22:
            try:
                try:
                    providers.R._PIA_FASTPOLL[0] = True  # V10.3: cap pia poll 24s in cron
                except Exception:
                    pass
                out["topup"] = providers.topup_all(budget_s=min(15, left() - 10))
            except Exception as e:
                out["topup"] = {"err": str(e)[:80]}
            self._flush_if_slow(t0)
        if left() > 14:
            try:
                providers._seed_load()
                _an = len((providers.R.ACH_ST.get("accounts") or []))
                out["mint_ach"] = providers.mint_ach(count=min(max(0, 1000 - _an), 4), budget_s=min(15, left() - 6))
            except Exception as e:
                out["mint_ach"] = {"err": str(e)[:80]}
            self._flush_if_slow(t0)
        if left() > 6:
            try:
                if _n % 2 == 0:
                    out["harvest"] = providers.harvest_proxies(max_keep=60, deadline=min(6, left() - 1))
                else:
                    out["proxy"] = providers.proxy_fill(budget_s=min(6, left() - 1))
            except Exception as e:
                out["px"] = {"err": str(e)[:80]}
            self._flush_if_slow(t0)
        try:
            out["catalog"] = {"models": len(providers.full_catalog())}
        except Exception as e:
            out["catalog"] = {"err": str(e)[:80]}
        try:
            out["pools"] = providers.pool_stats()
        except Exception:
            pass
        out["seconds"] = round(time.time() - t0, 1)
        try:
            _bo = float(getattr(providers.kv, "_G_BACKOFF", [0.0])[0] or 0.0)
            out["gist_backoff_s"] = max(0, round(_bo - time.time(), 1))
        except Exception:
            pass
        try:
            _sync_ok = sum(1 for v in (out.get("sync") or {}).values() if (v or {}).get("ok"))
            _mint = sum((v or {}).get("minted", 0) for v in (out.get("topup") or {}).values()
                        if isinstance(v, dict))
            providers.kv.kv_jset("vpx:cron_t", {"t": time.time()})
            providers.kv.kv_jset("vpx:cron_last", {
                "t": time.time(), "sec": out.get("seconds"), "run": _n,
                "sync_ok": _sync_ok, "minted": _mint,
                "models": (out.get("catalog") or {}).get("models", 0)})
            self._flush()
        except Exception:
            pass
        try:
            _nm = (out.get("catalog") or {}).get("models", 0)
            _sy = sum(1 for v in (out.get("sync") or {}).values() if (v or {}).get("ok"))
            if _nm and _nm < 150:
                providers._vpx_sec_alert("⚠️ VPX catalog dropped: %s models (was ~190)" % _nm)
            elif out.get("sync") and _sy < 10:
                providers._vpx_sec_alert("⚠️ VPX sync weak: %s/14 ok" % _sy)
            try:
                _pt = float((_prev_cl or {}).get("t", 0))
                if _pt and time.time() - _pt > 1800:
                    providers._vpx_sec_alert("🚨 VPX persistence DEAD 30min+ (gist/token down?) — chat runs on memory, growth paused")
            except Exception:
                pass
            try:
                _ps = out.get("pools") or {}
                _weak = [k for k in ("ca", "cb", "nv", "ac", "alle") if (_ps.get(k) or {}).get("n", 0) < 300]
                if _weak:
                    providers._vpx_sec_alert("🚨 VPX pools collapsing: %s <300 — minting broken?" % ",".join(_weak))
            except Exception:
                pass
            try:
                _kb = providers.kv.kv_jget("vpx:kb:check") or {}
                if time.time() - float(_kb.get("t", 0)) > 3600:
                    _ok = kb.health_check()
                    providers.kv.kv_jset("vpx:kb:check", {"t": time.time(), "ok": bool(_ok),
                                                         "n": len(kb._KB.get("chunks") or [])})
                    if not _ok:
                        providers._vpx_sec_alert("🚨 VPX KB DEAD (recovery-books gist unreachable) — addiction answers running WITHOUT books")
            except Exception:
                pass
            try:
                usage.check_and_alert()
            except Exception:
                pass
        except Exception:
            pass
        return self._send(200, {"ok": True, **out})

    def _probes(self, deadline=10):
        t0 = time.time()
        names = ("pol", "lr", "aff", "gz", "ach", "ca", "cb", "nv", "ac",
                 "alle", "rwd", "duck", "l7", "g4f", "ct", "aka", "pi")
        res = {}
        def _one(p):
            try:
                ok, info = providers.probe(p)
                res[p] = {"ok": ok, "info": info}
            except Exception as e:
                res[p] = {"ok": False, "info": str(e)[:60]}
        ths = []
        for p in names:
            t = threading.Thread(target=_one, args=(p,), daemon=True)
            t.start()
            ths.append(t)
        for t in ths:
            rem = deadline - (time.time() - t0)
            if rem <= 0:
                break
            t.join(timeout=rem)
        for p in names:
            res.setdefault(p, {"ok": None, "info": "timeout"})
        try:
            providers.kv.kv_jset("vpx:health", {"t": time.time(), "probes": res})
        except Exception:
            pass
        return res

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.send_header("Content-Length", "0")
        self.end_headers()
