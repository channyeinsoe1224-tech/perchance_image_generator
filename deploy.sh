#!/usr/bin/env bash
# ==============================================================================
# Perchance AI Studio — Ubuntu / Debian VPS Deployment Script
# ==============================================================================
set -e

echo "=========================================================="
echo "  Deploying Perchance AI Studio on VPS"
echo "=========================================================="

# 1. Update packages and install system prerequisites
sudo apt-get update -y
sudo apt-get install -y python3 python3-pip python3-venv git curl

# 2. Setup Python virtual environment
if [ ! -d "venv" ]; then
    echo "[+] Creating Python virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# 3. Upgrade pip and install requirements
echo "[+] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# 4. Install Playwright browser and system dependencies
echo "[+] Installing Playwright Chromium & system libraries..."
playwright install-deps chromium
playwright install chromium

# 5. Install package in editable mode
pip install -e .

# 6. Ensure runtime directories exist
mkdir -p data/browser_profile static/outputs

echo "=========================================================="
echo "  Installation Complete!"
echo "  To start the server manually:"
echo "    source venv/bin/activate && python run_webapp.py"
echo "=========================================================="
