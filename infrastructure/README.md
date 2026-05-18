# Infrastructure & Deployment

This directory contains everything needed to deploy Chess-Assistance to production on our Hetzner VPS.

## Architecture

```
                        Internet
                           │
                    ┌──────┴──────┐
                    │    Caddy    │  (shared reverse proxy, auto TLS)
                    │  ports 80/443│
                    └──────┬──────┘
                           │ caddy_net (Docker network)
              ┌────────────┼────────────┐
              │                         │
   chess.cannyboiz.com       api-chess.cannyboiz.com
              │                         │
      ┌───────┴───────┐        ┌───────┴────────┐
      │   frontend    │        │  api-gateway   │
      │  (nginx :80)  │        │ (Express :3001)│
      └───────────────┘        └───────┬────────┘
                                       │ gRPC
                               ┌───────┴────────┐
                               │  grpc-service  │
                               │  (Node :50051) │
                               └───┬────────┬───┘
                          gRPC     │        │    gRPC
                       ┌───────────┘        └───────────┐
               ┌───────┴───────┐              ┌────────┴────────┐
               │    ml-api     │              │   iot-service   │
               │(FastAPI :8000)│              │  (C# gRPC :8080)│
               └───────────────┘              └─────────────────┘
```

## Files

| File | Purpose |
|------|---------|
| `docker-compose.prod.yml` (repo root) | Production Docker Compose — defines all services |
| `infrastructure/Caddyfile.chess` | Caddy reverse proxy rules for our subdomains |
| `.github/workflows/deploy.yml` | CI/CD — auto-deploys on push to `main` |
| `api-gateway/Dockerfile` | Dockerfile for the Express API gateway |
| `services/grpc-service/Dockerfile` | Dockerfile for the Node.js gRPC relay |

## How deployment works

1. A push to `main` triggers `.github/workflows/deploy.yml`
2. The workflow SSHs into the Hetzner VPS
3. It clones/pulls the latest code to `/opt/chess-assistance`
4. Runs `docker compose -f docker-compose.prod.yml up --build -d`
5. Copies `Caddyfile.chess` to the shared Caddy sites directory
6. Reloads Caddy — TLS certificates are provisioned automatically

## Networks

- **caddy_net** — shared external Docker network connecting Caddy to service frontends (frontend + api-gateway). Managed by the Caddy gateway stack.
- **chess_internal** — internal bridge network for service-to-service communication (grpc-service, ml-api, iot-service). Not exposed externally.

## Required GitHub Secrets

| Secret | Description |
|--------|-------------|
| `VPS_HOST` | Hetzner VPS IP address |
| `VPS_SSH_KEY` | SSH private key for `root` on the VPS |
| `REPO_CLONE_URL` | Git clone URL (HTTPS with PAT or SSH) |

## Local development vs production

- **Local**: Use the root `docker-compose.yml` — services expose ports directly for local access
- **Production**: Use `docker-compose.prod.yml` — no ports exposed, Caddy handles all external traffic with TLS
