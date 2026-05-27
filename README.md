# Chess-Assistance

A full-stack IoT and Machine Learning platform that helps chess players understand how their physical environment and health habits affect their game performance. The system collects real-time sensor data (temperature, humidity, CO2, light), tracks player wellness (sleep, water intake, activity), imports game data from Lichess, and uses trained ML models to predict win rates, detect tilt/angriness, estimate move accuracy, and recommend optimal playing conditions.

Built as a SEP4 semester project (Internet of Things) by a 14-person team.

## Table of Contents

- [Key Features](#key-features)
- [Tech Stack](#tech-stack)
- [Architecture Overview](#architecture-overview)
- [Prerequisites](#prerequisites)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [Available Scripts](#available-scripts)
- [Project Structure](#project-structure)
- [CI/CD Pipeline](#cicd-pipeline)
- [Deployment Architecture](#deployment-architecture)
- [Testing](#testing)
- [Contributing](#contributing)

## Key Features

- **Lichess OAuth Integration** -- sign in with a Lichess account and automatically import game history, ratings, and opening data
- **IoT Environmental Monitoring** -- Arduino-based sensors (ATmega2560) measure temperature, humidity, CO2, and ambient light during chess sessions
- **Health Tracking** -- record sleep duration, water intake, and physical activity for each session
- **Win Rate Prediction** -- ML model correlates environment and health metrics with game outcomes to predict win probability
- **Angriness/Tilt Detection** -- predicts player emotional state from game patterns (blunders, time usage, consecutive losses)
- **Accuracy Prediction** -- estimates centipawn loss per game based on player profile, opening choice, and opponent data
- **Factor Impact Analysis** -- ranks which factors (sleep, CO2, temperature, etc.) most influence chess performance
- **Environment Recommendations** -- suggests optimal room conditions to maximize playing quality
- **Session Management** -- start and end chess sessions that tie together health records, sensor readings, and games played
- **Player Preferences** -- configurable limits for daily games, play time, break intervals, and rest recommendations

## Tech Stack

| Layer | Technology | Details |
|-------|-----------|---------|
| Frontend | React 19, Vite 8, Bootstrap 5, Sass | SPA with Lichess OAuth, deployed to Cloudflare Pages |
| API Gateway | Node.js 18, Express 5 | REST-to-gRPC proxy with JWT cookie auth |
| Lichess API Service | C# .NET 10, gRPC | Fetches and stores Lichess game data, manages sessions |
| IoT Service | C# .NET 10, gRPC | Receives sensor data via RabbitMQ, serves readings |
| ML API | Python 3.11, FastAPI | Serves 4 trained ML models with JWT-protected endpoints |
| Database | PostgreSQL 17 | `chess_assistant` schema with custom enums, computed columns, triggers |
| Message Queue | RabbitMQ | Async sensor data ingestion from IoT devices |
| IoT Client | C / Arduino / PlatformIO | ATmega2560-based sensor hardware |
| Shared Contracts | Protocol Buffers | `IoT.proto` and `LichessApi.proto` gRPC service definitions |

## Architecture Overview

The platform follows a microservices architecture with gRPC as the internal communication protocol:

1. **Frontend** (`chess.cannyboiz.com`) -- React SPA hosted on Cloudflare Pages. All API calls go to `api-chess.cannyboiz.com`.

2. **Caddy Reverse Proxy** -- routes incoming requests on `api-chess.cannyboiz.com`:
   - ML endpoints (`/predictions/*`, `/recommendations/*`, `/angriness/*`, `/accuracy/*`, `/factor-impact/*`, `/health`) are forwarded to the **ML API** on port 8000
   - All other requests are forwarded to the **API Gateway** on port 3001

3. **API Gateway** (Express) -- translates REST requests into gRPC calls to the Lichess API Service (port 8082) and IoT Service (port 8080). Handles JWT authentication and session cookies.

4. **Lichess API Service** (C# gRPC) -- manages player registration, Lichess OAuth token exchange, session lifecycle, and game data import/storage in PostgreSQL.

5. **IoT Service** (C# gRPC) -- consumes sensor readings from RabbitMQ queues (`sensor.requests` / `sensor.responses`) and persists them to PostgreSQL. Serves sensor data to the gateway on request.

6. **ML API** (FastAPI) -- loads pre-trained scikit-learn models at startup and exposes prediction endpoints. Also queries PostgreSQL directly for dataset construction and Lichess data enrichment.

7. **IoT Hardware** -- Arduino sensors (ATmega2560) publish readings to RabbitMQ via a C client over the network.

The two gRPC contracts live in `shared/`: `IoT.proto` defines sensor recording control and data retrieval; `LichessApi.proto` defines player registration, session management, and game queries.

## Prerequisites

**Required (Docker-based development):**
- [Docker](https://docs.docker.com/get-docker/) and Docker Compose v2+

**Optional (for developing individual services outside Docker):**
- Node.js 20+ and npm (frontend and API gateway)
- .NET 10 SDK (Lichess API Service and IoT Service)
- Python 3.11 (ML API and training pipelines)
- PlatformIO CLI (Arduino/IoT sensor builds)
- CMake and a C compiler (IoT C client unit tests)

## Getting Started

### 1. Clone the Repository

```bash
git clone https://github.com/Kanku-SEP4-org/Chess-Assistance.git
cd Chess-Assistance
```

### 2. Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in all values. See the [Environment Variables](#environment-variables) section for descriptions and examples.

### 3. Start Backend Services with Docker Compose

```bash
docker compose up --build
```

This starts six services:

| Service | Port | Description |
|---------|------|-------------|
| PostgreSQL | 5433 | Database (mapped from container port 5432) |
| RabbitMQ | 5672, 15672 | Message broker + management UI |
| IoT Service | 8080 | gRPC sensor data server |
| ML API | 8000 | FastAPI prediction server |
| Lichess API | 8082 | gRPC Lichess data server |
| API Gateway | 3001 | REST-to-gRPC proxy |

The ML API Docker image trains all 4 models during the build stage, so the first build takes longer than subsequent ones.

### 4. Start the Frontend

In a separate terminal:

```bash
cd frontend/chessapp
npm install
npm run dev
```

The frontend will be available at [http://localhost:5173](http://localhost:5173).

### 5. Verify Everything Works

- Frontend: [http://localhost:5173](http://localhost:5173)
- API Gateway: [http://localhost:3001](http://localhost:3001)
- ML API health check: [http://localhost:8000/health](http://localhost:8000/health)
- RabbitMQ management: [http://localhost:15672](http://localhost:15672) (guest/guest in dev)

## Environment Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `POSTGRES_DB` | PostgreSQL database name | `chess_postgres` |
| `POSTGRES_USER` | PostgreSQL username | `chess` |
| `POSTGRES_PASSWORD` | PostgreSQL password | *(set a strong password)* |
| `CONNECTIONSTRINGS__DEFAULTCONNECTION` | .NET connection string for PostgreSQL | `Host=postgres;Port=5432;Database=chess_postgres;Username=chess;Password=yourpassword` |
| `RABBITMQ_USERNAME` | RabbitMQ username | `guest` *(dev only)* |
| `RABBITMQ_PASSWORD` | RabbitMQ password | `guest` *(dev only)* |
| `FRONTEND_URL` | Frontend origin for CORS | `http://localhost:5173` |
| `LICHESS_REDIRECT_URI` | OAuth callback URL | `http://localhost:5173/callback` |
| `JWT_SECRET` | Secret for signing JWT session tokens | *(set a strong random string)* |

## Available Scripts

### Root

| Command | Description |
|---------|-------------|
| `npm start` | Starts API Gateway, gRPC service, and frontend concurrently |

### Frontend (`frontend/chessapp/`)

| Command | Description |
|---------|-------------|
| `npm run dev` | Start Vite dev server (port 5173) |
| `npm run build` | Production build |
| `npm run preview` | Preview production build locally |
| `npm run test` | Run Vitest in watch mode |
| `npm run test:coverage` | Run Vitest with coverage report |

### ML Helper Scripts (`scripts/ml/`)

| Command | Description |
|---------|-------------|
| `python run_all.py` | Set up venv, clean artifacts, train all models, start FastAPI |
| `python clean_data.py` | Remove generated training data |
| `python clean_models.py` | Remove trained model artifacts |

### Database (`scripts/databases/`)

| File | Description |
|------|-------------|
| `init.sql` | Full schema creation (auto-loaded by Docker on first run) |
| `triggers.sql` | Database triggers (auto-loaded by Docker on first run) |
| `migrations/` | Incremental SQL migration files (applied during CI/CD deployment) |

## Project Structure

```
Chess-Assistance/
├── api-gateway/                  # Node.js/Express REST-to-gRPC proxy
├── frontend/chessapp/            # React 19 + Vite 8 SPA
├── infrastructure/               # Caddy reverse proxy config (chess.Caddyfile)
├── internet_of_things/
│   ├── Sensors/                  # PlatformIO project (ATmega2560 Arduino)
│   ├── sensor_client_c/          # C sensor client with CMake build + unit tests
│   └── mock_sensor_c/            # Mock sensor for testing without hardware
├── machine_learning/
│   ├── api/                      # FastAPI serving 4 ML models
│   └── trainers/                 # Training pipelines
│       ├── trainer-winrate/      #   Win rate prediction model
│       ├── trainer-angriness-predictor/  # Angriness/tilt detection model
│       ├── trainer-ap/           #   Accuracy prediction model
│       └── trainer-factor-imp/   #   Factor impact analysis
├── scripts/
│   ├── databases/                # SQL init, triggers, and migrations
│   └── ml/                       # Helper scripts for ML workflow
├── services/
│   ├── iot-service/Grpc-Server/  # C# .NET 10 gRPC server (sensor data)
│   ├── LichessApiService.grpc/   # C# .NET 10 gRPC server (Lichess data)
│   └── LichessApiService.grpc.Tests/  # xUnit tests (80% coverage threshold)
├── shared/                       # Protobuf definitions (IoT.proto, LichessApi.proto)
├── documentation/                # Analysis, design, and implementation docs
├── docker-compose.yml            # Development environment
└── docker-compose.prod.yml       # Production environment (GHCR images, caddy_net)
```

## CI/CD Pipeline

Three GitHub Actions workflows automate testing, building, and deployment:

### `frontend.yml`

Triggers on push/PR to `develop` when `frontend/chessapp/**` files change.

- **CI job**: `npm ci` → `npm run test:coverage` → `npm run build`
- **Docker job** (push only): builds and pushes the frontend image to GHCR

### `iot_workflow.yaml`

Triggers on push to `develop` or any PR when IoT-related paths change.

- Builds the C sensor client with CMake and runs unit tests (`test_message_builder`, `test_sensor_reader`)
- Builds the PlatformIO Arduino project
- Builds and tests the .NET IoT gRPC server

### `ml-team-ci-cd.yml`

The main pipeline, triggers on push/PR to `develop` and `main`.

- **Test jobs**:
  - Lichess API Service: .NET 10 build + xUnit tests with 80% line coverage threshold
  - ML pipelines: runs all 4 training pipelines (winrate, angriness, accuracy, factor impact), verifies model artifacts are produced, starts FastAPI and validates `/health` and `/health/ready` endpoints
- **Publish jobs** (push only): builds and pushes 4 Docker images to GHCR:
  - `lichessapi-grpc`
  - `chess-ml-api`
  - `chess-api-gateway`
  - `iot-grpc-server`
- **Deploy job** (main branch only): SCPs compose files and SQL migrations to the VPS, SSHs in, pulls latest images, restarts services, reloads Caddy, and runs incremental database migrations

## Deployment Architecture

The production environment uses a three-tier setup:

### Frontend: Cloudflare Pages (PaaS)

The React SPA is deployed to [Cloudflare Pages](https://pages.cloudflare.com/) at **`chess.cannyboiz.com`** using a rented custom domain. Cloudflare provides a global CDN, automatic HTTPS, and edge caching.

### Backend: Hetzner Cloud CX23 (IaaS)

All backend services run on a single **Hetzner Cloud CX23** VPS via Docker Compose. Services expose no external ports; all traffic is routed through the reverse proxy on the internal `caddy_net` Docker network.

### Reverse Proxy: Caddy

[Caddy](https://caddyserver.com/) was chosen as the reverse proxy because it is simple to configure and provides automatic HTTPS, HTTP/2, and sensible defaults out of the box.

- The core Caddy instance and its main configuration live in a separate repository: [cannyboiz-devops-hub](https://github.com/MrPAkaCannyBoiz/cannyboiz-devops-hub)
- This repository contributes `infrastructure/chess.Caddyfile`, which is imported by the main Caddy gateway via `import /etc/caddy/sites/*`
- Backend domain: **`api-chess.cannyboiz.com`**

### Container Registry

All service images are published to GitHub Container Registry under `ghcr.io/kanku-sep4-org/chess-assistance/`.

### Deployment Flow

1. Code is merged to `main`, triggering the CI/CD pipeline
2. All tests pass, Docker images are built and pushed to GHCR
3. The deploy job SSHs into the VPS and copies compose files + SQL migrations
4. `docker compose pull` fetches the latest images
5. `docker compose up -d` restarts services
6. Caddy configuration is reloaded to pick up any routing changes
7. SQL migrations are applied incrementally (tracked in a `schema_migrations` table)

## Testing

### Frontend

- **Framework**: Vitest with jsdom and React Testing Library
- **Coverage thresholds**: 80% lines, 80% functions, 70% branches
- **Test files**: `*.test.jsx` alongside page components

```bash
cd frontend/chessapp
npm run test:coverage
```

### Lichess API Service

- **Framework**: xUnit with Moq
- **Coverage threshold**: 80% line coverage (excludes generated protobuf code and `Program.cs`)

```bash
dotnet test services/LichessApiService.grpc.Tests/
```

### IoT C Client

- **Framework**: CMake-based unit tests

```bash
cd internet_of_things/sensor_client_c
mkdir build && cd build
cmake .. && cmake --build .
./test_message_builder
./test_sensor_reader
```

### IoT gRPC Server

- **Framework**: .NET test project

```bash
dotnet test services/iot-service/Grpc_Test/
```

### ML API

- **Framework**: pytest

```bash
cd machine_learning/api
pytest test_health.py -v
```

### ML Training Pipelines

Each pipeline is validated in CI by running the full training process and verifying that expected artifacts (model files, metrics JSON) are produced.

## Contributing

This is a team project with 14 contributors. Follow these conventions:

1. **Branch from `develop`** -- create feature branches off the `develop` branch
2. **Pull requests required** -- all changes to `develop` and `main` go through PRs
3. **CI must pass** -- all workflow checks must be green before merging
4. **`develop`** is the integration branch; **`main`** is production
5. **Follow existing conventions** per service:
   - JavaScript/Node.js for the API gateway
   - C# / .NET for Lichess API and IoT services
   - Python for ML pipelines and FastAPI
   - C for the IoT sensor client
