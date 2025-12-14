# 🚀 One-Click Install and Run Guide

This guide provides the **simplest possible way** to install and run the Titan arbitrage system with a single command.

## Quick Start Options

### Option 1: Yarn (Recommended for Unix/Linux/macOS)

```bash
# Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

# Configure your .env file (see Configuration section below)
cp .env.example .env
nano .env  # or use your favorite editor

# One command to install and run everything!
yarn install-and-run:yarn
```

### Option 2: npm (Unix/Linux/macOS)

```bash
# Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

# Configure your .env file
cp .env.example .env
nano .env

# One command to install and run everything!
npm run install-and-run
```

### Option 3: Shell Script (Unix/Linux/macOS)

```bash
# Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

# Run the one-click script (it will guide you through configuration)
./run_titan.sh
```

### Option 4: Batch File - Yarn (Windows)

```batch
REM Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

REM Double-click or run from command prompt:
run_titan_yarn.bat
```

### Option 5: Batch File - npm (Windows)

```batch
REM Clone repository
git clone https://github.com/MavenSource/Titan.git
cd Titan

REM Double-click or run from command prompt:
run_titan.bat
```

## Prerequisites

Before using the one-click install, ensure you have:

- **Node.js 18+** - [Download](https://nodejs.org/)
- **Python 3.11+** - [Download](https://python.org/)
- **Git** - [Download](https://git-scm.com/)
- **Yarn** (optional, but recommended) - Install with: `npm install -g yarn`

### Optional Prerequisites

- **Redis 5.0+** - [Installation guide](https://redis.io/download) (system will work without it but with limited features)

## Configuration

Before running the one-click install, you need to configure your `.env` file:

### Step 1: Create .env file

```bash
cp .env.example .env
```

### Step 2: Edit .env file

**Minimum Required Configuration:**

```env
# Your wallet private key (DO NOT share this!)
PRIVATE_KEY=0xYOUR_PRIVATE_KEY_HERE_64_HEX_CHARACTERS

# RPC endpoints (get free keys from infura.io)
RPC_ETHEREUM=https://mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
RPC_POLYGON=https://polygon-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID
RPC_ARBITRUM=https://arbitrum-mainnet.infura.io/v3/YOUR_INFURA_PROJECT_ID

# Li.Fi API Key (get free key from li.fi)
LIFI_API_KEY=your_lifi_api_key_here

# Execution mode
EXECUTION_MODE=PAPER  # Use PAPER for testing, LIVE for real trading
```

**Where to get API keys (all free):**

| Service | Purpose | Get Key | Required |
|---------|---------|---------|----------|
| **Infura** | RPC Provider | [infura.io](https://infura.io/) | ✅ Yes |
| **Alchemy** | Backup RPC | [alchemy.com](https://alchemy.com/) | Recommended |
| **Li.Fi** | Cross-chain | [li.fi](https://li.fi/) | ✅ Yes |
| CoinGecko | Price feeds | [coingecko.com](https://coingecko.com/en/api) | Optional |

## What the One-Click Script Does

The one-click installation automatically:

1. ✅ **Checks prerequisites** - Verifies Node.js, Python, and pip are installed
2. ✅ **Creates .env file** - Copies from template if not exists
3. ✅ **Installs Node.js dependencies** - Uses Yarn or npm
4. ✅ **Installs Python dependencies** - All required Python packages
5. ✅ **Compiles smart contracts** - Hardhat compilation
6. ✅ **Starts the system** - Launches Brain and Executor components

## After Installation

Once the one-click script completes, you'll see:

```
================================================================
   TITAN SYSTEM IS NOW RUNNING!
================================================================

Components started:
  - Brain (AI Engine): Python ml/brain.py
  - Executor (Trading Bot): Node execution/bot.js

Monitor the windows/terminals to see system activity.
```

### Expected Output

**Brain Terminal:**
```
🧠 Booting Apex-Omega Titan Brain...
🕸️  Constructing Hyper-Graph Nodes...
✅ System Online. Tracking 256 nodes.
🚀 Titan Brain: Engaging Hyper-Parallel Scan Loop...
📡 Connecting to POLYGON... ✅ ONLINE | Block: 52847291
```

**Executor Terminal:**
```
🤖 Titan Bot Online.
Mode: PAPER
Subscribed to: trade_signals
Waiting for opportunities...
```

## Stopping the System

### Unix/Linux/macOS
```bash
# Press Ctrl+C in the terminal where the system is running
# Or use Make command:
make stop
```

### Windows
```batch
# Close the component windows
# Or press Ctrl+C in each window
```

## Troubleshooting

### "Node.js not found"

**Solution:** Install Node.js from [nodejs.org](https://nodejs.org/)

### "Python not found"

**Solution:** Install Python from [python.org](https://python.org/)

### "yarn not found" (when using Yarn commands)

**Solution:** 
```bash
npm install -g yarn
```

Or use the npm commands instead:
```bash
npm run install-and-run
```

### ".env file not configured"

**Solution:** Edit the `.env` file and add your:
- Private key
- RPC endpoints
- Li.Fi API key

### "Redis connection failed"

**Don't worry!** The system will work without Redis, just with limited caching. To fix:

```bash
# macOS
brew services start redis

# Ubuntu/Debian
sudo systemctl start redis

# Windows
# Download and install Redis from https://redis.io/download
```

### "Insufficient funds for gas"

**Solution:**
1. Ensure your wallet has native tokens (ETH, MATIC, etc.)
2. Start with PAPER mode first (set `EXECUTION_MODE=PAPER` in .env)
3. Test on testnet before mainnet

### Smart contract compilation fails

**Solution:**
```bash
# Clear cache and recompile
rm -rf cache/ artifacts/
npx hardhat compile
```

## Package.json Scripts Reference

For those who prefer more granular control:

```bash
# Install dependencies only
yarn install                    # or: npm install --legacy-peer-deps
pip3 install -r requirements.txt

# Compile contracts only
yarn compile                    # or: npm run compile

# Start system only (after install)
yarn start                      # or: npm start

# Full setup with compilation
yarn setup:yarn                 # or: npm run setup

# One-click install and run
yarn install-and-run:yarn       # or: npm run install-and-run
```

## Security Checklist

Before running on mainnet with real funds:

- [ ] Using a **dedicated wallet** (not your main wallet)
- [ ] Private key stored **securely** (not committed to git)
- [ ] Tested on **testnet first**
- [ ] Started with **PAPER mode** (EXECUTION_MODE=PAPER)
- [ ] Reasonable **MIN_PROFIT_USD** threshold set
- [ ] Gas limits configured **appropriately**
- [ ] Redis secured (not exposed to internet)
- [ ] `.env` file in `.gitignore`
- [ ] **Limited funds** in bot wallet

## Next Steps

Once Titan is running:

1. **Monitor the logs** - Watch for profit opportunities
2. **Tune parameters** - Adjust MIN_PROFIT_USD, gas limits, etc. in `.env`
3. **Deploy contracts** - Deploy to your target networks
4. **Enable features** - Turn on cross-chain, MEV protection, etc.
5. **Scale up** - Add more networks and increase capital

## Additional Resources

- **[QUICKSTART.md](QUICKSTART.md)** - Detailed 15-minute setup guide
- **[README.md](README.md)** - Complete documentation
- **[MAINNET_QUICKSTART.md](MAINNET_QUICKSTART.md)** - 5-minute mainnet setup
- **[INSTALL.md](INSTALL.md)** - Platform-specific installation
- **[.env.example](.env.example)** - Full configuration template

## Support

Need help?

- **Documentation**: See [README.md](README.md)
- **Issues**: [Open an issue on GitHub](https://github.com/MavenSource/Titan/issues)
- **Security**: Report vulnerabilities responsibly

---

**That's it! You're ready to run Titan with one click! 🚀**
