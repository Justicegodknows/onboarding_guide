# VaultMind HTTPS/Cloudflare Deployment Validation Checklist

## ✅ Configuration Validation Results

### Frontend Configuration (.env.production)
- [x] `NEXT_PUBLIC_API_URL=/api/proxy` - Frontend uses proxy
- [x] `CLOUDFLARE_BACKEND_URL=https://vaultmind.yourdomain.com` - HTTPS domain template
- [x] `DGX_BACKEND_URL=https://vaultmind.yourdomain.com` - Server-side fallback
- [x] Auth endpoints configured for HTTPS

### Backend Configuration (rag_backend/.env)
- [x] `NEXT_PUBLIC_API_URL=https://vaultmind.yourdomain.com` - HTTPS template
- [x] `CORS_ORIGINS` includes Vercel frontend
- [x] `CORS_ORIGINS` includes Cloudflare HTTPS domain template
- [x] Internal services (ChromaDB, Redis, PostgreSQL, Ollama) remain on HTTP

### API Proxy (app/api/proxy/[...path]/route.ts)
- [x] Reads from `CLOUDFLARE_BACKEND_URL` environment
- [x] Fallback to `DGX_BACKEND_URL` 
- [x] Fallback to `http://192.168.18.199:8000`
- [x] All HTTP methods supported (GET, POST, PUT, PATCH, DELETE)
- [x] Request/response headers properly forwarded

### FastAPI HTTPS Support (rag_backend/app/main.py)
- [x] `TrustedHostMiddleware` imported and configured
- [x] Cloudflare hosts in allowed_hosts list
- [x] CORS middleware configured from settings
- [x] Security headers middleware implemented
- [x] Strict-Transport-Security header set (HSTS)
- [x] X-Content-Type-Options: nosniff
- [x] X-Frame-Options: DENY
- [x] X-XSS-Protection: 1; mode=block
- [x] Cloudflare header handling middleware

### Docker Configuration (rag_backend/docker-compose.yml)
- [x] ChromaDB port mapping: `8100:8000` (correct)
- [x] PostgreSQL accessible on `192.168.18.199:5432`
- [x] Redis accessible on `192.168.18.199:6379`

### Tests Updated
- [x] app/api/__tests__/backend.test.ts - Updated for new API_URL logic

### Documentation
- [x] CLOUDFLARE_HTTPS_SETUP.md created
- [x] DGX_DEPLOYMENT_GUIDE.md updated
- [x] HTTPS_MIGRATION_SUMMARY.md created
- [x] test-https-config.sh created

---

## 🚀 Pre-Deployment Checklist

### Step 1: Prepare Your Cloudflare Domain
- [ ] Set up Cloudflare Tunnel to DGX
- [ ] Get your domain/tunnel URL: `https://yourbackend.example.com`
- [ ] Verify tunnel is running: `curl https://yourbackend.example.com/health`

### Step 2: Update Environment Variables
- [ ] Replace `https://vaultmind.yourdomain.com` in `.env.production` with your domain
- [ ] Replace `https://vaultmind.yourdomain.com` in `rag_backend/.env` with your domain
- [ ] Verify CORS_ORIGINS includes your domain

### Step 3: Deploy Frontend
```bash
# Commit and push (Vercel auto-redeploys)
git add .env.production app/api/proxy
git commit -m "feat: HTTPS support for Cloudflare tunnel"
git push origin main

# Wait for Vercel deployment (check https://vercel.com dashboard)
```

### Step 4: Deploy Backend
```bash
# SSH to DGX
ssh admin@192.168.18.199

# Update .env with your Cloudflare domain
cd /home/admin/onboarding_guide
nano rag_backend/.env

# Restart containers
cd rag_backend
docker compose down
docker compose up -d

# Verify all services healthy
docker compose ps
```

### Step 5: Verification Tests
```bash
# Test 1: Backend health (HTTP only, for verification)
curl http://192.168.18.199:8000/health

# Test 2: Backend health via Cloudflare HTTPS
curl https://yourbackend.example.com/health

# Test 3: Login endpoint
curl -X POST https://yourbackend.example.com/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vaultmind.local","password":"admin123"}'

# Test 4: Frontend integration
# Navigate to: https://onboarding-guide-three.vercel.app/login
# Use: admin@vaultmind.local / admin123
# Try chat functionality
# Check browser console for any errors
```

### Step 6: Monitoring
- [ ] Monitor DGX backend logs: `docker compose logs -f api`
- [ ] Check Cloudflare tunnel status
- [ ] Verify no mixed content errors in browser console
- [ ] Test different departments and chat functionality
- [ ] Upload documents and verify RAG pipeline works

---

## 🔒 Security Verification

### HTTPS/TLS
- [x] All client-to-internet traffic is HTTPS
- [x] Cloudflare provides edge SSL/TLS termination
- [x] HSTS header set (forces HTTPS)

### Origin Security
- [x] CORS_ORIGINS whitelisted
- [x] Only Vercel frontend and your Cloudflare domain allowed
- [x] Localhost only for development

### Header Security
- [x] Strict-Transport-Security enabled
- [x] X-Content-Type-Options: nosniff
- [x] X-Frame-Options: DENY (prevents clickjacking)
- [x] X-XSS-Protection enabled

### Database Security
- [x] PostgreSQL on private network (no public access)
- [x] Redis on private network (no public access)
- [x] Only accessible from FastAPI container

---

## 📊 Architecture Diagram

```
User Browser (HTTPS)
    ↓
Vercel Frontend
    ├─ Production: https://onboarding-guide-three.vercel.app
    └─ Next.js API Proxy: /api/proxy/...
         ↓
    Vercel Backend Route
         ↓ (server-side, uses CLOUDFLARE_BACKEND_URL)
    Cloudflare Tunnel (HTTPS)
         ↓ (encrypted tunnel)
    DGX Backend (HTTP internally)
         ├─ FastAPI: 192.168.18.199:8000
         ├─ ChromaDB: 192.168.18.199:8100
         ├─ PostgreSQL: 192.168.18.199:5432
         ├─ Redis: 192.168.18.199:6379
         └─ Ollama: 192.168.18.199:11434
```

---

## ⚠️ Important Notes

1. **Template Placeholder**: All references to `https://vaultmind.yourdomain.com` are placeholders
2. **Do Not Deploy Without Updating Domain**: Tests will work but will fail with wrong domain
3. **ChromaDB Port Mapping**: Must be `8100:8000` for external access to work
4. **Restart Required**: Backend must be restarted after .env changes to reload CORS_ORIGINS
5. **HTTPS Required**: Vercel (HTTPS) cannot call HTTP backends; proxy solves this
6. **Internal Services**: Remain on HTTP inside private network (correct architecture)

---

## 🧹 Cleanup After Deployment

Once everything is verified working:
1. Remove/replace hardcoded IP `192.168.18.199` if infrastructure changes
2. Enable HTTPS certificate pinning for production
3. Consider rate limiting at Cloudflare edge
4. Set up log aggregation for monitoring
5. Create backup strategy for PostgreSQL and ChromaDB

---

## 📞 Support Reference

- Cloudflare HTTPS Setup: See [CLOUDFLARE_HTTPS_SETUP.md](./CLOUDFLARE_HTTPS_SETUP.md)
- DGX Deployment: See [DGX_DEPLOYMENT_GUIDE.md](./DGX_DEPLOYMENT_GUIDE.md)
- Migration Summary: See [HTTPS_MIGRATION_SUMMARY.md](./HTTPS_MIGRATION_SUMMARY.md)
