# Mainnet Execution Modes

## Overview

Titan now supports two mainnet execution modes, providing full wiring for:
- ✅ Real-time mainnet data ingestion
- ✅ Real arbitrage calculations
- ✅ Paper execution OR live blockchain interaction (configurable)
- ✅ Real-time ML model training on mainnet data

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    MAINNET ORCHESTRATOR                         │
│                  (mainnet_orchestrator.py)                      │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [1] Real-Time Data Ingestion                                  │
│      • Gas prices across all chains                            │
│      • Liquidity checks                                         │
│      • Token prices from DEXs                                   │
│      ↓                                                          │
│  [2] Real Arbitrage Calculations                               │
│      • ProfitEngine: Net profit calculation                     │
│      • DexPricer: Real DEX simulations                         │
│      • BridgeManager: Cross-chain routing                       │
│      ↓                                                          │
│  [3] Mode Selection                                             │
│      ┌────────────────┬──────────────────┐                     │
│      │  PAPER MODE    │   LIVE MODE      │                     │
│      │  (Simulated)   │   (Real)         │                     │
│      └────────────────┴──────────────────┘                     │
│      ↓                                                          │
│  [4] Real-Time ML Training                                      │
│      • MarketForecaster: Gas predictions                        │
│      • QLearningAgent: Strategy optimization                    │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Execution Modes

### 📝 PAPER MODE (Default)

**What it does:**
- ✅ Connects to real mainnet RPCs
- ✅ Calculates real arbitrage opportunities
- ✅ Simulates trades (no blockchain execution)
- ✅ Trains ML models on real mainnet data
- ❌ Does NOT use real funds

**Use cases:**
- Testing strategies with real market conditions
- Validating arbitrage logic before going live
- Training ML models without financial risk
- Collecting performance metrics

**Configuration:**
```bash
# In .env file
EXECUTION_MODE=PAPER
ENABLE_REALTIME_TRAINING=true
```

**Start command:**
```bash
# Method 1: Using make
make start-mainnet-paper

# Method 2: Direct script
./start_mainnet.sh paper

# Method 3: Python orchestrator directly
EXECUTION_MODE=PAPER python3 mainnet_orchestrator.py
```

**Output example:**
```
📝 Paper Trade #123 - 2024-12-13T19:30:00.000Z
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
   Trade ID: PAPER-123-1702491000000
   Chain: 137
   Token: 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174
   Amount: 10000000000
   Type: INTRA_CHAIN
   Expected Profit: $15.42
   Status: ✅ SIMULATED
   Duration: 125ms
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 🔴 LIVE MODE

**What it does:**
- ✅ Connects to real mainnet RPCs
- ✅ Calculates real arbitrage opportunities
- ✅ Executes real trades on blockchain
- ✅ Trains ML models on real mainnet data
- ⚠️ **USES REAL FUNDS**

**Use cases:**
- Production trading with real capital
- Autonomous profit generation
- Real-world strategy validation

**Prerequisites:**
- ✅ Thoroughly tested in PAPER mode
- ✅ Executor contracts deployed on target chains
- ✅ Wallet funded with native tokens (gas)
- ✅ Private key configured in .env
- ⚠️ **Start with small amounts**

**Configuration:**
```bash
# In .env file
EXECUTION_MODE=LIVE
ENABLE_REALTIME_TRAINING=true

# Required for LIVE mode
PRIVATE_KEY=0x...
EXECUTOR_ADDRESS=0x...
```

**Start command:**
```bash
# Method 1: Using make
make start-mainnet-live

# Method 2: Direct script
./start_mainnet.sh live

# Method 3: Python orchestrator directly
EXECUTION_MODE=LIVE python3 mainnet_orchestrator.py
```

**⚠️ WARNING:** LIVE mode executes real blockchain transactions. You can lose funds due to:
- Market volatility
- Failed transactions (gas costs)
- Smart contract bugs
- Front-running/MEV
- Configuration errors

## Components

### 1. Mainnet Orchestrator (`mainnet_orchestrator.py`)

**Role:** Main coordinator for the entire system

**Responsibilities:**
- Initialize and manage all components
- Configure execution mode
- Start real-time ML training loop
- Monitor system health
- Handle graceful shutdown

**Key features:**
- Mode-aware initialization
- Real-time metrics tracking
- Thread-safe training updates
- Circuit breaker integration

### 2. Execution Engine (`execution/bot.js`)

**Role:** Execute trades based on signals from orchestrator

**Responsibilities:**
- Subscribe to Redis trade signals
- Route to paper or live execution
- Handle gas management
- Monitor transaction status

**Paper mode features:**
- Simulates execution timing
- Records all trade metadata
- Maintains trade history
- No blockchain interaction

**Live mode features:**
- Real transaction signing
- MEV protection (BloxRoute)
- Gas optimization
- Transaction monitoring

### 3. AI Brain (`ml/brain.py`)

**Role:** Real-time data analysis and opportunity detection

**Responsibilities:**
- Ingest real-time mainnet data
- Calculate arbitrage opportunities
- Simulate DEX trades
- Broadcast profitable signals

**Key features:**
- Multi-chain Web3 connections
- Parallel opportunity evaluation
- Real DEX price queries
- Profit threshold filtering

### 4. ML Training Pipeline

**Components:**
- `MarketForecaster`: Gas price predictions
- `QLearningAgent`: Strategy optimization
- `FeatureStore`: Historical data management

**Training cycle:**
1. Collect real mainnet data (every cycle)
2. Update forecaster with gas prices
3. Evaluate strategy performance
4. Update RL agent Q-values
5. Save model checkpoints

## Configuration

### Environment Variables

```bash
# === EXECUTION MODE ===
EXECUTION_MODE=PAPER          # or LIVE
ENABLE_REALTIME_TRAINING=true

