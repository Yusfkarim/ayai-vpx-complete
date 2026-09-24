"""Appwrite function 'cronping' — pings Vercel /api/cron every 2 min.
Faithful reconstruction (2026-09-24) of the deployment running since 2026-09-23
(original /tmp source lost to sandbox volatility; behavior verified by 30+ executions).
Deploy layout: tarball containing src/main.py, entrypoint src/main.py, runtime python-3.12.
"""
import urllib.request

CRON_SECRET = "59a9eea2b0b63fb1bb4e9f1892300b43"  # baked at deploy time (same value as Vercel env CRON_SECRET)
URL = "https://ayai-vpx.vercel.app/api/cron?secret=" + CRON_SECRET


def main(context):
    try:
        req = urllib.request.Request(URL, headers={"User-Agent": "vpx-cronping/1.0"})
        r = urllib.request.urlopen(req, timeout=280)
        body = r.read().decode("utf-8", "replace")
        context.log("cron status=%s body=%s" % (r.status, body[:300]))
        return context.res.json({"ok": True, "status": r.status})
    except Exception as e:
        context.error("cron ping failed: %s" % e)
        return context.res.json({"ok": False, "err": str(e)[:200]})
