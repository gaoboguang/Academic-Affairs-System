@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在启动本地教务工具...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\start-local-windows.ps1"
echo.
echo 如需停止服务，请双击“停止本地教务工具.bat”。
pause