# === RPC ENDPOINTS (Required) ===
RPC_ETHEREUM=https://...
RPC_POLYGON=https://...
RPC_ARBITRUM=https://...
# ... (other chains)

# === LIVE MODE ONLY ===
PRIVATE_KEY=0x...             # Your wallet private key
EXECUTOR_ADDRESS=0x...        # Deployed contract address

# === STRATEGY PARAMETERS ===
MIN_PROFIT_USD=5.00
MIN_PROFIT_BPS=10
MAX_SLIPPAGE_BPS=50

# === GAS LIMITS ===
MAX_BASE_FEE_GWEI=200
MAX_PRIORITY_FEE_GWEI=50

# === REDIS ===
REDIS_URL=redis://localhost:6379
```

### Chain Configuration

All chains in `core/config.py` are supported:
- Ethereum (1)
- Polygon (137)
- Arbitrum (42161)
- Optimism (10)
- Base (8453)
- BSC (56)
- Avalanche (43114)
- Fantom (250)
- Linea (59144)
- Scroll (534352)
- Mantle (5000)
- ZKsync (324)
- Blast (81457)
- Celo (42220)
- opBNB (204)

## Quick Start Guide

### Step 1: Setup Environment

```bash
# Copy example env
cp .env.example .env

# Edit .env with your RPC endpoints
nano .env
```

### Step 2: Install Dependencies

```bash
# Run setup script
./setup.sh

# Or manually
npm install --legacy-peer-deps
pip3 install -r requirements.txt
```

### Step 3: Start Redis

```bash
# Start Redis server
redis-server --daemonize yes

# Verify it's running
redis-cli ping
```

### Step 4: Start in Paper Mode

```bash
# Start complete mainnet system in paper mode
make start-mainnet-paper

# Or use the script directly
./start_mainnet.sh paper
```

### Step 5: Monitor Activity

The system will:
1. Initialize all components
2. Connect to mainnet RPCs
3. Start scanning for opportunities
4. Log paper trades as they occur
5. Update ML models in real-time

Watch the logs to see:
- Opportunities discovered
- Paper trades executed
- ML training updates
- System metrics

### Step 6: Analyze Results

Paper trades are logged with:
- Trade ID
- Timestamp
- Chain and token details
- Expected profit
- Execution status

Use this data to:
- Validate strategy profitability
- Tune parameters
- Train ML models
- Identify optimal conditions

### Step 7: Go Live (Optional)

**Only after thorough testing:**

```bash
# Deploy contracts
make deploy-polygon

# Update .env with contract addresses
EXECUTOR_ADDRESS=0x...

# Start in live mode
make start-mainnet-live
```

## Monitoring

### Real-Time Metrics

The orchestrator tracks:
- Opportunities found
- Trades executed (paper/live)
- Total calculated profit
- ML training updates
- System uptime

### Logs

Logs are written to:
- `logs/orchestrator.log` - Main system log
- `logs/executor.log` - Execution engine log
- Console output - Real-time activity

View logs:
```bash
# Orchestrator
tail -f logs/orchestrator.log

# Executor
tail -f logs/executor.log

