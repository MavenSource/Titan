#!/bin/bash

# ==============================================================================
# 🚀 APEX-OMEGA TITAN: ONE-CLICK INSTALL AND RUN
# ==============================================================================
# This script installs all dependencies and starts the Titan system
# Prerequisites: Node.js, Python, Git must be installed
# Configuration: Edit .env file before running
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# ==============================================================================
# UTILITY FUNCTIONS
# ==============================================================================

print_banner() {
    echo -e "${BLUE}================================================================${NC}"
    echo -e "${CYAN}   🚀 APEX-OMEGA TITAN: ONE-CLICK INSTALL & RUN${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

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

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# ==============================================================================
# MAIN SCRIPT
# ==============================================================================

print_banner

echo "This script will:"
echo "  1. Install Node.js dependencies"
echo "  2. Install Python dependencies"
echo "  3. Compile smart contracts"
echo "  4. Start the Titan system"
echo ""
echo "Make sure you have configured .env file first!"
echo ""

# ==============================================================================
# STEP 1: CHECK PREREQUISITES
# ==============================================================================

echo ""
print_info "STEP 1/5: Checking prerequisites..."
echo ""

if command_exists node; then
    NODE_VERSION=$(node --version)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found. Please install from https://nodejs.org/"
    exit 1
fi

if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
elif command_exists python; then
    PYTHON_VERSION=$(python --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python not found. Please install from https://python.org/"
    exit 1
fi

if command_exists pip3; then
    print_status "pip3 found"
    PIP_CMD="pip3"
elif command_exists pip; then
    print_status "pip found"
    PIP_CMD="pip"
else
    print_error "pip not found. Please install with Python"
    exit 1
fi

# ==============================================================================
# STEP 2: CHECK .env FILE
# ==============================================================================

echo ""
print_info "STEP 2/5: Checking configuration..."
echo ""

if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_status ".env file created from .env.example"
        echo ""
        print_warning "IMPORTANT: Edit .env file with your configuration before continuing!"
        echo "  - Add your PRIVATE_KEY"
        echo "  - Add RPC endpoints (Infura/Alchemy API keys)"
        echo "  - Add LIFI_API_KEY"
        echo "  - Configure EXECUTION_MODE (PAPER or LIVE)"
        echo ""
        read -p "Press Enter after you've configured .env file..."
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_status ".env file exists"
fi

# ==============================================================================
# STEP 3: INSTALL NODE.JS DEPENDENCIES
# ==============================================================================

echo ""
print_info "STEP 3/5: Installing Node.js dependencies..."
echo ""

# Try yarn first, fall back to npm
if command_exists yarn; then
    print_info "Using Yarn..."
    yarn install
else
    print_info "Using npm..."
    npm install --legacy-peer-deps
fi

print_status "Node.js dependencies installed"

# ==============================================================================
# STEP 4: INSTALL PYTHON DEPENDENCIES
# ==============================================================================

echo ""
print_info "STEP 4/5: Installing Python dependencies..."
echo ""

if ! $PIP_CMD install -r requirements.txt; then
    print_error "Failed to install Python dependencies"
    exit 1
fi

print_status "Python dependencies installed"

# ==============================================================================
# STEP 5: COMPILE SMART CONTRACTS
# ==============================================================================

echo ""
print_info "STEP 5/5: Compiling smart contracts..."
echo ""

if ! npx hardhat compile; then
    print_error "Failed to compile smart contracts"
    exit 1
fi

print_status "Smart contracts compiled"

# ==============================================================================
# START THE SYSTEM
# ==============================================================================

echo ""
echo -e "${BLUE}================================================================${NC}"
echo -e "${GREEN}   INSTALLATION COMPLETE!${NC}"
echo -e "${BLUE}================================================================${NC}"
echo ""
echo "Starting Titan system..."
echo ""

# Make start script executable
chmod +x start.sh

# Start the system
./start.sh
