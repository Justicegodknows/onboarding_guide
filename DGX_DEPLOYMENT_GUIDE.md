# VaultMind DGX Spark Deployment Guide

## Architecture Overview
- **Frontend**: Vercel (https://onboarding-guide-three.vercel.app/) + Localhost (http://localhost:3000)
- **Backend**: DGX Spark at 192.168.18.199:8000 (FastAPI)
- **Database**: PostgreSQL at 192.168.18.199:5432
- **Vector Store**: ChromaDB at 192.168.18.199:8100
- **Cache**: Redis at 192.168.18.199:6379
- **LLM**: Ollama at 192.168.18.199:11434
- **Embeddings**: NVIDIA NIM (Cloud-based via API key)

## Pre-Deployment Checklist

### On DGX Spark (192.168.18.199)

1. **Create persistent data directories**:
```bash
mkdir -p /home/admin/app-data/{postgres,chromadb,redis}
chmod 755 /home/admin/app-data/{postgres,chromadb,redis}
```

2. **Install Docker & Docker Compose**:
   - Follow official Docker install guide
   - Verify with: `docker --version` and `docker-compose --version`

3. **Verify Ollama is running on port 11434**:
```bash
curl http://localhost:11434/api/tags
# Should return available models
```

4. **Verify network connectivity**:
```bash
# From frontend machine, test connectivity to DGX
ping 192.168.18.199
curl http://192.168.18.199:11434/api/tags
```

### On Frontend Machine (Vercel/Localhost)

1. **Update .env files** (Already done):
   - `.env.local` → `http://localhost:8000` (for local dev)
   - `.env.production` → `http://192.168.18.199:8000` (for Vercel)

2. **Build & Deploy to Vercel**:
```bash
# From project root
npm run build
# Deploy via Vercel CLI or GitHub integration
vercel deploy --prod
```

## Deployment Steps

### Step 1: Copy Backend to DGX

```bash
# On DGX, create project directory
mkdir -p /opt/vaultmind
cd /opt/vaultmind

# From localhost, copy the rag_backend folder to DGX
scp -r /path/to/rag_backend/* admin@192.168.18.199:/opt/vaultmind/

# OR use rsync for resume capability
rsync -avz --delete /path/to/rag_backend/ admin@192.168.18.199:/opt/vaultmind/
```

### Step 2: Start Backend Services on DGX

```bash
# SSH into DGX
ssh admin@192.168.18.199

# Navigate to project
cd /opt/vaultmind

# Build Docker images
docker-compose build

# Start services (detached)
docker-compose up -d

# Verify services are running
docker-compose ps

# Check logs
docker-compose logs -f api
```

### Step 3: Verify Backend Connectivity

```bash
# From frontend machine, test endpoints

# Health check
curl http://192.168.18.199:8000/health

# Should get:
# {"status":"ok","timestamp":"2026-05-22T..."}

# Try authentication endpoint (will fail without proper credentials, but shows connectivity)
curl -X POST http://192.168.18.199:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vaultmind.local","password":"admin123"}'
```

### Step 4: Update Vercel Environment Variables

In Vercel project settings:
1. Go to Settings → Environment Variables
2. Add/Update:
   - `NEXT_PUBLIC_API_URL=http://192.168.18.199:8000`
3. Redeploy after changes

### Step 5: Test Frontend-to-Backend Communication

1. Open https://onboarding-guide-three.vercel.app/
2. Try to login with:
   - Email: `admin@vaultmind.local`
   - Password: `admin123`
3. If login succeeds, check browser console for errors (Cmd+Opt+J / F12)

## HTTPS/SSL Setup (Optional but Recommended)

### For Production (Self-Signed or Valid Certificates)

If you want HTTPS instead of HTTP:

1. **Generate self-signed certificate on DGX**:
```bash
cd /opt/vaultmind
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365
# Fill in certificate details, common name should be 192.168.18.199 or your domain
```

2. **Update docker-compose.yml to use Nginx reverse proxy with SSL**:
   - Add Nginx service listening on 443
   - Mount cert.pem and key.pem
   - Proxy requests to FastAPI on 8000

3. **Update .env.production**:
```
NEXT_PUBLIC_API_URL=https://192.168.18.199:8000
```

## Troubleshooting

### Backend services fail to start
```bash
# Check logs
docker-compose logs api
docker-compose logs postgres
docker-compose logs chroma
docker-compose logs redis

# Common issue: Ports already in use
netstat -tuln | grep -E ':(5432|8000|8100|6379)'

# Solution: Stop other services or use different ports in docker-compose.yml
```

### Frontend can't reach backend
```bash
# From frontend machine
# 1. Check network connectivity
ping 192.168.18.199
traceroute 192.168.18.199

# 2. Check if port 8000 is open
nc -zv 192.168.18.199 8000

# 3. Check firewall on DGX
sudo ufw status
# If needed, allow port 8000:
sudo ufw allow 8000
```

### Database connection failures
```bash
# SSH to DGX and test PostgreSQL directly
psql -h 192.168.18.199 -U postgres -d postgres -c "SELECT 1;"
# Default password from .env is "postgres"
```

### ChromaDB not reachable externally
```bash
# ChromaDB inside the container listens on port 8000.
# The host port must be published as 8100:8000.
# Verify the compose mapping is correct:
cat docker-compose.yml | grep -A3 "chroma:"

# If the mapping is wrong, update it to:
#   - "8100:8000"

# Then recreate the container:
docker-compose up -d --force-recreate chroma

# Verify from the host:
curl http://192.168.18.199:8100/api/v1/heartbeat
```

### ChromaDB not persisting data
```bash
# Verify volume mount
docker-compose exec chroma ls -la /chroma/.chroma/index

# Check file permissions
ls -la /home/admin/app-data/chromadb

# Fix permissions if needed
sudo chown -R 1000:1000 /home/admin/app-data/chromadb
```

## Rolling Back / Local Development

To revert to local development mode:

1. **Backend**: Run `docker-compose up -d` in localhost `/rag_backend`
2. **Frontend**: Use `.env.local` (already configured for localhost)
3. **Stop DGX backend**: `ssh admin@192.168.18.199 'cd /opt/vaultmind && docker-compose down'`

## Monitoring & Logs

### View real-time logs from DGX
```bash
ssh admin@192.168.18.199 'cd /opt/vaultmind && docker-compose logs -f'
```

### Archive logs for analysis
```bash
ssh admin@192.168.18.199 'cd /opt/vaultmind && docker-compose logs > logs-$(date +%Y%m%d).txt'
scp admin@192.168.18.199:/opt/vaultmind/logs-*.txt ./
```

## Performance Optimization

Once deployed, monitor:
1. CPU/Memory usage on DGX
2. Database query performance
3. ChromaDB retrieval latency
4. Ollama LLM inference time

To improve:
- Increase Docker memory limits in docker-compose.yml
- Index optimization in PostgreSQL
- ChromaDB batch processing tuning
- Ollama quantization model (smaller model = faster inference)

## Data Backup Strategy

Regular backups of:
1. PostgreSQL database (weekly)
2. ChromaDB vector store (weekly)
3. Redis cache (optional, auto-recoverable)
4. Documents in local folder (as configured)

Example backup script:
```bash
#!/bin/bash
BACKUP_DIR="/home/admin/backups"
mkdir -p $BACKUP_DIR

# PostgreSQL backup
docker-compose exec -T postgres pg_dump -U postgres postgres > \
  $BACKUP_DIR/postgres-$(date +%Y%m%d-%H%M%S).sql

# ChromaDB backup
cp -r /home/admin/app-data/chromadb \
  $BACKUP_DIR/chromadb-$(date +%Y%m%d)

# Keep only last 30 days
find $BACKUP_DIR -type f -mtime +30 -delete
```

---

**Last Updated**: May 22, 2026
**Deployment Status**: Ready for DGX Spark
