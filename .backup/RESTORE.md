# AYAI-VPX — Restore guide (from this complete backup)

## 1. Vercel (API host)
- Project: `ayai-vpx` → `https://ayai-vpx.vercel.app` (code in `vercel/`, deploy from that dir)
- Required env vars (values in `BACKUP-SECRETS.env` unless noted):
  - `GH_KV_GIST=c7596be3555f365be4006458d1ba81a5` (KV gist id)
  - `GH_TOKEN` = classic PAT with **gist** scope (same user that owns the gist)
  - `CRON_SECRET` (cron auth)
  - `VAPI_KEY` (chat auth) + Firebase keys `CA_FB_KEY CB_FB_KEY NV_FB_KEY AC_FB_KEY ACH_FB_KEY`
  - optional: `HF_TOKENS TG_TOKEN AL_KEY MC_MINTER_*`
- `vercel/vercel.json`: maxDuration 300 + backup crons 02:07/14:37Z (built-in)
- Deploy: `cd vercel && npx vercel deploy --prod --yes`

## 2. GitHub Gist KV (live database)
- Gist id `c7596be3555f365be4006458d1ba81a5` — restore files from `snapshot-20260924/`
- WARNING: GitHub secondary rate-ban if you burst PATCHes (>~30 rapid writes).
  The app has 403-backoff + no-storm logic (V10.4+). Restore slowly if ever needed.

## 3. Appwrite Cloud (DUAL schedulers — either alone keeps full cover)
- PRIMARY: project `vpxsched` → function `cronping`, schedule `*/2 * * * *` (even min)
- BACKUP: project `vpxsched2` → function `cronping2`, schedule `1-59/2 * * * *` (odd min)
- Overlap lock in cron.py arbitrates (second arrival skips). Keys: AW_KEY (proj1), AW_KEY2 (proj2).
- GitHub Actions `vpx-ping` (hourly) is a 3rd backup IF user enables Actions (currently disabled at user level).

- Console API: `https://cloud.appwrite.io/v1`, region endpoint: `https://fra.cloud.appwrite.io/v1`
- Org `vpxorg` (tier-0) → project `vpxsched` (region fra) → function `cronping`
- Function: runtime `python-3.12`, entrypoint `src/main.py`, **timeout 300**,
  schedule `*/2 * * * *`, source in `appwrite-cronping/main.py` (tar as `src/main.py`)
- API key needs scopes: `functions.read functions.write executions.read executions.write schedules.read schedules.write`
- Login + key in `BACKUP-SECRETS.env` (AW_EMAIL/AW_PW/AW_KEY)
- NOTE: Appwrite PUT /functions/{id} needs the FULL object or timeout resets to 15!
- Death-alerts (#105): cron sends TG alert if persistence dead 30min+ or any main pool <300 (1/hr throttle).
- Vercel mgmt token (for deploys) is NOT in this backup — ask owner (stored in agent workspace).

## 4. Verify
- Appwrite executions → `completed`, cron body `{"ok":true,"run":N,...}`
- Gist `vpx_cron_n.json` advancing + `vpx_cron_last.json` fresh
- `POST /api/chat` with `Authorization: Bearer <VAPI_KEY>` → 200 on several models
