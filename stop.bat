@echo off
chcp 65001 >nul
title HXZ - Stop Server
cd /d "%~dp0"
echo.
echo   ============================================
echo    河小智 . 停止本地服务 (port 8501)
echo   ============================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop.ps1"
echo.
pause
