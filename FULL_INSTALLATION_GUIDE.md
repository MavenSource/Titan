# 🚀 Titan Full-Scale Installation & Execution Guide

Complete guide for installing, configuring, and running the Titan arbitrage system with a single command.

## Overview

The full-scale installation script (`install_and_run_titan.sh` for Linux/macOS, `install_and_run_titan.bat` for Windows) automates the entire setup process:

1. ✅ Installs all dependencies (Node.js, Python, Redis)
2. ✅ Builds Rust components (rustworkx library for graph algorithms)
3. ✅ Sets up Redis message queue (with optional fallback)
4. ✅ Compiles smart contracts (OmniArbExecutor, registries, pools)
5. ✅ Deploys contracts to build on-chain registries
6. ✅ Configures wallet for gas, TX signing, execution, and profit deposits
7. ✅ Launches the complete Titan system

## Quick Start

### Linux / macOS

```bash
# Make script executable
chmod +x install_and_run_titan.sh

# Run with your wallet credentials
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_PRIVATE_KEY_HERE \
  --wallet-address 0xYOUR_WALLET_ADDRESS \
  --mode paper \
  --network polygon
```

### Windows

```batch
# Run the installation script
install_and_run_titan.bat

# Follow the interactive prompts
```

## Prerequisites

### Required Software

The script will attempt to install missing components, but you should have:

- **Node.js 18+** - JavaScript runtime
- **Python 3.11+** - Python runtime
- **pip3** - Python package manager
- **Git** - Version control (optional)
- **Yarn** (optional but recommended) - Better dependency conflict resolution than npm

### Required Information

Before running the script, prepare:

1. **Wallet Private Key** - Your Ethereum wallet private key (starts with `0x`)
   - ⚠️ Use a dedicated wallet, NOT your main wallet
   - Fund with a small amount for gas fees
   - Never share this key or commit it to version control

2. **RPC API Keys** (optional but recommended):
   - **Infura** - Get free key at https://infura.io/
   - **Alchemy** - Get free key at https://alchemy.com/
   - **Li.Fi** - Get free key at https://li.fi/ (for cross-chain)

## Usage

### Command Line Options

```bash
./install_and_run_titan.sh [OPTIONS]
```

#### Available Options

| Option | Description | Default | Example |
|--------|-------------|---------|---------|
| `--wallet-key <KEY>` | Your wallet private key (with 0x prefix) | (prompted) | `--wallet-key 0x123...` |
| `--wallet-address <ADDR>` | Your wallet address | (derived from key) | `--wallet-address 0xabc...` |
| `--mode <paper\|live>` | Execution mode | `paper` | `--mode paper` |
| `--network <network>` | Deployment network | `polygon` | `--network arbitrum` |
| `--infura-key <KEY>` | Infura API key | (none) | `--infura-key abc123...` |
| `--alchemy-key <KEY>` | Alchemy API key | (none) | `--alchemy-key xyz789...` |
| `--lifi-key <KEY>` | Li.Fi API key | (none) | `--lifi-key def456...` |
| `--skip-redis` | Skip Redis installation/setup | false | `--skip-redis` |
| `--help` | Show help message | - | `--help` |

### Execution Modes

#### Paper Mode (Recommended for Testing)
```bash
--mode paper
```
- ✅ Real-time mainnet data
- ✅ Real arbitrage calculations
- ✅ Real ML model training
- ❌ Simulated execution (no blockchain transactions)
- 💰 **No real funds used**

#### Live Mode (Production)
```bash
--mode live
```
- ✅ Real-time mainnet data
- ✅ Real arbitrage calculations
- ✅ Real ML model training
- ✅ **Live blockchain execution**
- 💰 **REAL FUNDS AT RISK**

### Supported Networks

Deploy to any of these networks:

- `ethereum` - Ethereum Mainnet (Chain ID: 1)
- `polygon` - Polygon (Chain ID: 137) **[Recommended for testing]**
- `arbitrum` - Arbitrum One (Chain ID: 42161)
- `optimism` - Optimism (Chain ID: 10)
- `base` - Base (Chain ID: 8453)
- `bsc` - Binance Smart Chain (Chain ID: 56)
- `avalanche` - Avalanche C-Chain (Chain ID: 43114)
- `fantom` - Fantom Opera (Chain ID: 250)
- `linea` - Linea (Chain ID: 59144)
- `scroll` - Scroll (Chain ID: 534352)
- `mantle` - Mantle (Chain ID: 5000)
- `zksync` - zkSync Era (Chain ID: 324)
- `blast` - Blast (Chain ID: 81457)
- `celo` - Celo (Chain ID: 42220)
- `opbnb` - opBNB (Chain ID: 204)

