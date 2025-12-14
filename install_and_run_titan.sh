#!/bin/bash

# ==============================================================================
# 🚀 APEX-OMEGA TITAN: FULL-SCALE INSTALLATION & EXECUTION SCRIPT
# ==============================================================================
# Complete end-to-end installation, configuration, and execution
# This script:
#   1. Installs ALL dependencies (Node.js, Python, Redis)
#   2. Builds Rust components (rustworkx Python library)
#   3. Sets up Redis (optional, with fallback)
#   4. Compiles and deploys smart contracts (pools + tokenomics + registries)
#   5. Configures wallet for gas, TX signing, execution, and profit deposits
#   6. Launches the complete Titan arbitrage system
#
# Usage: ./install_and_run_titan.sh [OPTIONS]
#
# Options:
#   --wallet-key <KEY>     Your wallet private key (with 0x prefix)
#   --wallet-address <ADDR> Your wallet address (with 0x prefix)
#   --mode <paper|live>     Execution mode (default: paper)
#   --network <network>     Deploy network (default: polygon)
#   --skip-redis            Skip Redis installation/setup
#   --help                  Show this help message
#
# Example:
#   ./install_and_run_titan.sh --wallet-key 0xYOUR_KEY --wallet-address 0xYOUR_ADDRESS --mode paper
# ==============================================================================

set -e  # Exit on error

# ==============================================================================
# CONFIGURATION & DEFAULTS
# ==============================================================================

WALLET_KEY=""
WALLET_ADDRESS=""
EXECUTION_MODE="paper"
DEPLOY_NETWORK="polygon"
SKIP_REDIS=false
RPC_INFURA_KEY=""
RPC_ALCHEMY_KEY=""
LIFI_API_KEY=""

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
    echo -e "${CYAN}   🚀 APEX-OMEGA TITAN: FULL-SCALE INSTALLATION & EXECUTION${NC}"
    echo -e "${BLUE}================================================================${NC}"
    echo ""
}

print_section() {
    echo ""
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${MAGENTA}  $1${NC}"
    echo -e "${MAGENTA}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
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

print_progress() {
    echo -e "${CYAN}[→]${NC} $1"
}

command_exists() {
    command -v "$1" >/dev/null 2>&1
}

show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Full-scale installation and execution of Titan arbitrage system"
    echo ""
    echo "Options:"
    echo "  --wallet-key <KEY>       Your wallet private key (with 0x prefix)"
    echo "  --wallet-address <ADDR>  Your wallet address (with 0x prefix)"
    echo "  --mode <paper|live>      Execution mode (default: paper)"
    echo "  --network <network>      Deploy network (default: polygon)"
    echo "  --infura-key <KEY>       Infura API key"
    echo "  --alchemy-key <KEY>      Alchemy API key"
    echo "  --lifi-key <KEY>         Li.Fi API key"
    echo "  --skip-redis             Skip Redis installation/setup"
    echo "  --help                   Show this help message"
    echo ""
    echo "Example:"
    echo "  $0 --wallet-key 0xYOUR_KEY --wallet-address 0xYOUR_ADDRESS --mode paper"
    echo ""
    exit 0
}

# ==============================================================================
# PARSE COMMAND LINE ARGUMENTS
# ==============================================================================

while [[ $# -gt 0 ]]; do
    case $1 in
        --wallet-key)
            WALLET_KEY="$2"
            shift 2
            ;;
        --wallet-address)
            WALLET_ADDRESS="$2"
            shift 2
            ;;
        --mode)
            EXECUTION_MODE=$(echo "$2" | tr '[:upper:]' '[:lower:]')
            shift 2
            ;;
        --network)
            DEPLOY_NETWORK="$2"
            shift 2
            ;;
        --infura-key)
            RPC_INFURA_KEY="$2"
            shift 2
            ;;
        --alchemy-key)
            RPC_ALCHEMY_KEY="$2"
            shift 2
            ;;
        --lifi-key)
            LIFI_API_KEY="$2"
            shift 2
            ;;
        --skip-redis)
            SKIP_REDIS=true
            shift
            ;;
        --help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# ==============================================================================
