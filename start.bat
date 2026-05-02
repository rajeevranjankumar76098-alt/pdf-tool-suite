@echo off
echo ========================================
echo   PDF Tool Suite — Starting...
echo ========================================
echo.
echo Backend API: http://localhost:8000
echo Frontend UI: frontend/index.html ko browser mein open karein
echo.
echo Server band karne ke liye: Ctrl+C dabayein
echo.
cd /d "%~dp0backend"
python main.py
