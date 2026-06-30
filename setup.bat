@echo off
REM ============================================================================
REM AI-Enhanced Intrusion Detection System - Quick Setup (Windows)
REM ============================================================================

echo.
echo ============================================================
echo  AI-ENHANCED INTRUSION DETECTION SYSTEM
echo  Windows Quick Setup Script
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [!] Python is not installed or not in PATH
    echo [!] Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

echo [+] Python found
python --version

REM Step 1: Install dependencies
echo.
echo [*] Step 1: Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo [!] Failed to install dependencies
    pause
    exit /b 1
)
echo [OK] Dependencies installed

REM Step 2: Train model
echo.
echo [*] Step 2: Training ML model (this may take a minute)...
python ml\train_model.py
if errorlevel 1 (
    echo [!] Failed to train model
    pause
    exit /b 1
)
echo [OK] Model trained successfully

REM Step 3: Start backend
echo.
echo ============================================================
echo [+] Setup complete! Starting backend server...
echo ============================================================
echo.
echo [OK] Dashboard will be available at: http://localhost:5000
echo [OK] Press Ctrl+C to stop the server
echo.

python backend\main.py
pause