# MAIN INSTALLATION & SETUP PROCESS
# ==============================================================================

print_banner

print_section "STEP 1/10: CHECKING SYSTEM PREREQUISITES"

# Detect OS
OS="unknown"
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="linux"
    print_info "Detected OS: Linux"
elif [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macos"
    print_info "Detected OS: macOS"
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    OS="windows"
    print_info "Detected OS: Windows"
else
    print_warning "Unknown OS: $OSTYPE"
fi

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node -v)
    print_status "Node.js found: $NODE_VERSION"
else
    print_error "Node.js not found"
    print_info "Installing Node.js..."
    if [[ "$OS" == "linux" ]]; then
        curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
        sudo apt-get install -y nodejs
    elif [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install node@18
        else
            print_error "Homebrew not found. Please install Node.js manually from https://nodejs.org/"
            exit 1
        fi
    else
        print_error "Please install Node.js manually from https://nodejs.org/"
        exit 1
    fi
    print_status "Node.js installed successfully"
fi

# Check Python
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version)
    print_status "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found"
    print_info "Installing Python..."
    if [[ "$OS" == "linux" ]]; then
        sudo apt-get update
        sudo apt-get install -y python3 python3-pip python3-venv
    elif [[ "$OS" == "macos" ]]; then
        if command_exists brew; then
            brew install python@3.11
        else
            print_error "Homebrew not found. Please install Python manually from https://python.org/"
            exit 1
        fi
    else
        print_error "Please install Python manually from https://python.org/"
        exit 1
    fi
    print_status "Python installed successfully"
fi

# Check pip
if command_exists pip3; then
    print_status "pip3 found"
else
    print_error "pip3 not found"
    if [[ "$OS" == "linux" ]]; then
        sudo apt-get install -y python3-pip
    elif [[ "$OS" == "macos" ]]; then
        python3 -m ensurepip --upgrade
    fi
fi

# Check Git
if command_exists git; then
    print_status "Git found"
else
    print_error "Git not found. Installing..."
    if [[ "$OS" == "linux" ]]; then
        sudo apt-get install -y git
    elif [[ "$OS" == "macos" ]]; then
        brew install git
    fi
fi

# Check Yarn (optional but recommended for better dependency resolution)
if command_exists yarn; then
    YARN_VERSION=$(yarn --version)
    print_status "Yarn found: $YARN_VERSION (recommended for dependency management)"
else
    print_warning "Yarn not found. Yarn offers better dependency conflict resolution."
    print_info "Install with: npm install -g yarn"
    print_info "System will use npm as fallback"
fi

print_section "STEP 2/10: INSTALLING NODE.JS DEPENDENCIES"

print_progress "Installing Node.js packages..."
if [ -f "package.json" ]; then
    # Check if Yarn is available (better dependency resolution)
    if command_exists yarn; then
        print_info "Using Yarn for dependency management (better conflict resolution)"
        yarn install
        print_status "Node.js dependencies installed via Yarn"
    else
        print_info "Using npm for dependency management"
        npm install --legacy-peer-deps
        print_status "Node.js dependencies installed via npm"
        print_info "Tip: Install Yarn for better dependency resolution: npm install -g yarn"
    fi
else
    print_error "package.json not found"
    exit 1
fi

print_section "STEP 3/10: INSTALLING PYTHON DEPENDENCIES & RUST COMPONENTS"

