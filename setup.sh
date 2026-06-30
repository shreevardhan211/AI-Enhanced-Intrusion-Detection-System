#!/bin/bash
# ============================================================================
# AI-Enhanced Intrusion Detection System - Quick Setup (macOS/Linux)
# ============================================================================

echo ""
echo "============================================================"
echo "  AI-ENHANCED INTRUSION DETECTION SYSTEM"
echo "  macOS/Linux Quick Setup Script"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[!] Python 3 is not installed"
    echo "[!] Please install Python 3.8+ using:"
    echo "    brew install python3  (macOS)"
    echo "    sudo apt install python3 python3-pip  (Linux)"
    exit 1
fi

echo "[+] Python found"
python3 --version

# Step 1: Create virtual environment (optional but recommended)
echo ""
echo "[*] Step 1: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "[OK] Virtual environment created"
else
    echo "[OK] Virtual environment already exists"
fi

# Activate virtual environment
source venv/bin/activate
echo "[OK] Virtual environment activated"

# Step 2: Install dependencies
echo ""
echo "[*] Step 2: Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "[!] Failed to install dependencies"
    exit 1
fi
echo "[OK] Dependencies installed"

# Step 3: Train model
echo ""
echo "[*] Step 3: Training ML model (this may take a minute)..."
python ml/train_model.py
if [ $? -ne 0 ]; then
    echo "[!] Failed to train model"
    exit 1
fi
echo "[OK] Model trained successfully"

# Step 4: Start backend
echo ""
echo "============================================================"
echo "[+] Setup complete! Starting backend server..."
echo "============================================================"
echo ""
echo "[OK] Dashboard will be available at: http://localhost:5000"
echo "[OK] Press Ctrl+C to stop the server"
echo ""

python backend/main.py