## Examples

### Example 1: Basic Setup (Paper Mode)

```bash
./install_and_run_titan.sh \
  --wallet-key 0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef \
  --mode paper \
  --network polygon
```

This will:
- Install all dependencies
- Configure wallet for paper trading
- Deploy contract to Polygon
- Launch in simulation mode

### Example 2: Full Setup with API Keys

```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_PRIVATE_KEY \
  --mode paper \
  --network arbitrum \
  --infura-key YOUR_INFURA_KEY \
  --alchemy-key YOUR_ALCHEMY_KEY \
  --lifi-key YOUR_LIFI_KEY
```

This provides:
- Complete RPC configuration
- Cross-chain capabilities
- Better data reliability

### Example 3: Live Trading (Advanced)

⚠️ **WARNING: This uses real funds!**

```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_PRIVATE_KEY \
  --mode live \
  --network polygon \
  --infura-key YOUR_INFURA_KEY \
  --alchemy-key YOUR_ALCHEMY_KEY \
  --lifi-key YOUR_LIFI_KEY
```

Prerequisites for live mode:
- Funded wallet with native token (MATIC for Polygon)
- Valid RPC endpoints
- Deployed contract on target network
- Understanding of risks

### Example 4: Skip Redis (Minimal Setup)

```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_PRIVATE_KEY \
  --mode paper \
  --skip-redis
```

Useful when:
- Redis installation fails
- Running in constrained environment
- Testing basic functionality

## Installation Steps (What the Script Does)

### Step 1: System Prerequisites
- Detects operating system (Linux/macOS/Windows)
- Checks for Node.js, Python, pip, Git
- Installs missing prerequisites if possible

### Step 2: Node.js Dependencies
- Installs all npm packages from `package.json`
- Includes: ethers, hardhat, paraswap SDK, flashbots, etc.

### Step 3: Python Dependencies & Rust Components
- Installs all Python packages from `requirements.txt`
- Builds **rustworkx** (Rust-based graph library)
- Installs ML libraries (pandas, numpy, web3, etc.)

### Step 4: Redis Setup
- Checks if Redis is installed
- Attempts to install Redis if missing
- Starts Redis server
- Gracefully handles Redis failures (optional component)

### Step 5: Smart Contract Compilation
- Compiles `OmniArbExecutor.sol`
- Compiles all contract dependencies
- Generates ABI and bytecode
- Creates artifacts in `artifacts/` directory

### Step 6: Environment Configuration
- Creates `.env` from `.env.example`
- Validates and sets wallet private key
- Configures execution mode (PAPER/LIVE)
- Sets up RPC endpoints
- Adds API keys

### Step 7: Data Directories
- Creates `data/` for storage
- Creates `logs/` for log files
- Creates `certs/` for certificates

### Step 8: Smart Contract Deployment
- Deploys `OmniArbExecutor` to target network
- Initializes on-chain registries
- Configures pools and tokenomics
- Saves deployed address to `.env`

### Step 9: System Audit
- Runs `audit_system.py`
- Validates file structure
- Checks module imports
- Verifies configuration

### Step 10: System Launch
- Starts Redis (if not running)
- Launches Python Orchestrator (data + ML + calculations)
- Launches Node.js Executor (trade execution)
- Provides monitoring commands

## What Gets Built

### Rust Components
- **rustworkx**: Rust-based Python library for graph algorithms
  - Used for pathfinding in arbitrage routes
  - Hyper-graph analysis for multi-hop opportunities
  - High-performance network analysis

### Smart Contracts (On-Chain Registries)
- **OmniArbExecutor**: Main arbitrage execution contract
  - Flash loan integration (Balancer V3, Aave)
  - Multi-DEX swap routing
  - Gas-optimized execution
  - Profit extraction and deposit to your wallet

### Token Universe & Pools
- Pool registries across all supported chains
- Token price feeds and liquidity data
- DEX adapter interfaces (Uniswap, Curve, Balancer, etc.)
- Bridge routing for cross-chain operations

