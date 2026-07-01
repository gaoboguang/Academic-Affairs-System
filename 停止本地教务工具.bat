@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo 正在停止本地教务工具...
call npm run stop:local
pause
