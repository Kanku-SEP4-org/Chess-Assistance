@echo off
setlocal EnableDelayedExpansion

set "ROOT=%~dp0"
set "ROOT=%ROOT:~0,-1%"

title Chess Assistance - System Startup

echo.
echo  ==========================================
echo   Chess Assistance System - Starting All
echo  ==========================================
echo.

REM ── STOP PHASE ────────────────────────────────────────────────────
echo [STOP] Cleaning up any running services...

REM Close named windows from a previous run
for %%W in ("IoT-Stack" "Mock-IoT-Producer" "ML-API" "gRPC-Service" "API-Gateway" "Frontend") do (
    taskkill /f /fi "WINDOWTITLE eq %%~W" /t >nul 2>&1
)

REM Kill anything still holding our ports
call :kill_port 3000
call :kill_port 3001
call :kill_port 50051
call :kill_port 8000
call :kill_port 8080

REM Stop Docker IoT stack if Docker is running
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    cd /d "%ROOT%\services\iot-service"
    docker-compose down >nul 2>&1
    cd /d "%ROOT%"
)

echo        Done. Waiting 3 s for ports to free...
timeout /t 3 /nobreak >nul
echo.

REM ── PREREQUISITES CHECK ───────────────────────────────────────────
echo [CHECK] Verifying prerequisites...

where node >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Node.js not found. Install from https://nodejs.org
    pause & exit /b 1
)

REM Docker
set "DOCKER_OK=0"
docker info >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "DOCKER_OK=1"
    echo [OK]   Docker is running.
) else (
    echo [WARN] Docker not running -- IoT stack will be SKIPPED.
    echo        Start Docker Desktop and re-run to include IoT + RabbitMQ.
)

REM ML model files
set "ML_MODELS_OK=0"
if exist "%ROOT%\machine_learning\trainer\models\model.pkl" (
    if exist "%ROOT%\machine_learning\trainer\models\scaler.pkl" (
        set "ML_MODELS_OK=1"
        echo [OK]   ML model files found.
    )
)
if "%ML_MODELS_OK%"=="0" (
    echo [WARN] ML model files missing. Run trainer first:
    echo          cd machine_learning\trainer ^&^& python run_pipeline.py
    echo        ML API will be SKIPPED until models exist.
)

REM uvicorn: venv > global PATH > python -m uvicorn
set "UVICORN_CMD="
set "VENV_ACTIVATE="
if exist "%ROOT%\machine_learning\api\venv\Scripts\activate.bat" (
    set "VENV_ACTIVATE=%ROOT%\machine_learning\api\venv\Scripts\activate.bat"
    set "UVICORN_CMD=uvicorn"
    echo [OK]   Python venv found.
) else (
    where uvicorn >nul 2>&1
    if !ERRORLEVEL! EQU 0 (
        set "UVICORN_CMD=uvicorn"
        echo [OK]   uvicorn found in PATH.
    ) else (
        python -m uvicorn --version >nul 2>&1
        if !ERRORLEVEL! EQU 0 (
            set "UVICORN_CMD=python -m uvicorn"
            echo [OK]   python -m uvicorn found.
        ) else (
            echo [WARN] uvicorn not found. ML API will be SKIPPED.
            echo        Install: pip install uvicorn fastapi joblib scikit-learn pandas
        )
    )
)

REM dotnet SDK for mock producer
set "DOTNET_OK=0"
where dotnet >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set "DOTNET_OK=1"
    echo [OK]   dotnet SDK found.
) else (
    echo [WARN] dotnet SDK not found -- Mock IoT Producer will be SKIPPED.
)

echo.
timeout /t 1 /nobreak >nul

REM ── START PHASE ───────────────────────────────────────────────────

REM 1. IoT Stack (RabbitMQ + IoT gRPC via Docker)
echo [1/6] IoT Stack (RabbitMQ :5672/:15672 + IoT gRPC :8080)...
if "%DOCKER_OK%"=="1" (
    start "IoT-Stack" cmd /k "title IoT-Stack && cd /d "%ROOT%\services\iot-service" && docker-compose up rabbitmq grpc-server"
    echo        Waiting 20 s for RabbitMQ and IoT gRPC to initialize...
    timeout /t 20 /nobreak >nul
    echo        [STARTED]
) else (
    echo        [SKIPPED] Docker not available
)
echo.

REM 2. Mock IoT Producer
echo [2/6] Mock IoT Producer (sensor data via RabbitMQ)...
if "%DOCKER_OK%"=="1" (
    if "%DOTNET_OK%"=="1" (
        start "Mock-IoT-Producer" cmd /k "title Mock-IoT-Producer && cd /d "%ROOT%\services\iot-service\Mock_IoT_Producer" && set RABBITMQ_URL=amqp://guest:guest@localhost:5672 && dotnet run"
        timeout /t 5 /nobreak >nul
        echo        [STARTED]
    ) else (
        echo        [SKIPPED] dotnet SDK not found
    )
) else (
    echo        [SKIPPED] RabbitMQ not available
)
echo.

REM 3. ML API (FastAPI)
echo [3/6] ML API (FastAPI :8000)...
if not "%UVICORN_CMD%"=="" (
    if "%ML_MODELS_OK%"=="1" (
        if not "%VENV_ACTIVATE%"=="" (
            start "ML-API" cmd /k "title ML-API && cd /d "%ROOT%\machine_learning\api" && call "%VENV_ACTIVATE%" && %UVICORN_CMD% main:app --host 0.0.0.0 --port 8000"
        ) else (
            start "ML-API" cmd /k "title ML-API && cd /d "%ROOT%\machine_learning\api" && %UVICORN_CMD% main:app --host 0.0.0.0 --port 8000"
        )
        timeout /t 5 /nobreak >nul
        echo        [STARTED]
    ) else (
        echo        [SKIPPED] Model files missing
    )
) else (
    echo        [SKIPPED] uvicorn not found
)
echo.

REM 4. gRPC Service (Node.js)
echo [4/6] gRPC Service (Node.js :50051)...
start "gRPC-Service" cmd /k "title gRPC-Service && cd /d "%ROOT%\services\grpc-service" && node server.js"
timeout /t 3 /nobreak >nul
echo        [STARTED]
echo.

REM 5. API Gateway (Express)
echo [5/6] API Gateway (Express :3001)...
start "API-Gateway" cmd /k "title API-Gateway && cd /d "%ROOT%\api-gateway" && node server.js"
timeout /t 3 /nobreak >nul
echo        [STARTED]
echo.

REM 6. React Frontend
echo [6/6] React Frontend (:3000)...
start "Frontend" cmd /k "title Frontend && cd /d "%ROOT%\frontend\chessapp" && npm start"
echo        [STARTING] React may take ~30 s to compile
echo.

echo  ==========================================
echo   All services launched
echo  ==========================================
echo.
echo   Service                URL
echo   ─────────────────────────────────────────
echo   RabbitMQ Management    http://localhost:15672  (guest/guest)
echo   ML API (Swagger)       http://localhost:8000/docs
echo   IoT gRPC Service       localhost:8080
echo   gRPC Service           localhost:50051
echo   API Gateway            http://localhost:3001
echo   React Frontend         http://localhost:3000
echo   ─────────────────────────────────────────
echo.
echo   Run stop-all.bat to shut everything down cleanly.
echo.
pause
exit /b 0

REM ── Subroutine ────────────────────────────────────────────────────
:kill_port
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%~1 " ^| findstr "LISTENING" 2^>nul') do (
    if not "%%p"=="" taskkill /f /pid %%p >nul 2>&1
)
exit /b 0
