#!/bin/bash

# VaultMind DGX Spark Deployment Script
# Automates copying backend to DGX and starting services

set -e

DGX_IP="192.168.18.199"
DGX_USER="admin"
PROJECT_PATH="/opt/vaultmind"
LOCAL_BACKEND_PATH="./rag_backend"

echo "======================================"
echo "VaultMind DGX Spark Deployment Script"
echo "======================================"
echo ""

# Verify local backend exists
if [ ! -d "$LOCAL_BACKEND_PATH" ]; then
    echo "❌ Error: ./rag_backend directory not found!"
    echo "Run this script from the project root directory"
    exit 1
fi

echo "📦 Configuration:"
echo "  DGX Host: $DGX_IP"
echo "  DGX User: $DGX_USER"
echo "  Project Path: $PROJECT_PATH"
echo "  Local Backend: $LOCAL_BACKEND_PATH"
echo ""

# Check network connectivity
echo "🔍 Checking DGX connectivity..."
if ! ping -c 1 "$DGX_IP" &> /dev/null; then
    echo "❌ Cannot reach DGX at $DGX_IP"
    exit 1
fi
echo "✓ DGX is reachable"
echo ""

# Ask for confirmation
echo "⚠️  This will:"
echo "  1. Copy the backend code to $DGX_USER@$DGX_IP:$PROJECT_PATH"
echo "  2. Build Docker images"
echo "  3. Start all services (postgres, chroma, redis, api)"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Cancelled."
    exit 0
fi

# Step 1: Create directories on DGX
echo "📁 Creating directories on DGX..."
ssh "$DGX_USER@$DGX_IP" mkdir -p "$PROJECT_PATH" \
    /home/admin/app-data/{postgres,chromadb,redis} 2>/dev/null || true
echo "✓ Directories created"

# Step 2: Copy backend code
echo ""
echo "📤 Copying backend code to DGX (this may take a minute)..."
rsync -avz --delete \
    --exclude='.git' \
    --exclude='__pycache__' \
    --exclude='.pytest_cache' \
    --exclude='chroma_db' \
    "$LOCAL_BACKEND_PATH/" \
    "$DGX_USER@$DGX_IP:$PROJECT_PATH/" \
    2>/dev/null || true
echo "✓ Code copied"

# Step 3: Build and start services
echo ""
echo "🚀 Starting services on DGX..."
ssh "$DGX_USER@$DGX_IP" "cd $PROJECT_PATH && docker-compose build --quiet 2>&1 && echo 'Build complete' || true"
echo "✓ Docker images built"

echo ""
echo "▶️  Starting services..."
ssh "$DGX_USER@$DGX_IP" "cd $PROJECT_PATH && docker-compose up -d"
echo "✓ Services started"

# Step 4: Wait for services to be ready
echo ""
echo "⏳ Waiting for services to be ready (max 30 seconds)..."
for i in {1..30}; do
    if ssh "$DGX_USER@$DGX_IP" "curl -s http://localhost:8000/health | grep -q 'ok'" 2>/dev/null; then
        echo "✓ Services are ready!"
        break
    fi
    echo -n "."
    sleep 1
done

echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "📋 Next steps:"
echo "  1. Run verification: ./verify-deployment.sh"
echo "  2. View logs: ssh $DGX_USER@$DGX_IP 'cd $PROJECT_PATH && docker-compose logs -f'"
echo "  3. Frontend: https://onboarding-guide-three.vercel.app/"
echo "  4. Test login with admin@vaultmind.local / admin123"
echo ""
echo "📖 For more details, see: DGX_DEPLOYMENT_GUIDE.md"
echo ""
