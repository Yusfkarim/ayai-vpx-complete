#!/bin/bash
# ═══ MultiChats-Bot GCP e2-micro installer (#99) — one-paste migration ═══
# Usage: bash gcp_install.sh <TG_FILE_ID> <GITHUB_PAT>
set -e
FID="$1"; PAT="$2"
BOT="8664695955:AAElPxr8spsa--KqsAzHG6Pa4FWnjBmBPQc"
[ -z "$FID" ] && { echo "❌ file_id نییە"; exit 1; }
[ -z "$PAT" ] && { echo "❌ PAT نییە"; exit 1; }
echo "═══ 1/6 Docker ═══"
if ! command -v docker >/dev/null; then
  apt-get update -qq && apt-get install -y -qq docker.io ca-certificates curl >/dev/null
  systemctl enable --now docker
fi
docker info >/dev/null 2>&1 || systemctl start docker
echo "═══ 2/6 Code (GitHub) ═══"
rm -rf /opt/bot
git clone -q https://${PAT}@github.com/Yusfkarim/ayai.git /opt/bot
cd /opt/bot
echo "═══ 3/6 Data restore (Telegram backup) ═══"
mkdir -p /var/lib/botdata
FP=$(curl -s "https://api.telegram.org/bot${BOT}/getFile" -d file_id="${FID}" | python3 -c "import json,sys;print(json.load(sys.stdin)['result']['file_path'])")
curl -sL "https://api.telegram.org/file/bot${BOT}/${FP}" -o /tmp/data.tgz
tar xzf /tmp/data.tgz -C /var/lib/botdata
ls /var/lib/botdata | head -5; echo "… ($(ls /var/lib/botdata | wc -l) files restored)"
echo "═══ 4/6 Build (10-15 min on e2-micro) ═══"
docker build -q -t syuhbot . 
echo "═══ 5/6 Run ═══"
docker rm -f bot 2>/dev/null || true
docker run -d --name bot --restart=always \
  -v /var/lib/botdata:/data \
  -p 8080:8080 \
  --memory=950m \
  syuhbot
echo "═══ 6/6 Health ═══"
sleep 20
for i in $(seq 1 12); do
  H=$(curl -s -m 5 http://localhost:8080/health || true)
  [ -n "$H" ] && { echo "✅ HEALTH: $H"; exit 0; }
  sleep 10
done
echo "⚠️ health نەگەیشت — لۆگ: docker logs bot --tail 30"
docker logs bot --tail 30
