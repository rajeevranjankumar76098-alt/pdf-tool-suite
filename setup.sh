#!/bin/bash
echo "========================================"
echo "  PDF Tool Suite - Setup (Linux/Mac)"
echo "========================================"
echo

# Check Python
if ! command -v python3 &>/dev/null; then
    echo "[ERROR] Python3 install nahi hai!"
    echo "Ubuntu/Debian:  sudo apt install python3 python3-pip"
    echo "Mac:            brew install python"
    exit 1
fi

echo "[1/5] Python mila: $(python3 --version)"

echo "[2/5] pip update..."
python3 -m pip install --upgrade pip -q

echo "[3/5] Backend dependencies install ho rahi hain..."
cd "$(dirname "$0")/backend"
pip3 install -r requirements.txt -q

if [ $? -ne 0 ]; then
    echo "[ERROR] Dependencies install fail hua!"
    exit 1
fi

echo "[4/5] Folders create kar rahe hain..."
mkdir -p uploads processed

echo "[5/5] Permissions set kar rahe hain..."
chmod +x ../start.sh

echo
echo "========================================"
echo " Setup complete! Ab './start.sh' chalayein"
echo "========================================"
