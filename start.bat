@echo off
chcp 65001 >nul
title HXZ - Henan University AI Campus
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 pause