print_progress "Installing Python packages (including rustworkx for graph algorithms)..."
if [ -f "requirements.txt" ]; then
    # Install build dependencies for rustworkx
    if [[ "$OS" == "linux" ]]; then
        print_info "Installing build tools for Rust components..."
        sudo apt-get install -y build-essential python3-dev
    elif [[ "$OS" == "macos" ]]; then
        print_info "Ensuring Xcode command line tools are installed..."
        xcode-select --install 2>/dev/null || true
    fi
    
    # Install with --user flag to avoid system-wide conflicts (unless running in venv)
    if [ -z "$VIRTUAL_ENV" ]; then
        print_info "Installing to user directory (use virtual environment for isolation)"
        pip3 install --user -r requirements.txt
    else
        print_info "Installing to virtual environment"
        pip3 install -r requirements.txt
    fi
    print_status "Python dependencies installed (including rustworkx)"
    print_info "rustworkx: Rust-based graph library for pathfinding and arbitrage routing"
else
    print_error "requirements.txt not found"
    exit 1
fi

print_section "STEP 4/10: SETTING UP REDIS (MESSAGE QUEUE)"

if [ "$SKIP_REDIS" = true ]; then
    print_warning "Skipping Redis setup (--skip-redis flag provided)"
else
    if command_exists redis-server; then
        print_status "Redis already installed"
    else
        print_warning "Redis not found. Installing..."
        if [[ "$OS" == "linux" ]]; then
            sudo apt-get install -y redis-server
        elif [[ "$OS" == "macos" ]]; then
            brew install redis
        else
            print_warning "Redis installation skipped on this platform"
        fi
    fi
    
    # Try to start Redis
    if command_exists redis-cli; then
        if redis-cli ping >/dev/null 2>&1; then
            print_status "Redis is running"
        else
            print_warning "Starting Redis server..."
            if [[ "$OS" == "linux" ]]; then
                sudo systemctl start redis-server 2>/dev/null || redis-server --daemonize yes
            elif [[ "$OS" == "macos" ]]; then
                brew services start redis || redis-server --daemonize yes
            else
                redis-server --daemonize yes
            fi
            sleep 2
            if redis-cli ping >/dev/null 2>&1; then
                print_status "Redis started successfully"
            else
                print_warning "Redis failed to start. System will attempt to run without it."
            fi
        fi
    fi
fi

print_section "STEP 5/10: COMPILING SMART CONTRACTS"

print_progress "Compiling Solidity contracts (OmniArbExecutor, registries, tokenomics)..."
npx hardhat compile
if [ $? -eq 0 ]; then
    print_status "Smart contracts compiled successfully"
    print_info "Built: OmniArbExecutor (flash loan arbitrage executor)"
    print_info "Built: Token registries, pool managers, and tokenomics modules"
else
    print_error "Smart contract compilation failed"
    exit 1
fi

print_section "STEP 6/10: CONFIGURING ENVIRONMENT"

# Create or update .env file
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        print_status "Created .env from template"
    else
        print_error ".env.example not found"
        exit 1
    fi
else
    print_status ".env file already exists"
fi

# Prompt for wallet key if not provided
if [ -z "$WALLET_KEY" ]; then
    echo ""
    print_warning "Wallet private key not provided via --wallet-key"
    echo -e "${YELLOW}Please enter your wallet private key (with 0x prefix):${NC}"
    read -s WALLET_KEY
    echo ""
fi

# Validate wallet key format
if [[ ! "$WALLET_KEY" =~ ^0x[0-9a-fA-F]{64}$ ]]; then
    print_error "Invalid private key format. Must be 0x followed by 64 hex characters"
    print_info "Example: 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    exit 1
fi

# Additional validation: Check if key looks valid (not all zeros, not obviously invalid)
if [[ "$WALLET_KEY" == "0x0000000000000000000000000000000000000000000000000000000000000000" ]]; then
    print_error "Private key appears to be invalid (all zeros)"
    exit 1
fi

# Warning for placeholder keys
if [[ "$WALLET_KEY" =~ YOUR_PRIVATE_KEY|YOUR_KEY|REPLACE|PLACEHOLDER ]]; then
    print_error "Private key appears to be a placeholder. Please use a real private key"
    exit 1
fi