### Tokenomics System
- Profit calculation engine
- Gas cost estimation
- Slippage modeling
- Risk assessment

## After Installation

### Monitor the System

```bash
# Watch Python orchestrator logs
tail -f logs/orchestrator.log

# Watch Node.js executor logs  
tail -f logs/executor.log

# Watch both logs simultaneously
tail -f logs/orchestrator.log logs/executor.log
```

### Check System Status

```bash
# Check Redis
redis-cli ping

# Check running processes
ps aux | grep -E "python.*orchestrator|node.*bot"

# View installation summary
cat logs/installation_summary.txt
```

### Stop the System

```bash
# Find process IDs
ps aux | grep -E "python.*orchestrator|node.*bot"

# Kill processes (replace PIDs)
kill <ORCHESTRATOR_PID> <EXECUTOR_PID>

# Or use pkill
pkill -f mainnet_orchestrator.py
pkill -f "node execution/bot.js"
```

### Restart the System

```bash
# Use the mainnet launcher
./start_mainnet.sh paper    # Paper mode
./start_mainnet.sh live     # Live mode
```

## Configuration

### Post-Installation Configuration

Edit `.env` file to customize:

```bash
nano .env
```

#### Key Settings

```env
# Execution mode
EXECUTION_MODE=PAPER   # or LIVE

# Profit thresholds
MIN_PROFIT_USD=5.00
MIN_PROFIT_BPS=10

# Gas limits
MAX_PRIORITY_FEE_GWEI=50
MAX_BASE_FEE_GWEI=200

# Features
ENABLE_CROSS_CHAIN=true
ENABLE_MEV_PROTECTION=false
ENABLE_REALTIME_TRAINING=true

# Logging
LOG_LEVEL=INFO   # DEBUG, INFO, WARNING, ERROR
```

### Deploy to Additional Networks

After initial installation, deploy to more networks:

```bash
# Deploy to Arbitrum
npx hardhat run scripts/deploy.js --network arbitrum

# Deploy to Optimism
npx hardhat run scripts/deploy.js --network optimism

# Add addresses to .env
echo "EXECUTOR_ADDRESS_ARBITRUM=0xYOUR_ADDRESS" >> .env
echo "EXECUTOR_ADDRESS_OPTIMISM=0xYOUR_ADDRESS" >> .env
```

## Wallet & Gas Configuration

### How the Wallet is Used

Your wallet performs these functions:

1. **Gas Payment**: Pays for blockchain transaction fees
2. **Transaction Signing**: Signs all transactions with your private key
3. **Trade Execution**: Executes arbitrage trades through your deployed contract
4. **Profit Deposits**: Receives profits from successful arbitrage

### Funding Your Wallet

#### Paper Mode
- Minimal funding required
- Only for contract deployment (~$5-10 in native token)
- No trading funds needed

#### Live Mode
- Fund with native token for gas (ETH, MATIC, etc.)
- Recommended starting amount: $100-500
- Monitor gas prices and adjust funding
- Set up automatic alerts for low balance

### Security Best Practices

✅ **DO:**
- Use a dedicated wallet for Titan (not your main wallet)
- Start with small amounts in Paper mode
- Keep private key secure and never share it
- Back up your wallet securely
- Monitor wallet balance regularly
- Use hardware wallet integration if possible

❌ **DON'T:**
- Commit `.env` file to version control
- Share your private key with anyone
- Use your main wallet with large holdings
- Run Live mode without testing Paper mode first
- Leave system running unmonitored

## Troubleshooting

### Issue: "Node.js not found"

**Solution:**
```bash
# Linux
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# macOS
brew install node@18

# Windows
# Download from https://nodejs.org/
```

### Issue: "Python not found"

**Solution:**
```bash
# Linux
sudo apt install python3.11 python3-pip

# macOS
brew install python@3.11

# Windows
# Download from https://python.org/
# Check "Add Python to PATH" during installation
```

### Issue: "Redis connection refused"

**Solution:**
```bash
# Start Redis
redis-server --daemonize yes

# Or use system service
sudo systemctl start redis-server  # Linux
brew services start redis          # macOS

# Or skip Redis
./install_and_run_titan.sh --skip-redis
```