# Both
tail -f logs/*.log
```

### Health Checks

```bash
# Check system health
make health

# Check Redis
redis-cli ping

# Check Python processes
ps aux | grep mainnet_orchestrator

# Check Node processes
ps aux | grep "execution/bot.js"
```

## Troubleshooting

### Issue: No opportunities found

**Possible causes:**
- RPC endpoints not configured
- Gas prices too high
- Insufficient liquidity
- Profit thresholds too high

**Solutions:**
- Check RPC endpoints in .env
- Lower MIN_PROFIT_USD
- Increase MAX_BASE_FEE_GWEI
- Wait for better market conditions

### Issue: Redis connection failed

**Possible causes:**
- Redis not running
- Wrong REDIS_URL in .env

**Solutions:**
```bash
# Start Redis
redis-server --daemonize yes

# Check status
redis-cli ping

# Update .env if needed
REDIS_URL=redis://localhost:6379
```

### Issue: Paper trades not showing

**Possible causes:**
- Execution mode not set
- Bot.js not started
- Redis not connected

**Solutions:**
```bash
# Verify mode
echo $EXECUTION_MODE

# Restart bot
pkill -f "node execution/bot.js"
node execution/bot.js

# Check Redis subscription
redis-cli monitor
```

### Issue: ML training not running

**Possible causes:**
- ENABLE_REALTIME_TRAINING=false
- Training thread crashed

**Solutions:**
```bash
# Enable in .env
ENABLE_REALTIME_TRAINING=true

# Check logs for errors
grep "training" logs/orchestrator.log
```

## Best Practices

### For Paper Mode

1. **Run extended tests** - Minimum 24-48 hours
2. **Track metrics** - Opportunities vs executed trades
3. **Tune parameters** - Adjust thresholds based on results
4. **Validate logic** - Ensure calculations are correct
5. **Train models** - Let ML components learn patterns

### For Live Mode

1. **Start small** - Use minimal capital initially
2. **Monitor closely** - Watch first trades carefully
3. **Set limits** - Use circuit breakers and max trade sizes
4. **Enable MEV protection** - Use BloxRoute for Polygon/BSC
5. **Have exit plan** - Know how to stop system quickly

### General

1. **Keep RPC keys secure** - Use environment variables
2. **Monitor gas prices** - Adjust MAX_BASE_FEE_GWEI as needed
3. **Update regularly** - Pull latest code and dependencies
4. **Backup configs** - Save working .env configurations
5. **Test thoroughly** - Paper mode before live mode

## Safety Features

### Built-in Protections

1. **Simulation before execution** (LIVE mode)
   - All trades simulated via eth_call
   - Reverts caught before transaction
   - Gas estimation with buffer

2. **Circuit breakers**
   - MAX_CONSECUTIVE_FAILURES
   - Automatic cooldown periods
   - Graceful degradation

3. **Profit thresholds**
   - MIN_PROFIT_USD
   - MIN_PROFIT_BPS
   - Gas cost validation

4. **Gas limits**
   - MAX_BASE_FEE_GWEI
   - MAX_PRIORITY_FEE_GWEI
   - Automatic fee adjustment

5. **Liquidity checks**
   - TitanCommander validation
   - TVL verification
   - Slippage protection

## Performance Tuning

### Optimize for Speed

```bash
# Lower confirmation blocks
CONFIRMATION_BLOCKS=1

# Use pending block
PRICE_QUERY_BLOCK_IDENTIFIER=pending

# Increase concurrent evaluations
MAX_CONCURRENT_TXS=5
```

### Optimize for Accuracy

```bash
# Higher confirmation blocks
CONFIRMATION_BLOCKS=3

# Use latest block
PRICE_QUERY_BLOCK_IDENTIFIER=latest

# Lower concurrent evaluations
MAX_CONCURRENT_TXS=2
```

### Optimize for Profit

```bash
# Lower thresholds
MIN_PROFIT_USD=3.00
MIN_PROFIT_BPS=5

# Higher gas tolerance
MAX_BASE_FEE_GWEI=300

# Enable all features
ENABLE_CROSS_CHAIN=true
ENABLE_MEV_PROTECTION=true
```

## System Requirements

### Minimum

- CPU: 2 cores
- RAM: 4 GB
- Disk: 10 GB
- Network: Stable internet connection

### Recommended

- CPU: 4+ cores
- RAM: 8+ GB
- Disk: 20+ GB SSD
- Network: Low-latency connection (<50ms to RPC)

### For Production (LIVE mode)

- CPU: 8+ cores
- RAM: 16+ GB
- Disk: 50+ GB SSD
- Network: Redundant connections
- Backup: Hot standby system

## Support

For issues or questions:
1. Check this documentation
2. Review logs for errors
3. Test in PAPER mode first
4. Consult README.md for general setup

## Version History

- **v4.2.0** - Added mainnet orchestrator and execution modes
- **v4.1.0** - Mainnet safety improvements
- **v4.0.0** - Initial mainnet support

## License

See LICENSE file in repository root.

---

**⚠️ IMPORTANT DISCLAIMER:**

This software is provided as-is for educational and research purposes. Trading cryptocurrencies involves substantial risk. Paper mode provides simulation only - real trading (LIVE mode) can result in financial loss. Always test thoroughly in paper mode before using real funds. The developers assume no liability for financial losses.
