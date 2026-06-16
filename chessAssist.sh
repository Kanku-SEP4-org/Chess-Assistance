#!/bin/bash
set -e
clear

echo "========================================================"
echo "🚀 Starting Chess-Assistance local development setup..."
echo "========================================================"

# 1. ENVIRONMENT SETUP
if [ ! -f .env ]; then
    echo "⚠️  No .env file detected in root folder. Copying template..."
    cp .env.example .env
fi

# 2. CONTAINERS ENVIRONMENT REBOOT
echo -e "\n🧹 Re-building and spinning up Docker microservices..."
docker compose down --remove-orphans
docker compose up --build -d

# 3. SHOW RUNNING CONTAINERS
echo -e "\n⏳ Checking container cluster health status..."
sleep 2
docker compose ps

# 4. FRONTEND INSTALLATION & RUNTIME
echo -e "\n📦 Setting up frontend web application..."

# Store our home root path so we don't get lost in folder layers
ROOT_DIR=$(pwd)

cd frontend/chessapp

if [ ! -d "node_modules" ]; then
    echo "📥 Installing frontend dependencies..."
    npm install
fi

echo -e "\n========================================================"
echo "⚡ Starting Vite Frontend Server..."
echo "💻 Environment fully operational at: http://localhost:5173"
echo "👉 OPEN A NEW SEPARATE WSL TERMINAL WINDOW TO RUN: ./launchSensorClient.sh"
echo "========================================================"

# This command takes over this terminal window permanently
npm run dev

# to enable this script to be used, first run `chmod +x chessAssist.sh` in the terminal to make it executable.
# afterwards,in Git bash, run the script with `./chessAssist.sh` from the root directory of the project.