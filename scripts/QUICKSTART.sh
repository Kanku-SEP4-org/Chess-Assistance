#!/bin/bash
# Quick Start Script - Run this to set up and start all services

echo "=========================================="
echo "Chess Assistance - IoT to React Connection"
echo "=========================================="
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Step 1: Start ML API${NC}"
echo "Run in a new terminal:"
echo "  cd machine_learning/api"
echo "  source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "  pip install -r requirements.txt"
echo "  uvicorn main:app --reload"
echo ""

echo -e "${YELLOW}Step 2: Start gRPC Service${NC}"
echo "Run in a new terminal:"
echo "  cd services/grpc-service"
echo "  npm install"
echo "  node server.js"
echo ""

echo -e "${YELLOW}Step 3: Start API Gateway${NC}"
echo "Run in a new terminal:"
echo "  cd api-gateway"
echo "  npm install"
echo "  node server.js"
echo ""

echo -e "${YELLOW}Step 4: Start React Frontend${NC}"
echo "Run in a new terminal:"
echo "  cd frontend/chessapp"
echo "  npm install"
echo "  npm run dev"
echo ""

echo -e "${GREEN}=========================================="
echo "Expected Ports:"
echo "  ML API: http://localhost:8000"
echo "  gRPC Service: localhost:50051"
echo "  API Gateway: http://localhost:3001"
echo "  React App: http://localhost:5173"
echo "==========================================${NC}"
echo ""

echo -e "${YELLOW}ONE-TIME SETUP (if not done before):${NC}"
echo "Run the ML trainer to generate model files:"
echo "  cd machine_learning/trainer"
echo "  source venv/bin/activate  # or venv\\Scripts\\activate on Windows"
echo "  pip install -r requirements.txt"
echo "  python run_pipeline.py"
echo ""

echo -e "${GREEN}Ready to go!${NC}"
