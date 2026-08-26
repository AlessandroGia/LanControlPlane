# LanControlPlane

LanControlPlane is a self-hosted LAN dashboard for monitoring hosts and sending Wake-on-LAN, shutdown, and reboot commands. It consists of:

- `server`: FastAPI, WebSockets, SQLAlchemy, Alembic, and SQLite;
- `agent`: a Python service installed on each managed host;
- `shared`: validated protocol models shared by server and agent;
- `web`: a Next.js dashboard;
- `server/wol_helper`: a small authenticated service that sends broadcast packets from the host network.

## Security model

Dashboard users authenticate with an HTTP-only session cookie. Only users with the `admin` role can change host network data or send control commands. Agent messages are bound to the authenticated connection and may only update jobs belonging to that agent's host.

`AGENT_ENROLLMENT_TOKEN` is the shared, short-lived enrollment secret for new agents. Each agent also has its own unique `AGENT_TOKEN`; only its hash is stored by the server, and a credential already assigned to one host cannot enroll another. Protect every `.env` file, rotate the enrollment token after provisioning, and use `wss://` for traffic that can cross an untrusted network.

The WOL helper requires `WOL_HELPER_TOKEN`. Use the same long random token in `server/.env` and `server/wol_helper/.env` and restrict port 8099 to the server host with a firewall.

## Server setup

1. Copy `server/.env.example` to `server/.env` and configure the database, agent token, WOL helper URL/token, CORS origins, and cookie security.
2. Create the external Docker network once:

   ```bash
   docker network create rp-admin
   ```

3. Start the server:

   ```bash
   cd server
   docker compose up -d --build
   ```

   The server image applies Alembic migrations before starting.

4. Create the administrator password file and account:

   ```bash
   mkdir -p secrets
   printf '%s' 'replace-this-password' > secrets/admin_password.txt
   ./scripts/create_admin.sh
   ```

## Web setup

Set `INTERNAL_API_BASE_URL` in `web/.env.production`. The browser expects the reverse proxy to route `/auth`, `/hosts`, `/jobs`, `/agents`, `/audit-logs`, `/metrics`, and `/ws/client` to the FastAPI server.

For Docker deployment, create the external `public-net` network used by the reverse proxy and run:

```bash
docker network create public-net
cd web
docker compose up -d --build
```

## Agent setup

Copy `agent/.env.example` to `agent/.env`, choose a safe identifier containing only letters, numbers, `.`, `_`, or `-`, generate a unique random `AGENT_TOKEN`, and set the same `AGENT_ENROLLMENT_TOKEN` configured by the server. After the first successful registration, remove the enrollment token from that agent's environment. The server marks connections stale after `AGENT_OFFLINE_AFTER_SECONDS`; keep that value comfortably above `WS_HEARTBEAT_INTERVAL`.

Install the native service from the repository root:

```bash
python agent/install.py
```

Linux, macOS, and Windows installers are included. Native installation is required for real shutdown/reboot control. The agent Docker image is appropriate for development and `DRY_RUN=true`; a normal container cannot safely power off its host.

## Wake-on-LAN helper

On the machine connected to the target broadcast network:

```bash
cp server/wol_helper/.env.example server/wol_helper/.env
server/wol_helper/install_service.sh
```

The helper runs as a restricted dynamic system user and refuses wake requests without the configured token.

## Development checks

Python projects require Python 3.12 and `uv`. The web application requires Node.js 22.

```bash
server/scripts/check.sh
```

The script runs Ruff, formatting checks, mypy, pytest, frontend lint, and the production Next.js build. CI performs the same categories of checks and also builds all Docker images and applies migrations to a fresh database.
