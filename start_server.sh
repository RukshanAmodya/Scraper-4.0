#!/bin/bash
# =======================================================
# Faymas AI Prompt & Image 24/7 Scraper - Linux Launcher
# =======================================================

set -e

echo "=== Setting up Faymas Scraper Environment ==="

# Check Python3
if ! command -v python3 &> /dev/null; then
    echo "[!] python3 not found. Installing python3 and venv..."
    sudo apt update && sudo apt install -y python3 python3-pip python3-venv
fi

# Create virtual environment if not present
if [ ! -d "venv" ]; then
    echo "[*] Creating virtual environment (venv)..."
    python3 -m venv venv
fi

# Activate venv & install dependencies
source venv/bin/activate
echo "[*] Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "=== Starting 24/7 Continuous Daemon ==="
echo "[*] Press CTRL+C to stop the daemon gracefully."
python faymas_scraper.py --daemon --interval 60
