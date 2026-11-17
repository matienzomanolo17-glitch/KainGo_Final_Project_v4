@echo off
REM Starts the KainGo website. Keep this window open while you use the site.
REM First start Apache and MySQL in the XAMPP Control Panel, then open http://localhost
cd /d "%~dp0"
python app.py
pause
