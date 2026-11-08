@echo off
setlocal
if not exist "%~dp0index.html" (
  echo 未找到 index.html，请确认本文件与 index.html 在同一文件夹中。
  pause
  exit /b 1
)
start "" "%~dp0index.html"
endlocal
