# VaultMind DGX Deployment - Quick Reference

## System Configuration
- **DGX Spark IP**: 192.168.18.199
- **Frontend**: https://onboarding-guide-three.vercel.app/
- **Backend API**: http://192.168.18.199:8000

## Service Ports (All on DGX)
| Service | Port | Status |
|---------|------|--------|
| FastAPI Backend | 8000 | ✓ Configured |
| PostgreSQL | 5432 | ✓ Configured |
| ChromaDB | 8100 | ✓ Configured |
| Redis | 6379 | ✓ Configured |
| Ollama | 11434 | ✓ Configured |

## Files Changed
- [x] `rag_backend/.env` - DGX configuration
- [x] `rag_backend/docker-compose.yml` - Persistent volumes & DGX endpoints
- [x] `rag_backend/app/main.py` - CORS whitelist
- [x] `.env.production` - Frontend production config

## New Documentation
- `DGX_DEPLOYMENT_GUIDE.md` - Full deployment guide
- `DEPLOYMENT_SUMMARY.md` - Migration summary
- `deploy-to-dgx.sh` - Deployment automation
- `verify-deployment.sh` - Validation script

## 🚀 Deployment Command
```bash
# From project root
./deploy-to-dgx.sh
```

## ✅ Verification Command
```bash
./verify-deployment.sh
```

## 🔍 Check Services
```bash
# SSH to DGX
ssh admin@192.168.18.199

# View status
cd /opt/vaultmind && docker-compose ps

# View logs
docker-compose logs -f api
```

## 🧪 Test Endpoints
```bash
# Health check
curl http://192.168.18.199:8000/health

# Get available Ollama models
curl http://192.168.18.199:11434/api/tags

# Test login
curl -X POST http://192.168.18.199:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@vaultmind.local","password":"admin123"}'
```

## 📊 Default Test Credentials
- **Email**: admin@vaultmind.local
- **Password**: admin123

## 🔐 Security Notes
- Change PostgreSQL password from "postgres" in production
- Consider SSL/HTTPS setup (see DGX_DEPLOYMENT_GUIDE.md)
- Restrict firewall to limit DGX access
- Backup data regularly (see guide)

## 📈 Expected Performance
- **LLM Response**: 2-30 seconds (depending on model/query)
- **Database Query**: < 200ms
- **Vector Search**: < 500ms
- **Frontend Load**: < 2 seconds

## 🛠️ Troubleshooting Quick Fixes
```bash
# Port already in use?
netstat -tuln | grep LISTEN

# Services won't start?
docker-compose logs api | tail -50

# Network issues?
ping 192.168.18.199

# Restart all services?
docker-compose restart
```

## 📋 Pre-Deployment Checklist
- [ ] SSH access to DGX (192.168.18.199)
- [ ] Docker installed on DGX
- [ ] Ollama running on port 11434
- [ ] Directories created: `/home/admin/app-data/{postgres,chromadb,redis}`
- [ ] Network connectivity from frontend to DGX
- [ ] Vercel project ready to deploy

## 🔄 Development Mode
Switch back to local development:
```bash
# 1. Stop DGX
ssh admin@192.168.18.199 'cd /opt/vaultmind && docker-compose down'

# 2. Start local backend
cd ./rag_backend && docker-compose up -d

# 3. Frontend uses .env.local automatically
```

## 📞 Support Resources
1. **Full Guide**: `DGX_DEPLOYMENT_GUIDE.md`
2. **Summary**: `DEPLOYMENT_SUMMARY.md`
3. **Scripts**: `deploy-to-dgx.sh`, `verify-deployment.sh`
4. **CLAUDE.md**: Project constraints & best practices
5. **README.md**: Product documentation

---

**Status**: ✅ Ready for Deployment
**Configuration Date**: May 22, 2026
**No Breaking Changes**: ✓ Fully backward compatible