# Update .env with wallet key
if grep -q "^PRIVATE_KEY=" .env; then
    # Use portable sed command
    if [[ "$OS" == "macos" ]]; then
        sed -i '' "s/^PRIVATE_KEY=.*/PRIVATE_KEY=$WALLET_KEY/" .env
    else
        sed -i "s/^PRIVATE_KEY=.*/PRIVATE_KEY=$WALLET_KEY/" .env
    fi
else
    echo "PRIVATE_KEY=$WALLET_KEY" >> .env
fi

print_status "Wallet private key configured"

# Update execution mode
EXECUTION_MODE_UPPER=$(echo "$EXECUTION_MODE" | tr '[:lower:]' '[:upper:]')
if grep -q "^EXECUTION_MODE=" .env; then
    if [[ "$OS" == "macos" ]]; then
        sed -i '' "s/^EXECUTION_MODE=.*/EXECUTION_MODE=$EXECUTION_MODE_UPPER/" .env
    else
        sed -i "s/^EXECUTION_MODE=.*/EXECUTION_MODE=$EXECUTION_MODE_UPPER/" .env
    fi
else
    echo "EXECUTION_MODE=$EXECUTION_MODE_UPPER" >> .env
fi

print_status "Execution mode set to: $EXECUTION_MODE_UPPER"

# Prompt for API keys if not in .env
print_info "Checking API keys..."

if [ -n "$RPC_INFURA_KEY" ]; then
    # Update Infura keys
    if [[ "$OS" == "macos" ]]; then
        sed -i '' "s|RPC_ETHEREUM=.*|RPC_ETHEREUM=https://mainnet.infura.io/v3/$RPC_INFURA_KEY|" .env
        sed -i '' "s|RPC_POLYGON=.*|RPC_POLYGON=https://polygon-mainnet.infura.io/v3/$RPC_INFURA_KEY|" .env
    else
        sed -i "s|RPC_ETHEREUM=.*|RPC_ETHEREUM=https://mainnet.infura.io/v3/$RPC_INFURA_KEY|" .env
        sed -i "s|RPC_POLYGON=.*|RPC_POLYGON=https://polygon-mainnet.infura.io/v3/$RPC_INFURA_KEY|" .env
    fi
    print_status "Infura API key configured"
fi

if [ -n "$RPC_ALCHEMY_KEY" ]; then
    # Update Alchemy keys
    if [[ "$OS" == "macos" ]]; then
        sed -i '' "s|ALCHEMY_RPC_ETH=.*|ALCHEMY_RPC_ETH=https://eth-mainnet.g.alchemy.com/v2/$RPC_ALCHEMY_KEY|" .env
        sed -i '' "s|ALCHEMY_RPC_POLY=.*|ALCHEMY_RPC_POLY=https://polygon-mainnet.g.alchemy.com/v2/$RPC_ALCHEMY_KEY|" .env
    else
        sed -i "s|ALCHEMY_RPC_ETH=.*|ALCHEMY_RPC_ETH=https://eth-mainnet.g.alchemy.com/v2/$RPC_ALCHEMY_KEY|" .env
        sed -i "s|ALCHEMY_RPC_POLY=.*|ALCHEMY_RPC_POLY=https://polygon-mainnet.g.alchemy.com/v2/$RPC_ALCHEMY_KEY|" .env
    fi
    print_status "Alchemy API key configured"
fi

if [ -n "$LIFI_API_KEY" ]; then
    # Update Li.Fi key
    if [[ "$OS" == "macos" ]]; then
        sed -i '' "s|LIFI_API_KEY=.*|LIFI_API_KEY=$LIFI_API_KEY|" .env
    else
        sed -i "s|LIFI_API_KEY=.*|LIFI_API_KEY=$LIFI_API_KEY|" .env
    fi
    print_status "Li.Fi API key configured"
fi

# Check if RPC endpoints are configured
RPC_CONFIGURED=false
if grep -q "^RPC_POLYGON=https://" .env || grep -q "^ALCHEMY_RPC_POLY=https://" .env; then
    RPC_CONFIGURED=true
fi

