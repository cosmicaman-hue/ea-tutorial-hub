@echo off
REM =====================================================
REM EA Tutorial Hub - Network Setup Assistant
REM =====================================================
REM This script helps you configure your network setup
REM for 24x7 access

setlocal enabledelayedexpansion

:menu
cls
echo.
echo =====================================================
echo EA Tutorial Hub - Network Setup Assistant
echo =====================================================
echo.
echo Choose an option:
echo.
echo 1. Display Server Information
echo 2. Test Network Connectivity
echo 3. Check Port 5000 Status
echo 4. Configure Firewall
echo 5. Run Full Server Setup
echo 6. Create Backup
echo 7. Restart Server
echo 8. Exit
echo.
set /p choice=Enter your choice (1-8): 

if "%choice%"=="1" goto show_info
if "%choice%"=="2" goto test_network
if "%choice%"=="3" goto check_port
if "%choice%"=="4" goto firewall
if "%choice%"=="5" goto full_setup
if "%choice%"=="6" goto backup
if "%choice%"=="7" goto restart_server
if "%choice%"=="8" goto exit
goto menu

:show_info
cls
echo.
echo =====================================================
echo SERVER INFORMATION
echo =====================================================
echo.
echo Hostname:
hostname
echo.
echo IP Address(es):
ipconfig | findstr /R "IPv4.*:" 
echo.
echo Access URLs:
for /f "tokens=2 delims=: " %%A in ('ipconfig ^| findstr /R "IPv4.*192"') do (
    echo   Main: http://%%A:5000
    echo   Login: http://%%A:5000/auth/login
    echo   Admin: http://%%A:5000/admin/dashboard
)
echo.
echo Database Location:
if exist "instance\ea_tutorial.db" (
    echo   ✅ Found: instance\ea_tutorial.db
    for %%A in (instance\ea_tutorial.db) do echo   Size: %%~zA bytes
) else (
    echo   ❌ Not found (will be created on first run)
)
echo.
echo Python Installation:
python --version
echo.
pause
goto menu

:test_network
cls
echo.
echo =====================================================
echo NETWORK CONNECTIVITY TEST
echo =====================================================
echo.

REM Get server IP
for /f "tokens=2 delims=: " %%A in ('ipconfig ^| findstr /R "IPv4.*192"') do (
    set SERVER_IP=%%A
)

if "%SERVER_IP%"=="" (
    echo ❌ Could not determine server IP
    echo Please check your network connection
    pause
    goto menu
)

echo Server IP: %SERVER_IP%
echo.
echo Testing localhost (this PC):
python -c "import requests; print('✅ localhost:5000 OK' if requests.get('http://localhost:5000', timeout=3).status_code else '❌ Failed')" 2>nul || echo ❌ Failed to connect

echo.
echo Testing from external interface:
python -c "import requests; print('✅ %SERVER_IP%:5000 OK' if requests.get('http://%SERVER_IP%:5000', timeout=3).status_code else '❌ Failed')" 2>nul || echo ❌ Failed to connect

echo.
echo To test from another PC on your network:
echo   ping %SERVER_IP%
echo   Or visit: http://%SERVER_IP%:5000
echo.
pause
goto menu

:check_port
cls
echo.
echo =====================================================
echo PORT 5000 STATUS
echo =====================================================
echo.
echo Checking what's using port 5000...
echo.
netstat -ano | findstr :5000 >nul
if %errorlevel%==0 (
    echo ✅ Port 5000 is in use:
    echo.
    netstat -ano | findstr :5000
    echo.
    echo Process details:
    for /f "tokens=5" %%A in ('netstat -ano ^| findstr :5000') do (
        tasklist | findstr %%A
    )
) else (
    echo ⚠️ Port 5000 is NOT in use
    echo Either the server is not running, or it's using a different port
)
echo.
pause
goto menu

:firewall
cls
echo.
echo =====================================================
echo FIREWALL CONFIGURATION
echo =====================================================
echo.
echo Attempting to enable Python through Windows Firewall...
echo.
echo If you see a security prompt, click "Yes"
echo.
pause
netsh advfirewall firewall add rule name="Python - EA Tutorial Hub" dir=in action=allow program="%PYTHON%" enable=yes >nul 2>&1
echo ✅ Firewall rule added (if user had admin rights)
echo.
echo Manual steps if auto-add didn't work:
echo   1. Open: Windows Defender Firewall > Allow an app
echo   2. Click: "Allow another app"
echo   3. Browse to: .\.venv\Scripts\python.exe
echo   4. Check: Private (for home network)
echo   5. Click: OK
echo.
pause
goto menu

:full_setup
cls
echo.
echo =====================================================
echo FULL SERVER SETUP
echo =====================================================
echo.
python server_setup.py
echo.
pause
goto menu

:backup
cls
echo.
echo =====================================================
echo DATABASE BACKUP
echo =====================================================
echo.

if not exist "instance\ea_tutorial.db" (
    echo ❌ Database file not found!
    echo The application may not have been run yet.
    pause
    goto menu
)

echo Creating backup...
set TIMESTAMP=%date:~-4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set BACKUP_FILE=instance\ea_tutorial.db.backup_%TIMESTAMP%

copy "instance\ea_tutorial.db" "%BACKUP_FILE%" >nul

if %errorlevel%==0 (
    echo ✅ Backup created successfully!
    echo   Original: instance\ea_tutorial.db
    echo   Backup: %BACKUP_FILE%
) else (
    echo ❌ Backup failed!
)
echo.
pause
goto menu

:restart_server
cls
echo.
echo =====================================================
echo RESTART SERVER
echo =====================================================
echo.
echo Restarting the application server...
echo.

if exist ".venv" (
    .\.venv\Scripts\Activate.ps1
    python run.py
) else (
    echo ❌ Virtual environment not found!
    echo Please run 'Full Server Setup' first
    pause
)

goto menu

:exit
cls
echo.
echo Goodbye!
echo.
exit /b 0
