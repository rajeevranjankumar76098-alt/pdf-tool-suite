@echo off
echo ========================================
echo   PDF Tool Suite - Setup (Windows)
echo ========================================
echo.

:: Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python install nahi hai!
    echo Python 3.10+ yahan se download karein: https://python.org/downloads
    pause
    exit /b 1
)

echo [1/4] Python mila — pip update kar rahe hain...
python -m pip install --upgrade pip --quiet

echo [2/4] Backend dependencies install ho rahi hain...
cd /d "%~dp0backend"
pip install -r requirements.txt --quiet

if errorlevel 1 (
    echo [ERROR] Dependencies install fail hua!
    pause
    exit /b 1
)

echo [3/4] Folders create kar rahe hain...
mkdir uploads 2>nul
mkdir processed 2>nul

echo [4/4] Setup complete!
echo.
echo ========================================
echo  Ab "start.bat" run karein server start karne ke liye
echo ========================================
pause
