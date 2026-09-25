#!/bin/bash
# #122: sync vercel/api + vercel/lib into functions/ (Firebase door mirrors Vercel code)
set -e
cd "$(dirname "$0")"
rm -rf functions/api functions/lib
mkdir -p functions/api functions/lib
cp -r vercel/api/. functions/api/
cp -r vercel/lib/. functions/lib/
find functions/api functions/lib -name "__pycache__" -type d -prune -exec rm -rf {} + 2>/dev/null
find functions/api functions/lib -name "*.pyc" -delete 2>/dev/null
echo "synced: $(ls functions/api/*.py | wc -l) api + $(ls functions/lib/*.py | wc -l) lib"
