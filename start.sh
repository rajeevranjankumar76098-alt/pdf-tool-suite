#!/bin/bash
echo "========================================"
echo "  PDF Tool Suite — Starting..."
echo "========================================"
echo
echo "Backend API : http://localhost:8000"
echo "Frontend UI : frontend/index.html ko browser mein open karein"
echo
echo "Server band karne ke liye: Ctrl+C"
echo
cd "$(dirname "$0")/backend"
python3 main.py
