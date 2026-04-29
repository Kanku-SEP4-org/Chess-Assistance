@echo off
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

title Chess Assistance - System Shutdown

echo.
echo  ==========================================
echo   Chess Assistance System - Stopping All
echo  ==========================================
echo.

REM Close named CMD windows
echo [1/3] Closing service windows...
for %%W in ("IoT-Stack" "Mock-IoT-Producer" "ML-API" "gRPC-Service" "API-Gateway" "Frontend") do (
    taskkill /f /fi "WINDOWTITLE eq %%~W" /t >nul 2>&1
)
echo        Done.
echo.

REM Kill any remaining processes on our ports
echo [2/3] Freeing ports (3000, 3001, 50051, 8000, 8080)...
call :kill_port 3000
call :kill_port 3001
call :kill_port 50051
call :kill_port 8000
call :kill_port 8080
echo        Done.
echo.

REM Stop Docker stack
echo [3/3] Stopping IoT Docker Stack (RabbitMQ + IoT gRPC)...
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    cd /d "%ROOT%\services\iot-service"
    docker-compose down
    echo        Done.
) else (
    echo        [SKIPPED] Docker not running.
)
echo.

echo  All services stopped.
echo.
pause
exit /b 0

:kill_port
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%~1 " ^| findstr "LISTENING" 2^>nul') do (
    if not "%%p"=="" taskkill /f /pid %%p >nul 2>&1
)
exit /b 0
