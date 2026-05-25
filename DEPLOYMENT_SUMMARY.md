# VaultMind DGX Migration - Summary of Changes

## Overview
Successfully configured VaultMind RAG system for deployment on NVIDIA DGX Spark. The entire backend and database move to DGX (192.168.18.199) while the frontend stays on Vercel and localhost.

## Files Modified

### 1. Backend Configuration
**`rag_backend/.env`** (completely rewritten for DGX)
- Updated all service URLs to point to DGX IP (192.168.18.199)
- PostgreSQL: `192.168.18.199:5432`
- ChromaDB: `192.168.18.199:8100`
- Redis: `192.168.18.199:6379`
- Ollama (primary LLM): `192.168.18.199:11434`
- Added Vercel frontend to CORS_ORIGINS
- Next.js public API URL: `http://192.168.18.199:8000`

**`rag_backend/docker-compose.yml`**
- Changed Ollama/LM Studio from `host.docker.internal` to `192.168.18.199`
- Updated volume mounts to use persistent host paths:
  - PostgreSQL: `/home/admin/app-data/postgres`
  - ChromaDB: `/home/admin/app-data/chromadb`
  - Redis: `/home/admin/app-data/redis`
- Changed PostgreSQL external port from 5433 → 5432 (standard port)
- Removed named volumes (using host paths for persistence)

**`rag_backend/app/main.py`**
- Updated CORS configuration to use `settings.CORS_ORIGINS` from .env
- Changed from wildcard `["*"]` to explicit origin list
- Enabled `allow_credentials=True` for secure cross-origin requests

### 2. Frontend Configuration
**`.env.production`**
- Updated `NEXT_PUBLIC_API_URL` to `http://192.168.18.199:8000`
- Updated all auth endpoints to use DGX IP
- Replaces old dev tunnel URL (`52j5v7nj-8000.euw.devtunnels.ms`)

**`.env.local`** (unchanged - good for local dev)
- Keeps `http://localhost:8000` for local development

### 3. New Files Created

**`DGX_DEPLOYMENT_GUIDE.md`**
- Comprehensive deployment documentation
- Architecture overview
- Pre-deployment checklist
- Step-by-step deployment instructions
- Troubleshooting guide
- Monitoring and backup strategies

**`deploy-to-dgx.sh`**
- Automated deployment script
- Creates directories on DGX
- Copies backend code via rsync
- Builds Docker images
- Starts all services
- Waits for services to be ready

**`verify-deployment.sh`**
- Verification script to run from frontend machine
- Checks network connectivity
- Validates all service ports
- Tests API endpoints
- Provides summary and next steps

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                        DGX Spark                         │
│                    (192.168.18.199)                      │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │ FastAPI      │  │ PostgreSQL │  │ ChromaDB (vec)  │  │
│  │ (port 8000)  │  │ (port 5432)│  │ (port 8100)     │  │
│  └──────────────┘  └────────────┘  └─────────────────┘  │
│                                                          │
│  ┌──────────────┐  ┌────────────┐  ┌─────────────────┐  │
│  │ Ollama       │  │ Redis      │  │ Persistent Data │  │
│  │ (port 11434) │  │ (port 6379)│  │ (/app-data/...)│  │
│  └──────────────┘  └────────────┘  └─────────────────┘  │
└─────────────────────────────────────────────────────────┘
         ▲                                    ▲
         │                                    │
    ┌────┴────────────────────────────────────┴────┐
    │    Network (LAN / HTTP over 192.168.x.x)    │
    └────┬────────────────────────────────────────┬────┘
         │                                    │
         │                              ┌─────┴──────┐
    ┌────┴──────┐                       │   Vercel   │
    │ Localhost │                       │  (HTTPS)   │
    │ Port 3000 │         Remote         │            │
    └───────────┘       Deployment       └────────────┘
         │                                    │
         └───────────────────────────────────┘
              (Can both call DGX backend)
```

## Backward Compatibility

✅ **No breaking changes**
- All APIs remain the same
- Database schema is compatible
- JWT authentication works as before
- Frontend API calls work unchanged (just different backend URL)
- Local development still works with `.env.local`

## Security Considerations

1. **Network Security**:
   - Backend is on private network (192.168.18.x)
   - Consider firewall rules to restrict access
   - For production, add VPN/reverse proxy layer

2. **HTTPS/SSL** (Optional):
   - Guide provided in `DGX_DEPLOYMENT_GUIDE.md`
   - Can use self-signed certs for testing
   - Production should use valid certificates

3. **Authentication**:
   - JWT tokens continue to work
   - CORS now uses explicit whitelist
   - Database passwords should be changed from defaults

## Deployment Process

### Quick Start
```bash
# 1. From project root, run deployment script
./deploy-to-dgx.sh

# 2. Verify deployment
./verify-deployment.sh

# 3. Test frontend
# Open https://onboarding-guide-three.vercel.app/
# Login with admin@vaultmind.local / admin123
```

### Manual Steps (if needed)
```bash
# 1. SSH to DGX
ssh admin@192.168.18.199

# 2. Create data directories
mkdir -p /home/admin/app-data/{postgres,chromadb,redis}

# 3. Copy backend (from localhost)
rsync -avz ./rag_backend/ admin@192.168.18.199:/opt/vaultmind/

# 4. Start services
cd /opt/vaultmind
docker-compose up -d

# 5. Check logs
docker-compose logs -f api
```

## Data Persistence

All persistent data stored on DGX at:
- **PostgreSQL**: `/home/admin/app-data/postgres`
- **ChromaDB**: `/home/admin/app-data/chromadb`
- **Redis**: `/home/admin/app-data/redis`

These mount points are preserved even if containers restart.

## Rollback to Local Development

If needed, revert to local development:
```bash
# 1. Stop DGX backend
ssh admin@192.168.18.199 'cd /opt/vaultmind && docker-compose down'

# 2. Start local backend
cd ./rag_backend && docker-compose up -d

# 3. Frontend automatically uses `.env.local` on localhost
```

## Testing Checklist

- [ ] Backend health check: `curl http://192.168.18.199:8000/health`
- [ ] Frontend loads: https://onboarding-guide-three.vercel.app/
- [ ] Can login with admin credentials
- [ ] Can upload documents
- [ ] Can chat with backend
- [ ] Chat responses use Ollama model
- [ ] Vector search works (ChromaDB)
- [ ] Logs show no errors

## Performance Notes

- **LLM Inference**: Ollama on DGX (gemma4 by default)
- **Embeddings**: NVIDIA NIM cloud API (can switch to local if needed)
- **Database**: PostgreSQL on same network (low latency)
- **Vector Search**: ChromaDB local on DGX (fast retrieval)

## Next Steps

1. **Pre-Deployment**:
   - [ ] Create SSH access to DGX
   - [ ] Verify Docker installed on DGX
   - [ ] Verify Ollama running on port 11434

2. **Deployment**:
   - [ ] Run `./deploy-to-dgx.sh`
   - [ ] Run `./verify-deployment.sh`
   - [ ] Update Vercel environment variables

3. **Post-Deployment**:
   - [ ] Test login on frontend
   - [ ] Test document upload
   - [ ] Test RAG chat
   - [ ] Monitor DGX resources
   - [ ] Setup backup strategy

## Support & Troubleshooting

Refer to:
- `DGX_DEPLOYMENT_GUIDE.md` - Detailed guide with troubleshooting
- `deploy-to-dgx.sh` - Automated deployment (read comments for details)
- `verify-deployment.sh` - Validation and diagnostics

---

**Migration Date**: May 22, 2026
**Status**: Ready for deployment
**Last Updated**: May 22, 2026
