@echo off
title AgriChain Server
echo.
echo  ========================================
echo   AgriChain - Smart Agriculture Platform
echo  ========================================
echo.

echo [1/2] Installing dependencies...
pip install google-generativeai >nul 2>&1
echo       Done.
echo.

echo [2/2] Starting server...
echo       Open http://localhost:5000 in your browser.
echo.
python "%~dp0server.py"
pause
