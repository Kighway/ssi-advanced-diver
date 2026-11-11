#!/bin/sh
set -eu

# Railway supplies PORT. Local Docker runs default to 8501.
# CLI options override the local-only address in .streamlit/config.toml.
exec python -m streamlit run app.py \
    --server.address=0.0.0.0 \
    --server.port="${PORT:-8501}" \
    --server.headless=true \
    --server.fileWatcherType=none \
    --server.runOnSave=false \
    --browser.gatherUsageStats=false
