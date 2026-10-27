@echo off
cd /d "%~dp0"
where py >nul 2>nul && (py -3 kiosk_server.py %*) || (python kiosk_server.py %*)
pause