### Issue: "Contract deployment failed"

**Causes:**
- Insufficient funds for gas
- Invalid RPC endpoint
- Network congestion

**Solutions:**
```bash
# 1. Fund wallet with native token
# 2. Verify RPC endpoint in .env
# 3. Try again with higher gas:
npx hardhat run scripts/deploy.js --network polygon --gas 5000000

# 4. Deploy manually later
npx hardhat run scripts/deploy.js --network <network>
```

### Issue: "Invalid private key format"

**Solution:**
- Private key must start with `0x`
- Must be exactly 66 characters (0x + 64 hex chars)
- Example: `0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef`

### Issue: "rustworkx installation failed"

**Solution:**
```bash
# Install build tools
# Linux
sudo apt install build-essential python3-dev

# macOS
xcode-select --install

# Retry installation
pip3 install rustworkx --force-reinstall
```

### Issue: "Permission denied"

**Solution:**
```bash
# Make script executable
chmod +x install_and_run_titan.sh

# Or run with bash
bash install_and_run_titan.sh
```

### Issue: "Dependency conflicts during npm install"

**Solution:**
Use Yarn for better dependency conflict resolution:

```bash
# Install Yarn globally
npm install -g yarn

# Use Yarn for installation
yarn install

# Or use the yarn setup script
yarn setup:yarn
```

**Why Yarn?**
- Better dependency resolution algorithm
- `resolutions` field forces specific versions across all dependencies
- Deterministic installs with yarn.lock
- Faster installation with better caching
- Automatic conflict resolution without --legacy-peer-deps flag

## Advanced Usage

### Running Components Separately

If you prefer manual control:

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Python Orchestrator
python3 mainnet_orchestrator.py

# Terminal 3: Start Node.js Executor
node execution/bot.js
```

### Using Docker (Alternative)

```bash
# Start Redis in Docker
docker run -d -p 6379:6379 --name titan-redis redis

# Use Redis in Docker
export REDIS_URL=redis://localhost:6379
```

### Custom Installation Path

```bash
# Clone to custom location
git clone https://github.com/MavenSource/Titan.git /path/to/titan
cd /path/to/titan

# Run installation
./install_and_run_titan.sh
```

## Performance Optimization

### After Installation

1. **Tune Parameters**: Edit `.env` to adjust profit thresholds
2. **Monitor Metrics**: Watch logs for opportunity detection rate
3. **Add RPC Endpoints**: More endpoints = better reliability
4. **Enable Features**: Turn on cross-chain, MEV protection as needed
5. **Scale Resources**: More CPU/RAM = faster analysis

### Recommended Settings

For optimal performance:

```env
# .env optimizations
MIN_PROFIT_USD=5.00              # Balance profitability vs frequency
MAX_CONCURRENT_TXS=3             # Limit concurrent operations
MAX_PRIORITY_FEE_GWEI=50         # Cap gas costs
ENABLE_REALTIME_TRAINING=true    # Keep ML models current
CACHE_TTL=300                    # 5-minute cache
```

## Support & Documentation

### Documentation Files
- `README.md` - Complete system documentation
- `QUICKSTART.md` - 15-minute getting started guide
- `INSTALL.md` - Detailed installation instructions
- `MAINNET_QUICKSTART.md` - Mainnet deployment guide
- `SECURITY_SUMMARY.md` - Security best practices

### Getting Help

1. **Check Logs**: Most issues are visible in logs
2. **System Audit**: Run `python3 audit_system.py`
3. **Health Check**: Run `./health-check.sh`
4. **GitHub Issues**: Open issue with error details

## Summary

The full-scale installation script provides:

✅ **Complete Automation** - One command installs everything  
✅ **Rust Components** - Builds rustworkx for high-performance graphs  
✅ **Smart Contracts** - Deploys registries, pools, and tokenomics  
✅ **Wallet Integration** - Configures for gas, signing, execution, profits  
✅ **Flexible Modes** - Paper (safe) or Live (production)  
✅ **Multi-Chain** - Deploy to 15+ blockchain networks  
✅ **Production Ready** - Launches complete arbitrage system  

**Next Steps:**
1. Run the installation script
2. Monitor logs for opportunities
3. Tune parameters based on performance
4. Scale to additional networks
5. Optimize for maximum profitability

**Happy Trading! 🚀**
