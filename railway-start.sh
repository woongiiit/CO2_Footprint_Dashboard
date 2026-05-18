#!/usr/bin/env sh
set -e

# Railway Root Directory가 repo 루트이면 workspace/app 으로 이동
if [ -f workspace/app/app.py ]; then
  cd workspace/app
fi

exec streamlit run app.py \
  --server.port="$PORT" \
  --server.address=0.0.0.0 \
  --server.headless=true \
  --browser.gatherUsageStats=false
