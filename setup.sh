#!/bin/bash

# ==============================================================================
# 🚀 APEX-OMEGA TITAN: AUTOMATED SETUP SCRIPT
# ==============================================================================
# This script automates the complete installation and setup of Titan
# Run: chmod +x setup.sh && ./setup.sh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   APEX-OMEGA TITAN: AUTOMATED SETUP${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Function to print status messages
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

print_info() {
    echo -e "${BLUE}[i]${NC} $1"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Prerequisites
echo -e "${BLUE}[1/9] Checking Prerequisites...${NC}"

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node -v)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install Node.js 18+ from https://nodejs.org/"
    exit 1
fi

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.11+ from https://python.org/"
    exit 1
fi

# Check pip
if command_exists pip3; then
    print_status "pip3 found"
else
    print_error "pip3 not found. Please install pip"
    exit 1
fi

# Check Redis
if command_exists redis-server; then
    print_status "Redis found"
else
    print_warning "Redis not found. Installing Redis is recommended."
    print_info "Ubuntu/Debian: sudo apt install redis-server"
    print_info "macOS: brew install redis"
    print_info "Visit: https://redis.io/download"
fi

echo ""

# Step 2: Install Node.js Dependencies
echo -e "${BLUE}[2/9] Installing Node.js Dependencies...${NC}"
if [ -f "package.json" ]; then
    # Check if Yarn is available (better dependency resolution)
    if command_exists yarn; then
        print_status "Using Yarn for better dependency conflict resolution"
        yarn install
        print_status "Node.js dependencies installed via Yarn"
    else
        # Note: --legacy-peer-deps is used to resolve ethers.js version conflict
        # between hardhat-toolbox (requires ^6.14.0) and flashbots-provider (requires 6.7.1)
        # This is a known compatibility issue and is safe for our use case
        print_status "Using npm with --legacy-peer-deps flag"
        npm install --legacy-peer-deps
        print_status "Node.js dependencies installed via npm"
        print_info "Tip: Install Yarn for better dependency resolution: npm install -g yarn"
    fi
else
    print_error "package.json not found"
    exit 1
fi
echo ""

# Step 3: Install Python Dependencies
echo -e "${BLUE}[3/9] Installing Python Dependencies...${NC}"
if [ -f "requirements.txt" ]; then
    pip3 install -r requirements.txt
    print_status "Python dependencies installed"
else
    print_error "requirements.txt not found"
    exit 1
fi
echo ""

# Step 4: Compile Smart Contracts
echo -e "${BLUE}[4/9] Compiling Smart Contracts...${NC}"
npx hardhat compile
if [ $? -eq 0 ]; then
    print_status "Smart contracts compiled successfully"
else
    print_error "Smart contract compilation failed"
    exit 1
fi
echo ""

# Step 5: Setup Environment File
echo -e "${BLUE}[5/9] Setting Up Environment Configuration...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Created .env from template"
        print_warning "IMPORTANT: Edit .env file with your API keys and private key"
        print_info "Required: PRIVATE_KEY, RPC endpoints, LIFI_API_KEY"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_status ".env already exists"
fi
echo ""

# Step 6: Check Redis Connection
echo -e "${BLUE}[6/9] Verifying Redis Connection...${NC}"
if command_exists redis-cli; then
    if redis-cli ping >/dev/null 2>&1; then
        print_status "Redis is running and accessible"
    else
        print_warning "Redis is not running. Starting Redis is required before running Titan."
        print_info "Start with: redis-server"
        print_info "Or: brew services start redis (macOS)"
        print_info "Or: sudo systemctl start redis (Linux)"
    fi
else
    print_warning "redis-cli not found. Cannot verify Redis connection."
fi
echo ""

# Step 7: Create Data Directories
echo -e "${BLUE}[7/9] Creating Data Directories...${NC}"
mkdir -p data
mkdir -p logs
mkdir -p certs
print_status "Data directories created"
echo ""

# Step 8: Run System Audit
echo -e "${BLUE}[8/9] Running System Audit...${NC}"
if [ -f "audit_system.py" ]; then
    python3 audit_system.py
    if [ $? -eq 0 ]; then
        print_status "System audit passed"
    else
        print_warning "System audit completed with warnings"
    fi
else
    print_warning "audit_system.py not found, skipping audit"
fi
echo ""

# Step 9: Display Next Steps
echo -e "${BLUE}[9/9] Setup Complete!${NC}"
echo ""
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}   ✅ SETUP COMPLETED SUCCESSFULLY${NC}"
echo -e "${GREEN}===================================================${NC}"
echo ""
echo -e "${YELLOW}NEXT STEPS:${NC}"
echo ""
echo "1. Configure your environment:"
echo -e "   ${BLUE}nano .env${NC}"
echo "   - Add your PRIVATE_KEY (from a dedicated wallet)"
echo "   - Add RPC provider API keys (Infura/Alchemy)"
echo "   - Add LIFI_API_KEY for cross-chain operations"
echo ""
echo "2. Deploy the smart contract:"
echo -e "   ${BLUE}npx hardhat run scripts/deploy.js --network polygon${NC}"
echo "   - Copy the deployed address to .env as EXECUTOR_ADDRESS_POLYGON"
echo ""
echo "3. Start Redis (if not running):"
echo -e "   ${BLUE}redis-server${NC}"
echo ""
echo "4. Start the system:"
echo "   Option A - All components:"
echo -e "     ${BLUE}./start.sh${NC}"
echo ""
echo "   Option B - Manual (3 separate terminals):"
echo -e "     Terminal 1: ${BLUE}redis-server${NC}"
echo -e "     Terminal 2: ${BLUE}python3 ml/brain.py${NC}"
echo -e "     Terminal 3: ${BLUE}node execution/bot.js${NC}"
echo ""
echo "For detailed instructions, see QUICKSTART.md"
echo ""
echo -e "${YELLOW}⚠️  SECURITY REMINDER:${NC}"
echo "- Never commit your .env file to git"
echo "- Use a dedicated wallet with limited funds"
echo "- Test on testnets before mainnet deployment"
echo ""