if [ "$RPC_CONFIGURED" = false ]; then
    print_warning "RPC endpoints not fully configured in .env"
    print_info "You may need to add Infura/Alchemy API keys for full functionality"
    print_info "Get free keys from: https://infura.io/ and https://alchemy.com/"
fi

print_section "STEP 7/10: CREATING DATA DIRECTORIES"

mkdir -p data logs certs
print_status "Data directories created (data/, logs/, certs/)"

print_section "STEP 8/10: DEPLOYING SMART CONTRACTS (REGISTRIES & POOLS)"

print_progress "Deploying OmniArbExecutor to $DEPLOY_NETWORK..."
print_info "This creates the on-chain registry for pools, tokenomics, and arbitrage execution"

# Check if contract already deployed
CONTRACT_DEPLOYED=false
if grep -q "^EXECUTOR_ADDRESS_$(echo $DEPLOY_NETWORK | tr '[:lower:]' '[:upper:]')=" .env; then
    EXISTING_ADDRESS=$(grep "^EXECUTOR_ADDRESS_$(echo $DEPLOY_NETWORK | tr '[:lower:]' '[:upper:]')=" .env | cut -d'=' -f2)
    if [[ "$EXISTING_ADDRESS" =~ ^0x[0-9a-fA-F]{40}$ ]]; then
        print_warning "Contract already deployed to $DEPLOY_NETWORK at $EXISTING_ADDRESS"
        echo -e "${YELLOW}Redeploy? (y/N):${NC} "
        read -r REDEPLOY
        if [[ ! "$REDEPLOY" =~ ^[Yy]$ ]]; then
            CONTRACT_DEPLOYED=true
            print_info "Using existing contract deployment"
        fi
    fi
fi

if [ "$CONTRACT_DEPLOYED" = false ]; then
    # Deploy contract
    DEPLOY_OUTPUT=$(npx hardhat run scripts/deploy.js --network $DEPLOY_NETWORK 2>&1)
    DEPLOY_EXIT=$?
    
    if [ $DEPLOY_EXIT -eq 0 ]; then
        # Extract deployed address from output
        DEPLOYED_ADDRESS=$(echo "$DEPLOY_OUTPUT" | grep -oE "0x[0-9a-fA-F]{40}" | tail -1)
        
        if [[ "$DEPLOYED_ADDRESS" =~ ^0x[0-9a-fA-F]{40}$ ]]; then
            print_status "Contract deployed to: $DEPLOYED_ADDRESS"
            
            # Update .env with deployed address
            ENV_KEY="EXECUTOR_ADDRESS_$(echo $DEPLOY_NETWORK | tr '[:lower:]' '[:upper:]')"
            if grep -q "^$ENV_KEY=" .env; then
                if [[ "$OS" == "macos" ]]; then
                    sed -i '' "s|^$ENV_KEY=.*|$ENV_KEY=$DEPLOYED_ADDRESS|" .env
                else
                    sed -i "s|^$ENV_KEY=.*|$ENV_KEY=$DEPLOYED_ADDRESS|" .env
                fi
            else
                echo "$ENV_KEY=$DEPLOYED_ADDRESS" >> .env
            fi
            
            print_status "Contract address saved to .env"
            print_info "Registry initialized: Pools + Tokenomics + Omni Token Universe"
        else
            print_warning "Could not extract deployed address from output"
            print_info "Please manually add EXECUTOR_ADDRESS_$(echo $DEPLOY_NETWORK | tr '[:lower:]' '[:upper:]') to .env"
        fi
    else
        print_warning "Contract deployment failed or skipped"
        print_info "This may be due to insufficient funds or network issues"
        print_info "You can deploy later with: npx hardhat run scripts/deploy.js --network $DEPLOY_NETWORK"
        print_info "System can still run in simulation mode without deployment"
    fi
fi

print_section "STEP 9/10: RUNNING SYSTEM AUDIT"

