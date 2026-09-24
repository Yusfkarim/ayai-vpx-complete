# VPX Mirror Backend (2nd Vercel account) — Setup Guide

Why: Vercel Hobby limits (100K invocations / 100GB / month) stop the site
with 503 when exhausted. A mirror on a second FREE account doubles the
headroom. Switch-over is client-side (each `*.vercel.app` URL belongs to
one account — the server cannot change its own URL).

## Step 1 — User (once, ~5 min)
1. Create a 2nd Vercel account (different email) at vercel.com/signup.
2. Create a token: Account Settings → Tokens → Create (scope: full).
3. Send the token to the agent (chat) — it is stored only as `~/.vtok2`
   in the agent sandbox, never in git.

## Step 2 — Agent (automatic)
1. `vercel deploy --prod --token=$VTOK2` from `vercel/` (same code).
2. Copy the SAME 12 env vars to the mirror project, INCLUDING
   `GH_TOKEN` + `GH_KV_GIST` (mirror shares pools/usage state via the
   same KV gist — one global brain, two serving doors).
3. Verify: `/api/status` 200 + models count matches + 1 test chat.
4. Report the mirror URL (e.g. `https://ayai-vpx-xxxx.vercel.app`).

## Step 3 — Clients (failover)
- **ta3afi app**: Settings → custom servers → add mirror URL (+ same
  `VAPI_KEY`). The app tries servers in order — if main 503s, it uses
  the mirror automatically.
- **Direct API users**: keep both base URLs; on HTTP 503 / timeout,
  retry the same request against the mirror.
- **Alert flow**: at 70% the agent TG-warns; at 90% it TG-orders the
  switch ("move clients to mirror now").

## Live doors (all same code + same env + same VAPI_KEY, one shared KV brain)
- main: https://ayai-vpx.vercel.app (yusgsg)
- M1: https://ayai-vpx-yusfkarim2001-1023s-projects.vercel.app
- M2: https://ayai-vpx-yusfkarim81-7952s-projects.vercel.app
- M3: https://ayai-vpx-yusfkarim994-4936s-projects.vercel.app
- M4: https://ayai-vpx-yusfkarims-projects.vercel.app

## Mirror recipe (per new account token)
1. Copy `vercel/` to clean dir (NO `.vercel/` link inside).
2. `vercel deploy --prod --token=$T --yes` (creates project).
3. `PATCH /v9/projects/{id} {"framework":null,"name":"ayai-vpx"}`
   (else new-runtime entrypoint error).
4. `vercel deploy --prod` again (Ready).
5. POST 11 env vars to `/v10/projects/{id}/env` (production, encrypted).
6. `PATCH {"ssoProtection":null}` (else 302 login wall).
7. `vercel deploy --prod` (env baked) + verify /api/status + chat.
8. Add host to vpx-ping.yml loop + push.

## Notes
- Mirror deploys from the same git repo, so every push can update both
  (`--token` per account).
- Usage counters are GLOBAL (shared gist) — dashboard shows combined %.
  Per-door split is not tracked (Vercel-side meters stay per-account).
- If BOTH doors near limits → 3rd account, same recipe.
