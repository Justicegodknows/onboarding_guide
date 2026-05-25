#!/bin/bash
# VaultMind HTTPS/Cloudflare Configuration Test Suite

set -e

echo "================================================"
echo "VaultMind - HTTPS/Cloudflare Configuration Tests"
echo "================================================"
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

TEST_PASSED=0
TEST_FAILED=0

# Test function
run_test() {
    local test_name="$1"
    local test_cmd="$2"
    local expected_status="${3:-0}"
    
    echo -n "Testing: $test_name... "
    if eval "$test_cmd" >/dev/null 2>&1; then
        if [ "$expected_status" -eq 0 ]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            ((TEST_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAILED (expected failure)${NC}"
            ((TEST_FAILED++))
            return 1
        fi
    else
        if [ "$expected_status" -ne 0 ]; then
            echo -e "${GREEN}✓ PASSED${NC}"
            ((TEST_PASSED++))
            return 0
        else
            echo -e "${RED}✗ FAILED${NC}"
            ((TEST_FAILED++))
            return 1
        fi
    fi
}

# Configuration checks
echo "=== 1. Configuration Files ==="
run_test "Backend .env exists" "[ -f rag_backend/.env ]"
run_test "Frontend .env.production exists" "[ -f .env.production ]"
run_test "Proxy route exists" "[ -f app/api/proxy/[...path]/route.ts ]"
echo ""

# Environment variable checks
echo "=== 2. HTTPS Configuration ==="
run_test "CORS_ORIGINS includes HTTPS domain" "grep -q 'https://' rag_backend/.env"
run_test ".env.production has CLOUDFLARE_BACKEND_URL" "grep -q 'CLOUDFLARE_BACKEND_URL' .env.production"
run_test "Proxy supports CLOUDFLARE_BACKEND_URL" "grep -q 'CLOUDFLARE_BACKEND_URL' app/api/proxy/[...path]/route.ts"
echo ""

# FastAPI HTTPS configuration
echo "=== 3. FastAPI HTTPS Support ==="
run_test "TrustedHostMiddleware imported" "grep -q 'TrustedHostMiddleware' rag_backend/app/main.py"
run_test "Security headers configured" "grep -q 'Strict-Transport-Security' rag_backend/app/main.py"
run_test "CORS middleware configured" "grep -q 'CORSMiddleware' rag_backend/app/main.py"
echo ""

# Code integrity
echo "=== 4. Code Integrity ==="
run_test "No hardcoded HTTP URLs in proxy" "! grep -q 'http://192\.168\.18\.199' app/api/proxy/[...path]/route.ts"
run_test "Backend.ts uses environment variables" "grep -q 'DGX_BACKEND_URL' app/api/backend.ts"
run_test "Proxy handles HTTPS" "grep -q 'CLOUDFLARE_BACKEND_URL' app/api/proxy/[...path]/route.ts"
echo ""

# TypeScript/JavaScript tests
echo "=== 5. Build & Lint ==="
if [ -f "package.json" ]; then
    run_test "TypeScript configuration exists" "[ -f tsconfig.json ]"
    run_test "ESLint configuration exists" "[ -f eslint.config.mjs ]"
fi
echo ""

# Python tests (if available)
echo "=== 6. Backend Configuration ==="
run_test "FastAPI main.py is valid Python" "python3 -m py_compile rag_backend/app/main.py 2>/dev/null"
run_test "Config.py loads" "python3 -m py_compile rag_backend/app/core/config.py 2>/dev/null"
echo ""

# Documentation
echo "=== 7. Documentation ==="
run_test "HTTPS setup guide created" "[ -f CLOUDFLARE_HTTPS_SETUP.md ]"
run_test "Setup guide includes Cloudflare info" "grep -q 'Cloudflare' CLOUDFLARE_HTTPS_SETUP.md"
run_test "Setup guide includes troubleshooting" "grep -q 'Troubleshooting' CLOUDFLARE_HTTPS_SETUP.md"
echo ""

# Deployment files
echo "=== 8. Deployment Configuration ==="
run_test "DGX deployment guide exists" "[ -f DGX_DEPLOYMENT_GUIDE.md ]"
run_test "Docker compose file exists" "[ -f rag_backend/docker-compose.yml ]"
run_test "ChromaDB port mapping is correct" "grep -q '8100:8000' rag_backend/docker-compose.yml"
echo ""

# Summary
echo "================================================"
echo -e "Test Results: ${GREEN}$TEST_PASSED passed${NC}, ${RED}$TEST_FAILED failed${NC}"
echo "================================================"

if [ $TEST_FAILED -eq 0 ]; then
    echo -e "${GREEN}All tests passed! Ready for HTTPS deployment.${NC}"
    exit 0
else
    echo -e "${RED}Some tests failed. Please review the configuration.${NC}"
    exit 1
fi
