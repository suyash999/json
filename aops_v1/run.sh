#!/bin/bash
# ─────────────────────────────────────────────────
# eBay IAC Artifact Vault — Setup & Run Script
# ─────────────────────────────────────────────────

set -e

echo ""
echo "  ╔═══════════════════════════════════════════╗"
echo "  ║   🏛️  eBay IAC · Artifact Vault Setup     ║"
echo "  ╚═══════════════════════════════════════════╝"
echo ""

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required. Please install it first."
    exit 1
fi

echo "📦 Installing dependencies..."
pip install -r requirements.txt --quiet

echo ""
echo "✅ Dependencies installed."
echo ""
echo "🚀 Starting Artifact Vault..."
echo "   Open http://localhost:8501 in your browser"
echo ""

streamlit run app.py \
    --server.port 8501 \
    --server.headless true \
    --browser.gatherUsageStats false \
    --theme.base dark
