#!/bin/bash

# VaultMind DGX Spark Deployment Verification Script
# Run this from the frontend machine to verify all components are working

set -e

DGX_IP="192.168.18.199"
FRONTEND_URL="https://onboarding-guide-three.vercel.app"

echo "======================================"
echo "VaultMind DGX Deployment Verification"
echo "======================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

check_endpoint() {
    local name=$1
    local endpoint=$2
    local expected_code=$3
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$endpoint" 2>/dev/null || echo "000")
    
    if [ "$response" == "$expected_code" ] || [ "$response" == "200" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        return 1
    fi
}

check_port() {
    local name=$1
    local host=$2
    local port=$3
    
    echo -n "Checking $name ($host:$port)... "
    
    if nc -z -w 2 "$host" "$port" 2>/dev/null; then
        echo -e "${GREEN}✓ Open${NC}"
        return 0
    else
        echo -e "${RED}✗ Closed${NC}"
        return 1
    fi
}

# Check network connectivity
echo "=== Network Connectivity ==="
echo -n "Ping DGX ($DGX_IP)... "
if ping -c 1 "$DGX_IP" &> /dev/null; then
    echo -e "${GREEN}✓ Reachable${NC}"
else
    echo -e "${RED}✗ Unreachable${NC}"
    exit 1
fi
echo ""

# Check ports
echo "=== Service Ports ==="
check_port "FastAPI Backend" "$DGX_IP" "8000"
check_port "PostgreSQL" "$DGX_IP" "5432"
check_port "ChromaDB" "$DGX_IP" "8100"
check_port "Redis" "$DGX_IP" "6379"
check_port "Ollama" "$DGX_IP" "11434"
echo ""

# Check API endpoints
echo "=== API Endpoints ==="
check_endpoint "Backend Health" "http://$DGX_IP:8000/health" "200"
check_endpoint "Frontend" "$FRONTEND_URL" "200"
echo ""

# Check specific services
echo "=== Service Status ==="

echo -n "Ollama Models... "
models=$(curl -s "http://$DGX_IP:11434/api/tags" | grep -o '"name":"[^"]*"' | wc -l)
if [ "$models" -gt 0 ]; then
    echo -e "${GREEN}✓ Found $models models${NC}"
else
    echo -e "${RED}✗ No models found${NC}"
fi

echo -n "PostgreSQL Connection... "
response=$(curl -s -X POST "http://$DGX_IP:8000/auth/login" \
    -H "Content-Type: application/json" \
    -d '{"email":"test","password":"test"}' || echo "failed")
if echo "$response" | grep -q "error\|detail"; then
    echo -e "${GREEN}✓ Database responding${NC}"
else
    echo -e "${YELLOW}? Check manually${NC}"
fi

echo ""
echo "=== Summary ==="
echo -e "${GREEN}If all checks pass, deployment is ready!${NC}"
echo ""
echo "Next steps:"
echo "1. SSH to DGX: ssh admin@$DGX_IP"
echo "2. Navigate to project: cd /opt/vaultmind"
echo "3. Start services: docker-compose up -d"
echo "4. View logs: docker-compose logs -f"
echo ""
echo "Test frontend at: $FRONTEND_URL"
echo "Try login with:"
echo "  Email: admin@vaultmind.local"
echo "  Password: admin123"
echo ""
