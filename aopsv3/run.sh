#!/bin/bash
set -e
echo ""
echo "  eBay IAC - Artifact Vault"
echo "  Installing dependencies..."
pip install -r requirements.txt --quiet
echo "  Done. Launching at http://localhost:8501"
echo ""
streamlit run app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false