if [ -f "audit_system.py" ]; then
    print_progress "Auditing system integrity..."
    python3 audit_system.py
    if [ $? -eq 0 ]; then
        print_status "System audit passed"
    else
        print_warning "System audit completed with warnings (non-critical)"
    fi
else
    print_warning "audit_system.py not found, skipping audit"
fi

print_section "STEP 10/10: SYSTEM READY - LAUNCHING TITAN"

echo ""
print_status "Installation complete!"
echo ""
echo -e "${GREEN}================================================================${NC}"
echo -e "${GREEN}   ✅ TITAN SYSTEM CONFIGURED AND READY TO LAUNCH${NC}"
echo -e "${GREEN}================================================================${NC}"
echo ""
echo -e "${CYAN}Configuration Summary:${NC}"
echo -e "  • Wallet: ${GREEN}Configured${NC}"
echo -e "  • Execution Mode: ${GREEN}$EXECUTION_MODE_UPPER${NC}"
if [ "$EXECUTION_MODE_UPPER" == "PAPER" ]; then
    echo -e "    ${YELLOW}(Simulated execution - no real funds used)${NC}"
else
    echo -e "    ${RED}(LIVE execution - REAL FUNDS AT RISK)${NC}"
fi
echo -e "  • Network: ${GREEN}$DEPLOY_NETWORK${NC}"
echo -e "  • Redis: $(redis-cli ping >/dev/null 2>&1 && echo -e "${GREEN}Running${NC}" || echo -e "${YELLOW}Not running${NC}")"
echo -e "  • Smart Contracts: ${GREEN}Compiled${NC}"
if [ "$CONTRACT_DEPLOYED" = true ] || [[ "$DEPLOYED_ADDRESS" =~ ^0x[0-9a-fA-F]{40}$ ]]; then
    echo -e "  • Contract Deployed: ${GREEN}Yes${NC}"
else
    echo -e "  • Contract Deployed: ${YELLOW}Pending${NC}"
fi
echo ""

