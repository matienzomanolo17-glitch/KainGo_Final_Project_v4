@echo off
REM ONE-TIME setup: connects XAMPP's Apache to the KainGo website so it opens at http://localhost
set XAMPP=C:\xampp
if not exist "%XAMPP%\apache\conf\httpd.conf" set /p XAMPP=Type your XAMPP folder path and press Enter: 
if not exist "%XAMPP%\apache\conf\httpd.conf" goto notfound

copy /Y "%~dp0apache\kaingo-proxy.conf" "%XAMPP%\apache\conf\extra\kaingo-proxy.conf" >nul
findstr /C:"kaingo-proxy.conf" "%XAMPP%\apache\conf\httpd.conf" >nul
if errorlevel 1 (
    echo.>> "%XAMPP%\apache\conf\httpd.conf"
    echo Include conf/extra/kaingo-proxy.conf>> "%XAMPP%\apache\conf\httpd.conf"
)
echo.
echo Done. Now open the XAMPP Control Panel, then Stop and Start Apache.
echo After that, run start_kaingo.bat and open http://localhost
pause
exit /b

:notfound
echo Could not find XAMPP. Please check the folder path and run this file again.
pause
