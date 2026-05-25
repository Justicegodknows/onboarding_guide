# VaultMind - Cloudflare HTTPS Deployment Guide

## Overview

VaultMind is now exposed to the internet via Cloudflare with full HTTPS encryption. The backend is protected by Cloudflare's tunnel, and all browser-to-backend communication is encrypted.

## Configuration Steps

### Step 1: Get Your Cloudflare Domain

After setting up your Cloudflare tunnel to DGX Spark, you'll receive a domain URL in one of these formats:
- **Custom Domain**: `https://vaultmind.yourdomain.com`
- **Cloudflare Tunnel URL**: `https://dgx-spark-xxxxx.cloudflareaccess.com` or similar
- **Cloudflare Workers URL**: `https://dgx.your-tunnel.workers.dev`

### Step 2: Update Environment Variables

Replace `https://vaultmind.yourdomain.com` in these files with your actual Cloudflare domain:

#### Backend (DGX): `rag_backend/.env`
```env
# Update this to your Cloudflare domain
NEXT_PUBLIC_API_URL=https://vaultmind.yourdomain.com

# Update CORS to include your Cloudflare domain
CORS_ORIGINS=["http://localhost:3000","http://localhost:3001","https://onboarding-guide-three.vercel.app","https://vaultmind.yourdomain.com"]
```

#### Frontend (Vercel): `.env.production`
```env
CLOUDFLARE_BACKEND_URL=https://vaultmind.yourdomain.com
DGX_BACKEND_URL=https://vaultmind.yourdomain.com
```

### Step 3: Verify Cloudflare Tunnel Configuration

Your Cloudflare tunnel should route to:
- **Protocol**: HTTPS (or HTTP with Cloudflare terminating HTTPS)
- **Target**: `http://192.168.18.199:8000` (internal FastAPI backend)

Example tunnel configuration:
```
Service: http://192.168.18.199:8000
Public Hostname: vaultmind.yourdomain.com
```

### Step 4: Deploy Changes

```bash
# Commit and push configuration changes
git add rag_backend/.env .env.production app/api/proxy
git commit -m "feat: HTTPS via Cloudflare tunnel"
git push origin main

# Vercel will auto-redeploy
# For DGX backend: SSH and restart services
ssh admin@192.168.18.199
cd /home/admin/onboarding_guide/rag_backend
docker compose down
docker compose up -d
```

### Step 5: Test HTTPS Connection

```bash
# Test backend health endpoint
curl https://vaultmind.yourdomain.com/health

# Test authentication
curl -X POST https://vaultmind.yourdomain.com/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@vaultmind.local&password=admin123"

# Test from browser
# Navigate to: https://onboarding-guide-three.vercel.app/login
# Login with: admin@vaultmind.local / admin123
```

## What Changed

### Proxy Enhancement (`app/api/proxy/[...path]/route.ts`)
- Now supports Cloudflare HTTPS domain via `CLOUDFLARE_BACKEND_URL` environment variable
- Maintains backward compatibility with direct HTTP URLs
- Vercel server proxies HTTPS requests to your backend

### FastAPI CORS (`rag_backend/app/main.py`)
- Added `TrustedHostMiddleware` for Cloudflare proxy headers
- Updated CORS to accept HTTPS origins
- Added security headers (HSTS, X-Content-Type-Options, etc.)

### Environment Configuration
- Backend now expects HTTPS URLs
- CORS whitelist includes your Cloudflare domain
- Internal services (ChromaDB, Redis, Ollama) remain on HTTP (correct for internal networks)

## Security Notes

1. **HTTPS Termination**: Cloudflare provides HTTPS termination at the edge
2. **Tunnel Encryption**: Cloudflare tunnel encrypts traffic from tunnel endpoint to origin
3. **CORS Security**: Only whitelisted origins can call backend
4. **Browser Mixed Content**: All requests go through Vercel proxy (HTTPS) before reaching backend

## Troubleshooting

### "Mixed Content" Error
- Ensure `.env.production` has `CLOUDFLARE_BACKEND_URL` set to HTTPS domain
- Clear browser cache and hard refresh (Ctrl+Shift+R)

### "Connection Refused"
- Verify Cloudflare tunnel is active: `cloudflared tunnel list`
- Check tunnel target: `http://192.168.18.199:8000`
- Verify DGX backend is running: `ssh admin@192.168.18.199 docker ps`

### "CORS Error"
- Ensure Cloudflare domain is in `CORS_ORIGINS` in `rag_backend/.env`
- Restart backend after `.env` changes: `docker compose down && docker compose up -d`

### "401 Unauthorized"
- User accounts are seeded on backend startup
- Default admin: `admin@vaultmind.local` / `admin123`
- Check backend logs: `docker compose logs api`

## Rollback to HTTP (for internal-only deployment)

If you need to revert to HTTP for internal testing:

1. Update `.env.production`:
   ```env
   DGX_BACKEND_URL=http://192.168.18.199:8000
   ```

2. Restart Vercel deployment: `vercel --prod`

3. SSH to DGX and restart backend: `docker compose restart api`

## Additional Resources

- [Cloudflare Tunnel Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
- [FastAPI CORS Documentation](https://fastapi.tiangolo.com/tutorial/cors/)
- [VaultMind Deployment Guide](./DGX_DEPLOYMENT_GUIDE.md)
