# Installation Guide - Apex-Omega Titan

Complete installation instructions for all platforms.

## Table of Contents

- [System Requirements](#system-requirements)
- [Platform-Specific Installation](#platform-specific-installation)
  - [Linux](#linux-ubuntu--debian)
  - [macOS](#macos)
  - [Windows](#windows)
- [Dependency Installation](#dependency-installation)
- [Configuration](#configuration)
- [Verification](#verification)
- [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- **CPU**: 2 cores (4 cores recommended)
- **RAM**: 4GB (8GB recommended)
- **Disk**: 10GB free space
- **Network**: Broadband internet connection
- **OS**: Linux, macOS 10.14+, or Windows 10/11

### Software Prerequisites
- **Node.js**: 18.0.0 or higher
- **Python**: 3.11.0 or higher
- **Redis**: 5.0.0 or higher
- **Git**: 2.x or higher

### API Requirements
- **Infura** account (free tier available)
- **Alchemy** account (free tier available)
- **Li.Fi** API key (free)
- Ethereum wallet with private key

---

## Platform-Specific Installation

### Linux (Ubuntu / Debian)

#### 1. Install Prerequisites

```bash
# Update package lists
sudo apt update

# Install Node.js 18+
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install Python 3.11+
sudo apt install -y python3 python3-pip python3-venv

# Install Redis
sudo apt install -y redis-server

# Install Git
sudo apt install -y git

# Install build tools
sudo apt install -y build-essential
```

#### 2. Verify Installations

```bash
node -v        # Should show v18.x.x or higher
python3 --version  # Should show 3.11.x or higher
redis-server --version  # Should show 5.x.x or higher
git --version  # Should show 2.x.x or higher
```

#### 3. Start Redis

```bash
# Start Redis service
sudo systemctl start redis-server

# Enable Redis to start on boot
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping  # Should return: PONG
```

#### 4. Clone and Setup Titan

```bash
# Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

# Run automated setup
chmod +x setup.sh
./setup.sh
```

---

### macOS

#### 1. Install Homebrew (if not already installed)

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

#### 2. Install Prerequisites

```bash
# Install Node.js
brew install node@18

# Install Python 3.11
brew install python@3.11

# Install Redis
brew install redis

# Git is usually pre-installed, but if not:
brew install git
```

#### 3. Verify Installations

```bash
node -v        # Should show v18.x.x or higher
python3 --version  # Should show 3.11.x or higher
redis-server --version  # Should show 5.x.x or higher
git --version  # Should show 2.x.x or higher
```

#### 4. Start Redis

```bash
# Start Redis as a service
brew services start redis

# Or start Redis manually
redis-server
```

#### 5. Clone and Setup Titan

```bash
# Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

# Run automated setup
chmod +x setup.sh
./setup.sh
```

---

### Windows

#### Option 1: Using WSL2 (Recommended)

Windows Subsystem for Linux provides the best experience:

1. **Install WSL2**
   ```powershell
   # Run in PowerShell as Administrator
   wsl --install
   ```

2. **Install Ubuntu from Microsoft Store**

3. **Follow Linux installation instructions above**

#### Option 2: Native Windows Installation

1. **Install Node.js**
   - Download from: https://nodejs.org/
   - Run installer and follow prompts
   - Verify: Open CMD and run `node -v`

2. **Install Python**
   - Download from: https://python.org/downloads/
   - **Important**: Check "Add Python to PATH" during installation
   - Verify: Open CMD and run `python --version`

3. **Install Redis**
   - Download from: https://github.com/microsoftarchive/redis/releases
   - Extract and run `redis-server.exe`
   - Or use Docker: `docker run -d -p 6379:6379 redis`

4. **Install Git**
   - Download from: https://git-scm.com/download/win
   - Run installer with default settings

5. **Clone and Setup Titan**
   ```batch
   # Open Command Prompt
   git clone https://github.com/MavenSource/Titan.git
   cd Titan
   
   # Run Windows setup script
   start_titan_full.bat
   ```

---

## Dependency Installation

### Automated (Recommended)

```bash
# Linux/macOS
./setup.sh

# Windows
start_titan_full.bat
```

### Manual Installation

#### Node.js Dependencies

**For initial setup or when modifying dependencies:**

```bash
npm install
```

**For clean, reproducible installs (CI/production):**

```bash
npm ci
```

> **Note**: The `overrides` block in `package.json` ensures peer dependency conflicts are resolved automatically during `npm install`. Use `npm ci` for strict, lockfile-based installs in CI environments or when you want reproducible builds.

This installs:
- `ethers@6.16.0` - Blockchain interaction (unified via overrides)
- `@openzeppelin/contracts@5.4.0` - Smart contract utilities
- `@paraswap/sdk@7.3.1` - DEX aggregation
- `axios@1.6.7` - HTTP requests
- `dotenv@16.4.1` - Environment management
- `redis@4.6.12` - Message queue client
- `@flashbots/ethers-provider-bundle@1.0.0` - MEV protection
- `hardhat@2.19.5` - Smart contract development

#### Python Dependencies

```bash
pip3 install -r requirements.txt
```

This installs:
- `web3>=6.15.0` - Blockchain interaction
- `pandas>=2.2.0` - Data analysis
- `numpy>=1.26.0` - Numerical computations
- `rustworkx>=0.14.0` - Graph algorithms
- `requests>=2.31.0` - HTTP requests
- `python-dotenv>=1.0.1` - Environment management
- `redis>=5.0.1` - Message queue client
- `fastapi>=0.109.0` - API framework
- `uvicorn>=0.27.0` - ASGI server
- `eth-abi>=5.0.0` - ABI encoding/decoding
- `colorama>=0.4.6` - Terminal colors

#### Smart Contract Compilation

```bash
npx hardhat compile
```

This compiles:
- `contracts/OmniArbExecutor.sol` - Main arbitrage contract
- Contract interfaces and modules
- Generates artifacts in `artifacts/` directory

---

## Configuration

### 1. Create Environment File

```bash
cp .env.example .env
```

### 2. Edit Configuration

Open `.env` in your editor:

```bash
# Linux/macOS
nano .env

# Or use your preferred editor
code .env
vim .env
```

### 3. Required Configuration

#### A. Private Key

```env
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE
```

⚠️ **Security Notes:**
- Use a dedicated wallet (not your main wallet)
- Never commit `.env` to git
- Store backup securely
- Start with testnet

#### B. RPC Providers

Get free API keys from:
- **Infura**: https://infura.io/register
- **Alchemy**: https://www.alchemy.com/

```env
# Infura
RPC_ETHEREUM=https://mainnet.infura.io/v3/YOUR_PROJECT_ID
RPC_POLYGON=https://polygon-mainnet.infura.io/v3/YOUR_PROJECT_ID

# Alchemy
ALCHEMY_RPC_ETH=https://eth-mainnet.g.alchemy.com/v2/YOUR_API_KEY
ALCHEMY_RPC_POLY=https://polygon-mainnet.g.alchemy.com/v2/YOUR_API_KEY
```

#### C. Li.Fi API Key

Get free key from: https://li.fi/

```env
LIFI_API_KEY=your_lifi_api_key_here
```

### 4. Deploy Smart Contract

Choose your network (Polygon recommended for testing):

```bash
# Deploy to Polygon
npx hardhat run scripts/deploy.js --network polygon

# Deploy to Arbitrum
npx hardhat run scripts/deploy.js --network arbitrum

# Deploy to Optimism
npx hardhat run scripts/deploy.js --network optimism
```

Copy the deployed address and add to `.env`:

```env
EXECUTOR_ADDRESS_POLYGON=0xYOUR_DEPLOYED_CONTRACT_ADDRESS
```

### 5. Optional Configuration

```env
# Strategy parameters
MIN_PROFIT_USD=5.00
MAX_SLIPPAGE_BPS=50
MAX_PRIORITY_FEE_GWEI=50

# Features
ENABLE_CROSS_CHAIN=true
ENABLE_MEV_PROTECTION=false

# Additional APIs
COINGECKO_API_KEY=
ONEINCH_API_KEY=
ETHERSCAN_API_KEY=
```

---

## Verification

### 1. Check Prerequisites

```bash
make check-prereqs
```

Expected output:
```
✅ Node.js installed
✅ Python 3 installed
✅ pip3 installed
✅ Redis installed
✅ Git installed
```

### 2. Verify Redis

```bash
redis-cli ping
```

Expected output: `PONG`

### 3. Run System Audit

```bash
python3 audit_system.py
```

Expected output:
```
==================================
   APEX-OMEGA TITAN: FINAL AUDIT
==================================

[1] Checking File System...
   ✅ Found: .env
   ✅ Found: package.json
   ...

[2] Checking Logic Imports...
   ✅ Config Loaded. Chains Configured: 2

==================================
🚀 AUDIT PASSED. SYSTEM IS INTEGRAL.
```

### 4. Test Network Connectivity

```bash
python3 test_phase1.py
```

Expected output:
```
Testing POLYGON...
✅ Connected | Block: 52847291
```

### 5. Complete Verification

```bash
make verify
```

This runs:
- Prerequisite checks
- Contract compilation
- System audit

---

## Troubleshooting

### Issue: "command not found: node"

**Cause**: Node.js not in PATH

**Solution**:
```bash
# Linux/macOS - add to ~/.bashrc or ~/.zshrc
export PATH="/usr/local/bin:$PATH"

# Reload shell
source ~/.bashrc
```

### Issue: "command not found: python3"

**Cause**: Python not installed or not in PATH

**Solution**:
```bash
# Linux
sudo apt install python3

# macOS
brew install python@3.11

# Windows - reinstall Python and check "Add to PATH"
```

### Issue: "Redis connection refused"

**Cause**: Redis not running

**Solution**:
```bash
# Linux
sudo systemctl start redis-server

# macOS
brew services start redis

# Manual start
redis-server
```

### Issue: "Cannot connect to RPC provider"

**Cause**: Invalid or missing API keys

**Solution**:
1. Verify API keys in `.env`
2. Check key format (no extra spaces)
3. Test key directly:
   ```bash
   curl https://mainnet.infura.io/v3/YOUR_PROJECT_ID \
     -X POST \
     -H "Content-Type: application/json" \
     -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
   ```

### Issue: "Insufficient funds for gas"

**Cause**: Wallet has no native tokens

**Solution**:
1. Fund wallet with native token (ETH, MATIC, etc.)
2. For testnet, use faucets:
   - Mumbai: https://faucet.polygon.technology/
   - Goerli: https://goerlifaucet.com/

### Issue: "Contract deployment failed"

**Cause**: Invalid network configuration or insufficient gas

**Solution**:
```bash
# Check hardhat config
npx hardhat test

# Try with more gas
npx hardhat run scripts/deploy.js --network polygon --gas 5000000
```

### Issue: "Module not found"

**Cause**: Dependencies not installed

**Solution**:
```bash
# For development (initial setup or dependency changes)
rm -rf node_modules package-lock.json
npm install

# For clean rebuild (production/CI)
rm -rf node_modules
npm ci

# Reinstall Python dependencies
pip3 install -r requirements.txt --force-reinstall
```

### Issue: "Permission denied: ./setup.sh"

**Cause**: Script not executable

**Solution**:
```bash
chmod +x setup.sh
chmod +x start.sh
```

### Issue: "Python version too old"

**Cause**: System Python is < 3.11

**Solution**:
```bash
# Linux - use deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.11 python3.11-pip

# macOS
brew install python@3.11

# Update alternatives
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1
```

### Still Having Issues?

1. **Check logs**:
   ```bash
   tail -f logs/brain.log
   tail -f logs/bot.log
   ```

2. **Run in debug mode**:
   ```bash
   LOG_LEVEL=DEBUG python3 ml/brain.py
   ```

3. **Clean and rebuild**:
   ```bash
   make clean
   make compile
   make verify
   ```

4. **Ask for help**:
   - Open an issue: https://github.com/MavenSource/Titan/issues
   - Include: OS, error message, and steps to reproduce

---

## Post-Installation

After successful installation:

1. **Read**: [QUICKSTART.md](QUICKSTART.md) for usage guide
2. **Configure**: Tune strategy parameters in `.env`
3. **Test**: Start on testnet before mainnet
4. **Monitor**: Watch logs for profitable opportunities
5. **Optimize**: Adjust based on performance

---

## Next Steps

- [QUICKSTART.md](QUICKSTART.md) - Get started in 15 minutes
- [README.md](README.md) - Complete documentation
- [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) - Security best practices

**Installation Complete! Time to start trading! 🚀**
