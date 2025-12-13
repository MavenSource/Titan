# Mainnet Quick Start Guide

## 🚀 5-Minute Setup

This guide gets you running on mainnet in paper mode (simulated execution) in 5 minutes.

## Prerequisites

✅ Redis installed and running
✅ Node.js 18+ and Python 3.11+ installed  
✅ RPC endpoints configured in .env

## Step 1: Configure Environment (2 minutes)

```bash
# Copy example configuration
cp .env.example .env

# Edit .env with your RPC endpoints
nano .env
```

**Minimum required for paper mode:**
```bash
EXECUTION_MODE=PAPER
RPC_ETHEREUM=https://mainnet.infura.io/v3/YOUR_KEY
RPC_POLYGON=https://polygon-mainnet.infura.io/v3/YOUR_KEY
# ... add other RPC endpoints
```

**Note:** PRIVATE_KEY and EXECUTOR_ADDRESS not required for paper mode!

## Step 2: Start System (1 minute)

```bash
# Start Redis (if not running)
redis-server --daemonize yes

# Start Titan in paper mode
make start-mainnet-paper
```

## Step 3: Monitor Activity (2 minutes)

Watch for paper trades in the executor terminal:

```
📝 Paper Trade #1 - 2024-12-13T19:30:00.000Z
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Trade ID: PAPER-1-1702491000000
   Chain: 137 (Polygon)
   Token: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
   Amount: 10000000000
   Type: INTRA_CHAIN
   Expected Profit: $15.42
   Status: ✅ SIMULATED
   Duration: 125ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

## What's Happening?

1. **Orchestrator (Python)** scans mainnet for arbitrage opportunities
2. **Brain** calculates real profits using live DEX prices
3. **Executor (Node.js)** simulates trades (no blockchain transactions)
4. **ML Models** train on real mainnet data in background

## Understanding Output

### Orchestrator Terminal
- 🔍 Scanning for opportunities
- 💰 Profitable opportunities found
- ⚡ Signals broadcasted
- 🧠 ML training updates

### Executor Terminal  
- 📝 Paper trades executed
- ✅ Simulation results
- 📊 Performance metrics

## Next Steps

### Tune Parameters

Edit `.env` to adjust strategy:

```bash
# Profit thresholds
MIN_PROFIT_USD=5.00        # Minimum $5 profit
MIN_PROFIT_BPS=10          # 0.1% minimum margin

# Gas limits
MAX_BASE_FEE_GWEI=200      # Skip if gas > 200 gwei
```

### Enable More Chains

Add more RPC endpoints to `.env`:

```bash
RPC_ARBITRUM=https://...
RPC_OPTIMISM=https://...
RPC_BASE=https://...
```

### Analyze Results

Let system run for 24-48 hours in paper mode to:
- Validate arbitrage opportunities are real
- Measure expected profit vs gas costs
- Train ML models on market patterns
- Tune parameters for your risk tolerance

## Going Live (After Testing)

⚠️ **Only after extensive paper mode testing:**

1. **Deploy contracts:**
   ```bash
   make deploy-polygon
   ```

2. **Add contract addresses to .env:**
   ```bash
   EXECUTOR_ADDRESS=0x...
   PRIVATE_KEY=0x...
   ```

3. **Start in live mode:**
   ```bash
   make start-mainnet-live
   ```

## Stopping System

```bash
# Press Ctrl+C in each terminal
# Or use:
make stop
```

## Troubleshooting

### No opportunities found
- Check RPC endpoints are working
- Gas prices might be too high (increase MAX_BASE_FEE_GWEI)
- Lower MIN_PROFIT_USD temporarily

### Redis connection failed
```bash
redis-server --daemonize yes
redis-cli ping  # Should return "PONG"
```

### Import errors
```bash
pip3 install -r requirements.txt
npm install --legacy-peer-deps
```

## Full Documentation

- **[MAINNET_MODES.md](MAINNET_MODES.md)** - Complete mode guide
- **[QUICKSTART.md](QUICKSTART.md)** - General setup guide
- **[README.md](README.md)** - System overview

## Support

For detailed documentation on modes, configuration, and advanced features, see MAINNET_MODES.md.

---

**🎉 That's it! You're now running Titan on mainnet in paper mode.**

Let it run, monitor the results, tune parameters, and when ready, switch to live mode.
