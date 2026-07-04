# Mediva Deployment & Subdomain Routing Guide

This guide describes how to build the Mediva services using Docker and map them to the following subdomains under `novasyntax.in` for global access:
- **`mediva.novasyntax.in`** -> Next.js Frontend (`web` service on port `3000`)
- **`fastapi.novasyntax.in`** -> FastAPI Backend (`api` service on port `8000`)

---

## 1. Docker Build Commands

Since Mediva is structured as a monorepo, **all Docker builds must be run from the root of the project** (`c:\Users\rohan sai\OneDrive\Desktop\Mediva`). This is because the Dockerfiles copy files from package dependencies (e.g., `packages/backend-core/`) that live outside the individual app directories.

### Build All Services (Recommended)
To build all the services defined in your `docker-compose.yml` (PostgreSQL, Redis, LiveKit, Prometheus, Grafana, API, AI-Service, Worker, Web, and Cloudflare Tunnel), run:
```bash
docker compose build
```

### Build Individual Services
If you want to build only a specific container, you must specify the root directory as the context (`.`) and point to the Dockerfile with the `-f` flag:

* **Next.js Frontend (`web`)**:
  ```bash
  docker build -t mediva-web -f infrastructure/docker/web/Dockerfile .
  ```
* **FastAPI Backend (`api`)**:
  ```bash
  docker build -t mediva-api -f infrastructure/docker/api/Dockerfile .
  ```
* **AI Service (`ai-service`)**:
  ```bash
  docker build -t mediva-ai-service -f infrastructure/docker/ai/Dockerfile .
  ```
* **Celery Worker (`worker`)**:
  ```bash
  docker build -t mediva-worker -f infrastructure/docker/worker/Dockerfile .
  ```

---

## 2. Global Access Setup (Subdomains)

Depending on your hosting setup, choose either **Option A** (local testing on your PC exposed to the internet via Cloudflare Tunnel) or **Option B** (production deployment on a VPS via Dokploy).

### Option A: Local to Global Access (via Cloudflare Tunnels)

Cloudflare Tunnels allow you to expose your local containers to the internet securely under your custom subdomains without opening any ports on your local router/firewall.

#### Step 1: Create a Tunnel in Cloudflare Zero Trust
1. Log in to your [Cloudflare Dashboard](https://dash.cloudflare.com/).
2. Navigate to **Zero Trust** in the sidebar.
3. Go to **Networks** -> **Tunnels** and click **Create a Tunnel**.
4. Choose **Cloudflare (Recommended)** as the connector type and name it (e.g., `mediva-local`).
5. Click **Save tunnel**.

#### Step 2: Retrieve your Tunnel Token
Under the **Install and run a connector** section, select the Docker instructions. Look at the command provided, which contains a long token string.
Copy this token value.

#### Step 3: Add the Token to your local configuration
Add the token to your `.env` file at the root of the project:
```env
CLOUDFLARE_TUNNEL_TOKEN=your_copied_cloudflare_tunnel_token_here
```

#### Step 4: Configure the Subdomain Routing rules in Cloudflare
Inside your Tunnel details page on the Cloudflare Dashboard, go to the **Public Hostname** tab and add two rules:

1. **Frontend Rule:**
   - **Subdomain:** `mediva`
   - **Domain:** `novasyntax.in`
   - **Type:** `HTTP`
   - **URL:** `web:3000` *(Uses internal Docker network hostname)*

2. **Backend Rule:**
   - **Subdomain:** `fastapi`
   - **Domain:** `novasyntax.in`
   - **Type:** `HTTP`
   - **URL:** `api:8000` *(Uses internal Docker network hostname)*

#### Step 5: Spin up the Services
Run your Docker Compose stack:
```bash
docker compose up -d
```
The `tunnel` container will start, read the token, connect to Cloudflare, and bind traffic for `mediva.novasyntax.in` and `fastapi.novasyntax.in` directly to the `web` and `api` containers respectively.

---

### Option B: VPS Production Deployment (via Dokploy)

If you are hosting the project on a public VPS using **Dokploy**, Dokploy manages Traefik routing, HTTPS certificates (Let's Encrypt), and ingress for you.

#### Step 1: Configure your DNS Records
In your Cloudflare (or registrar) DNS panel, add two **A Records** pointing to your VPS public IP address:
- `mediva.novasyntax.in` -> `VPS_IP` (Proxied or DNS Only)
- `fastapi.novasyntax.in` -> `VPS_IP` (Proxied or DNS Only)

#### Step 2: Configure Domains in Dokploy UI
For each application inside the Dokploy dashboard:

1. **Frontend (`web`):**
   - Open the **web** application page in Dokploy.
   - Go to the **Domains** tab.
   - Add a new domain:
     - **Host:** `mediva.novasyntax.in`
     - **Port:** `3000`
   - Save and enable HTTPS. Dokploy will automatically request a Let's Encrypt certificate.

2. **Backend API (`api`):**
   - Open the **api** application page in Dokploy.
   - Go to the **Domains** tab.
   - Add a new domain:
     - **Host:** `fastapi.novasyntax.in`
     - **Port:** `8000`
   - Save and enable HTTPS.

*(Note: We have updated `infrastructure/dokploy/*.yaml` configurations to match the file structure. Dokploy will build the images using the Dockerfiles at `infrastructure/docker/web/Dockerfile` and `infrastructure/docker/api/Dockerfile` respectively).*
