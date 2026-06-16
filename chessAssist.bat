:: this is specific for running the project through Windows (Powershell or Command Prompt)

@echo off
cls
echo ========================================================
echo 🚀 Starting Chess-Assistance local development setup...
echo ========================================================

:: 1. ENVIRONMENT SETUP
if not exist .env (
    echo ⚠️  No .env file detected in root folder.
    if exist .env.example (
        echo 📋 Copying .env.example to .env...
        copy .env.example .env
        echo 💡 Note: Please remember to fill in your private API secrets inside .env if needed.
    ) else (
        echo ❌ Error: Neither .env nor .env.example found! Exiting.
        exit /b 1
    )
) else (
    echo ✅ .env file verified.
)

:: 2. CONTAINERS ENVIRONMENT CLEANUP
echo.
echo 🧹 Checking for and cleaning up old Docker resources...
docker compose down --remove-orphans

:: 3. SPIN UP BACKEND SERVICES
echo.
echo 🐳 Building and spinning up core backend containers...
docker compose up --build -d

:: 4. VERIFY CONTAINER STATUS
echo.
echo ⏳ Waiting a moment for Docker service health checks...
timeout /t 3 /nobreak > nul
docker compose ps

:: 5. FRONTEND INSTALLATION & RUNTIME
echo.
echo 📦 Navigating to frontend application directory...
cd frontend\chessapp

if not exist node_modules (
    echo 📥 Installing frontend dependencies (npm install)...
    call npm install
) else (
    echo ✅ Frontend dependencies already installed. Skipping install step.
)

echo.
echo ========================================================
echo ⚡ Starting Vite Frontend Server...
echo ========================================================

call npm run dev