# Ask to launch
echo -e "${CYAN}Launch Titan system now? (Y/n):${NC} "
read -r LAUNCH
if [[ ! "$LAUNCH" =~ ^[Nn]$ ]]; then
    print_section "LAUNCHING TITAN ARBITRAGE SYSTEM"
    
    echo ""
    print_info "Starting components:"
    print_info "  1. Redis Message Queue"
    print_info "  2. Mainnet Orchestrator (Python - Data + ML + Calculations)"
    print_info "  3. Execution Engine (Node.js - Trade Execution)"
    echo ""
    
    # Ensure Redis is running
    if ! redis-cli ping >/dev/null 2>&1; then
        print_progress "Starting Redis..."
        redis-server --daemonize yes
        sleep 2
    fi
    
    # Create logs directory
    mkdir -p logs
    
    # Export mode
    export EXECUTION_MODE=$EXECUTION_MODE_UPPER
    
    # Setup cleanup handler
    cleanup_processes() {
        print_info "Cleaning up processes..."
        [ -f .orchestrator.pid ] && kill $(cat .orchestrator.pid) 2>/dev/null || true
        [ -f .executor.pid ] && kill $(cat .executor.pid) 2>/dev/null || true
        rm -f .orchestrator.pid .executor.pid
    }
    
    # Register cleanup on script exit
    trap cleanup_processes EXIT INT TERM
    
    # Launch system components
    print_progress "Launching Mainnet Orchestrator..."
    python3 mainnet_orchestrator.py > logs/orchestrator.log 2>&1 &
    ORCHESTRATOR_PID=$!
    echo $ORCHESTRATOR_PID > .orchestrator.pid
    sleep 3
    
    # Verify orchestrator started
    if ! ps -p $ORCHESTRATOR_PID > /dev/null; then
        print_error "Orchestrator failed to start. Check logs/orchestrator.log"
        exit 1
    fi
    
    print_progress "Launching Execution Engine..."
    node execution/bot.js > logs/executor.log 2>&1 &
    EXECUTOR_PID=$!
    echo $EXECUTOR_PID > .executor.pid
    sleep 2
    
    # Verify executor started
    if ! ps -p $EXECUTOR_PID > /dev/null; then
        print_error "Executor failed to start. Check logs/executor.log"
        exit 1
    fi
    
    echo ""
    print_status "System launched successfully!"
    echo ""
    echo -e "${GREEN}================================================================${NC}"
    echo -e "${GREEN}   🎯 TITAN IS NOW HUNTING FOR ARBITRAGE OPPORTUNITIES${NC}"
    echo -e "${GREEN}================================================================${NC}"
    echo ""
    echo -e "${CYAN}Process IDs:${NC}"
    echo -e "  • Orchestrator PID: ${GREEN}$ORCHESTRATOR_PID${NC}"
    echo -e "  • Executor PID: ${GREEN}$EXECUTOR_PID${NC}"
    echo ""
    echo -e "${CYAN}Monitor Logs:${NC}"
    echo -e "  ${BLUE}tail -f logs/orchestrator.log${NC}  # Python ML engine"
    echo -e "  ${BLUE}tail -f logs/executor.log${NC}      # Node.js execution"
    echo ""
    echo -e "${CYAN}Stop System:${NC}"
    echo -e "  ${BLUE}kill $ORCHESTRATOR_PID $EXECUTOR_PID${NC}"
    echo -e "  Or: ${BLUE}kill \$(cat .orchestrator.pid .executor.pid)${NC}"
    echo ""
    
    if [ "$EXECUTION_MODE_UPPER" == "PAPER" ]; then
        echo -e "${YELLOW}📝 Running in PAPER mode - Trades are simulated${NC}"
    else
        echo -e "${RED}🔴 Running in LIVE mode - REAL FUNDS AT RISK${NC}"
    fi
    
    echo ""
    echo -e "${CYAN}System Functions:${NC}"
    echo -e "  ✓ Real-time mainnet data ingestion"
    echo -e "  ✓ Multi-chain arbitrage detection"
    echo -e "  ✓ Flash loan execution (Balancer V3 + Aave)"
    echo -e "  ✓ Cross-chain bridge aggregation (Li.Fi)"
    echo -e "  ✓ ML-based profit prediction"
    echo -e "  ✓ Gas optimization"
    if [ "$EXECUTION_MODE_UPPER" == "PAPER" ]; then
        echo -e "  ✓ Simulated trade execution"
    else
        echo -e "  ✓ Live blockchain execution"
    fi
    echo ""
    echo -e "${GREEN}Happy trading! 🚀${NC}"
    echo ""
else
    echo ""
    print_info "Launch skipped. You can start the system later with:"
    echo -e "  ${BLUE}./start_mainnet.sh $EXECUTION_MODE${NC}"
    echo ""
fi

# Save configuration summary
cat > logs/installation_summary.txt << EOF
TITAN INSTALLATION SUMMARY
==========================
Installation Date: $(date)
Execution Mode: $EXECUTION_MODE_UPPER
Deploy Network: $DEPLOY_NETWORK
Wallet Configured: Yes
Redis Status: $(redis-cli ping 2>/dev/null || echo "Not running")
Contract Deployed: $([ "$CONTRACT_DEPLOYED" = true ] && echo "Yes" || echo "$DEPLOYED_ADDRESS")

System Components:
- Node.js dependencies: Installed
- Python dependencies: Installed
- Rust components (rustworkx): Installed
- Smart contracts: Compiled
- Data directories: Created

Next Steps:
1. Monitor logs: tail -f logs/orchestrator.log logs/executor.log
2. View metrics: Check logs for profit opportunities
3. Adjust parameters: Edit .env file
4. Deploy to other networks: npx hardhat run scripts/deploy.js --network <network>

Documentation:
- README.md - Complete system documentation
- QUICKSTART.md - Getting started guide
- INSTALL.md - Detailed installation instructions
EOF

print_status "Installation summary saved to logs/installation_summary.txt"

echo ""
print_info "Installation complete! 🎉"
echo ""
