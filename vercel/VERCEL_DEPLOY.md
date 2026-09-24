# Vercel API (vpx) — Deploy Guide

OpenAI-compatible API + automatic pools. **KV only, ZERO Fly dependency.**

## 1) Import (5 min)
1. `vercel.com` → Add New → Project → Import `Yusfkarim/ayai`
2. **Root Directory = `vercel`** (REQUIRED — the api/ + vercel.json live here)
3. Framework: Other. Python auto-detected. Deploy — first build works WITHOUT env (KV falls back to memory)

## 2) Storage → KV (2 min)
1. Project → Storage → Create → KV (Upstash) → Connect to this project
2. Vercel auto-injects `KV_REST_API_URL` + `KV_REST_API_TOKEN` ✅
3. Redeploy (so functions pick up the env)

## 3) Env vars (Project → Settings → Environment Variables)
| var | value |
|---|---|
| `VAPI_KEY` | make one: `openssl rand -hex 24` (chatbots use `Bearer <this>`) |
| `CRON_SECRET` | another random hex (cron auth) |
| `CA_FB_KEY` / `CB_FB_KEY` / `NV_FB_KEY` | Firebase keys — from repo root `main.py`: `grep -n "^CA_KEY\|^CB_KEY\|^NV_KEY =" main.py` |
| `ACH_FB_KEY` | from `main.py`: `grep -n "^ACH_FB_KEY" main.py` |

Redeploy after adding env.

## 4) Test
```bash
BASE=https://<your-app>.vercel.app
curl $BASE/v1/models | head -c 300
curl -s $BASE/v1/chat/completions -H "Authorization: Bearer $VAPI_KEY" \
  -H "Content-Type: application/json" \
  -d '{"model":"pol-openai","messages":[{"role":"user","content":"Hi"}]}' | head -c 500
```

## 5) Cron on Hobby (IMPORTANT)
- Hobby cron = **1×/day only** (`0 4 * * *`). Pools fill slowly (~20/day).
- **Pro ($20/mo)**: change schedule to `*/10 * * * *` → pools fill ~1000+/day ✅
- **Hobby trick (FREE, Pro-like)**: ping cron from outside every 10 min:
  - **GitHub Actions** (add `.github/workflows/vpx-ping.yml` in repo root):
    ```yaml
    name: vpx-ping
    on:
      schedule: [{cron: "*/10 * * * *"}]
      workflow_dispatch:
    jobs:
      ping:
        runs-on: ubuntu-latest
        steps:
          - run: curl -s "https://<your-app>.vercel.app/api/cron?secret=${{ secrets.VPX_CRON }}" | head -c 400
    ```
    + repo Settings → Secrets → `VPX_CRON` = your CRON_SECRET
  - or **cron-job.org** (free): GET the same URL every 10 min

## 6) Use in chatbots (OpenAI-compatible)
```python
from openai import OpenAI
client = OpenAI(base_url="https://<your-app>.vercel.app/v1", api_key="<VAPI_KEY>")
r = client.chat.completions.create(model="pol-openai",
    messages=[{"role": "user", "content": "سڵاو"}])
print(r.choices[0].message.content)
```
Model IDs have provider prefixes: `pol-*`, `aff-*`, `lr-nano`, `gz-*`, `ach-*` (see `/v1/models`).

## V1 scope (honest)
- ✅ chat: pol / aff / lorka / giz / allchat (+ auto-fallback chain)
- ✅ auto-pools: CA/CB/NV Firebase minting + ACH full-cycle minting → KV
- ✅ proxy harvest + catalog sync + probes via cron
- ⏳ V2: pool-CHAT routing through CA/CB/NV pools (minted accounts used for chat), duck.ai (needs V8), streaming SSE
