#!/usr/bin/env bash
set -euo pipefail
HOST="root@drugoi.xyz"
DEST="/opt/myvision"

rsync -az --delete \
  --exclude '.venv/' --exclude 'posts/' --exclude 'docs/' \
  --exclude '.git/' --exclude '__pycache__/' --exclude '.pytest_cache/' \
  ./ "$HOST:$DEST/"

ssh "$HOST" "cd $DEST && docker compose up -d --build && nginx -t && systemctl reload nginx"
echo "Deployed. Remember TLS: certbot --nginx -d myvision.drugoi.xyz"
