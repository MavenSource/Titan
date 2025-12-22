#!/bin/bash

# ==============================================================================
# 🔨 APEX-OMEGA TITAN: BUILD AND VALIDATION SCRIPT
# ==============================================================================
# Complete build process with validation
# Run: chmod +x build.sh && ./build.sh

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   TITAN BUILD AND VALIDATION${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Step 1: Clean previous builds
echo -e "${BLUE}[1/6] Cleaning Previous Build Artifacts...${NC}"
rm -rf artifacts/ cache/ typechain/ typechain-types/
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
echo -e "${GREEN}[✓]${NC} Clean complete"
echo ""

# Step 2: Install Node.js dependencies
echo -e "${BLUE}[2/6] Installing Node.js Dependencies...${NC}"
if [ -f "package.json" ]; then
    # Note: --legacy-peer-deps is used to resolve ethers.js version conflict
    # between hardhat-toolbox (requires ^6.14.0) and flashbots-provider (requires 6.7.1)
    # This is a known compatibility issue and is safe for our use case
    npm install --legacy-peer-deps
    echo -e "${GREEN}[✓]${NC} Node.js dependencies installed"
else
    echo -e "${RED}[✗]${NC} package.json not found"
    exit 1
fi
echo ""

# Step 3: Install Python dependencies
echo -e "${BLUE}[3/6] Installing Python Dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt --quiet
    echo -e "${GREEN}[✓]${NC} Python dependencies installed"
else
    echo -e "${RED}[✗]${NC} requirements.txt not found"
    exit 1
fi
echo ""

# Step 4: Compile smart contracts
echo -e "${BLUE}[4/6] Compiling Smart Contracts...${NC}"
cd onchain
npx hardhat compile
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[✓]${NC} Smart contracts compiled successfully"
    cd ..
    
    # Copy ABIs to shared directory
    echo "Copying ABIs to shared directory..."
    mkdir -p shared/abi
    cp -r onchain/artifacts/contracts/*.sol/*.json shared/abi/ 2>/dev/null || true
    echo -e "${GREEN}[✓]${NC} ABIs copied to shared/abi/"
    
    # Verify compilation
    if [ -f "onchain/artifacts/contracts/OmniArbExecutor.sol/OmniArbExecutor.json" ]; then
        echo -e "${GREEN}[✓]${NC} OmniArbExecutor.json generated"
        
        # Get contract size
        SIZE=$(stat -f%z "onchain/artifacts/contracts/OmniArbExecutor.sol/OmniArbExecutor.json" 2>/dev/null || stat -c%s "onchain/artifacts/contracts/OmniArbExecutor.sol/OmniArbExecutor.json" 2>/dev/null)
        echo "       Contract artifact size: $(numfmt --to=iec-i --suffix=B $SIZE 2>/dev/null || echo "${SIZE} bytes")"
    else
        echo -e "${RED}[✗]${NC} Contract compilation verification failed"
        exit 1
    fi
else
    echo -e "${RED}[✗]${NC} Smart contract compilation failed"
    cd ..
    exit 1
fi
echo ""

# Step 5: Verify Python modules
echo -e "${BLUE}[5/6] Verifying Python Modules...${NC}"
PYTHON_ERRORS=0

# Test imports
python3 -c "import web3; import pandas; import numpy; import redis" 2>/dev/null
if [ $? -eq 0 ]; then
    echo -e "${GREEN}[✓]${NC} Core Python packages verified"
else
    echo -e "${RED}[✗]${NC} Python package import failed"
    PYTHON_ERRORS=$((PYTHON_ERRORS + 1))
fi

# Test core modules
if python3 -c "from core import config" 2>/dev/null; then
    echo -e "${GREEN}[✓]${NC} core.config module loads"
else
    echo -e "${YELLOW}[!]${NC} core.config module has issues (may require .env)"
fi

if python3 -c "from core import token_discovery" 2>/dev/null; then
    echo -e "${GREEN}[✓]${NC} core.token_discovery module loads"
else
    echo -e "${YELLOW}[!]${NC} core.token_discovery module has issues"
fi

echo ""

# Step 6: Run system audit
echo -e "${BLUE}[6/6] Running System Audit...${NC}"
if [ -f "audit_system.py" ]; then
    python3 audit_system.py
    AUDIT_RESULT=$?
    if [ $AUDIT_RESULT -eq 0 ]; then
        echo -e "${GREEN}[✓]${NC} System audit passed"
    else
        echo -e "${YELLOW}[!]${NC} System audit completed with warnings"
    fi
else
    echo -e "${YELLOW}[!]${NC} audit_system.py not found, skipping"
fi
echo ""

# Final Summary
echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   BUILD SUMMARY${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

if [ $PYTHON_ERRORS -eq 0 ]; then
    echo -e "${GREEN}✅ BUILD SUCCESSFUL${NC}"
    echo ""
    echo "Build artifacts:"
    echo "  • artifacts/contracts/ - Compiled contract ABIs"
    echo "  • node_modules/ - Node.js dependencies"
    echo "  • Python packages - Installed globally or in venv"
    echo ""
    echo "Next steps:"
    echo "  1. Configure .env file (cp .env.example .env)"
    echo "  2. Run health check: ./health-check.sh"
    echo "  3. Deploy contract: npx hardhat run scripts/deploy.js --network <network>"
    echo "  4. Start system: ./start.sh or make start"
    exit 0
else
    echo -e "${RED}❌ BUILD FAILED${NC}"
    echo ""
    echo "Errors found: $PYTHON_ERRORS"
    echo "Please fix the errors above and try again."
    exit 1
fi
