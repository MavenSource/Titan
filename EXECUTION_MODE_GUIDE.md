# 🚀 Titan Arbitrage Bot - Execution Mode Guide

## 📊 EXECUTION MODES OVERVIEW

Titan supports **three execution modes** for flexible deployment:

### 1. **📝 Paper Trading Mode** (RECOMMENDED FOR TESTING)
- **Zero Risk**: Simulates all trades without spending real capital
- **Portfolio Tracking**: Maintains virtual $100,000 portfolio
- **Performance Metrics**: Full P&L tracking, win rate, ROI
- **Learning Mode**: Test strategies safely before going live

### 2. **🔴 Live Mainnet Mode** (PRODUCTION)
- **Real Capital**: Executes actual trades with your funds
- **Safety Guards**: Pre-execution checks, slippage limits, gas validation
- **Requires**: Deployed contract + funded wallet
- **Risk Level**: HIGH - Real money at stake

### 3. **🔄 Hybrid Mode** (ADVANCED)
- **Confidence-Based**: Routes trades based on AI confidence score
- **High Confidence → Live**: Trades >85% confidence execute with real capital
- **Low Confidence → Paper**: Trades <85% confidence simulate only
- **Risk Level**: MEDIUM - Selective real execution

---

## 🛠️ CONFIGURATION

### Step 1: Choose Execution Mode

Edit `/workspaces/Titan/.env`:

```bash
# Options: "paper", "live", "hybrid"
EXECUTION_MODE=paper
```

### Step 2: Configure Mode-Specific Settings

#### Paper Trading Settings:
```bash
EXECUTION_MODE=paper
PAPER_TRADING_CAPITAL=100000.00    # Virtual starting capital
```

#### Live Trading Settings:
```bash
EXECUTION_MODE=live

# CRITICAL: Must be configured for live mode
PRIVATE_KEY=0xYourActualPrivateKeyHere
EXECUTOR_ADDRESS=0xYourDeployedContractAddressHere

# Safety limits
MIN_PROFIT_USD=5.00                # Minimum profit to execute
MAX_SLIPPAGE_BPS=50                # Maximum 0.5% slippage
MAX_CONCURRENT_TXS=3               # Prevent nonce collisions
```

#### Hybrid Mode Settings:
```bash
EXECUTION_MODE=hybrid
HYBRID_CONFIDENCE_THRESHOLD=0.85   # 85% confidence = go live
PAPER_TRADING_CAPITAL=100000.00    # For low-confidence trades
```

---

## 🚀 DEPLOYMENT WORKFLOW

### Phase 1: Paper Trading (Days 1-7)

**Goal**: Validate strategies without risk

```bash
# 1. Set paper trading mode
echo 'EXECUTION_MODE=paper' >> .env

# 2. Start the system
python3 ml/brain.py
```

**Expected Output**:
```
📝 Paper Trading Mode Initialized | Capital: $100,000.00
🧠 Booting Apex-Omega Titan Brain...
✅ System Online. Tracking 150 nodes.
🚀 Titan Brain: Engaging Hyper-Parallel Scan Loop...
📝 Simulating Trade PAPER_137_1
   Expected Profit: $12.50
✅ Paper Trade Complete | Net: $12.25 | Capital: $100,012.25
```

**Performance Tracking**:
```python
# Check paper trading stats
python3 -c "
from core.execution_modes import PaperTradingSimulator
import redis
r = redis.Redis(decode_responses=True)
capital = r.get('paper_capital')
print(f'Current Capital: ${float(capital):,.2f}')
"
```

### Phase 2: Contract Deployment (Before Live Trading)

**Required**: Deploy OmniArbExecutor.sol to all chains

```bash
# 1. Configure Hardhat networks (hardhat.config.js)
# 2. Deploy to mainnet
npx hardhat run scripts/deploy.js --network polygon

# 3. Update .env with deployed address
echo 'EXECUTOR_ADDRESS=0xYourNewContractAddress' >> .env

# 4. Fund the wallet
# Send MATIC, USDC, or ETH to your wallet address
```

**Deployment Checklist**:
- [ ] Contract deployed on target chains
- [ ] EXECUTOR_ADDRESS updated in .env
- [ ] Wallet funded with gas + initial capital
- [ ] PRIVATE_KEY securely configured
- [ ] Flash loan providers verified (Balancer V3 + Aave V3)

### Phase 3: Hybrid Mode (Days 8-14)

**Goal**: Gradually transition to live trading

```bash
# 1. Switch to hybrid mode
echo 'EXECUTION_MODE=hybrid' >> .env
echo 'HYBRID_CONFIDENCE_THRESHOLD=0.90' >> .env  # Conservative 90% threshold

# 2. Restart system
python3 ml/brain.py
```

**Expected Output**:
```
🔄 Hybrid Mode Initialized | Confidence Threshold: 0.90
📝 Low confidence (0.78) - Routing to PAPER execution
🔴 High confidence (0.92) - Routing to LIVE execution
🔴 Live Trade Submitted | ID: LIVE_137_1
```

**Confidence Tuning**:
- Start with **0.90** (very conservative)
- Lower to **0.85** after 50+ successful paper trades
- Lower to **0.80** after 100+ successful paper trades

### Phase 4: Full Live Mode (Production)

**Goal**: Maximum profit extraction

```bash
# 1. Switch to live mode
echo 'EXECUTION_MODE=live' >> .env

# 2. Final safety check
python3 -c "
import os
assert os.getenv('PRIVATE_KEY') != '0xYOUR_REAL_PRIVATE_KEY_HERE'
assert os.getenv('EXECUTOR_ADDRESS') != '0xYOUR_DEPLOYED_CONTRACT_ADDRESS_HERE'
print('✅ Configuration validated')
"

# 3. Start production system
python3 ml/brain.py
```

**Production Monitoring**:
```bash
# Monitor live trades
redis-cli
> LRANGE live_trades 0 10

# Check pending transactions
> SMEMBERS pending_txs

# View performance
> GET live_profit_total
```

---

## 📊 MONITORING & PERFORMANCE

### Real-Time Metrics

```python
# Get comprehensive stats
python3 -c "
from core.execution_modes import ExecutionModeFactory
executor = ExecutionModeFactory.create()
stats = executor.get_performance_summary()

print('📊 Performance Summary:')
print(f'Mode: {stats[\"mode\"]}')
print(f'Total Trades: {stats[\"total_trades\"]}')
print(f'Win Rate: {stats[\"win_rate\"]:.2f}%')

if 'current_capital' in stats:
    print(f'Capital: ${stats[\"current_capital\"]:,.2f}')
    print(f'Total Profit: ${stats[\"total_profit\"]:,.2f}')
    print(f'ROI: {stats[\"roi\"]:.2f}%')
"
```

### Trade History Analysis

```python
# Analyze recent trades
import redis
import json

r = redis.Redis(decode_responses=True)

# Last 20 paper trades
paper_trades = [json.loads(t) for t in r.lrange('paper_trades', 0, 19)]

# Last 20 live trades
live_trades = [json.loads(t) for t in r.lrange('live_trades', 0, 19)]

# Calculate average profit
avg_profit = sum(float(t['net_profit']) for t in paper_trades) / len(paper_trades)
print(f'Average Profit per Trade: ${avg_profit:.2f}')
```

---

## 🛡️ SAFETY FEATURES

### Pre-Execution Checks (Live Mode)

All live trades pass through 6 safety checks:

1. **Minimum Profit**: `expected_profit >= MIN_PROFIT_USD`
2. **Slippage Tolerance**: `slippage_bps <= MAX_SLIPPAGE_BPS`
3. **Concurrent Limit**: `pending_txs < MAX_CONCURRENT_TXS`
4. **Required Fields**: All trade parameters present
5. **Private Key**: PRIVATE_KEY configured
6. **Contract Deployed**: EXECUTOR_ADDRESS configured

**If any check fails, trade is rejected automatically.**

### Gas Protection

```python
# Automatically monitors gas prices
# Postpones trades during gas spikes
# Uses EIP-1559 dynamic fees

Chain: Polygon
Current Gas: 150 gwei
Threshold: 200 gwei
Status: ✅ SAFE TO TRADE

Chain: Ethereum  
Current Gas: 80 gwei
Threshold: 100 gwei
Status: ✅ SAFE TO TRADE
```

### Slippage Protection

```python
# Simulates exact output before execution
# Rejects trades with >0.5% slippage
# Uses DEX quoters for accurate estimates

Expected Output: $1000.00
Simulated Output: $995.50
Slippage: 0.45% ✅ WITHIN LIMIT

Expected Output: $1000.00
Simulated Output: $993.00
Slippage: 0.70% ❌ REJECTED
```

---

## 🔧 TROUBLESHOOTING

### Paper Trading Shows No Trades

**Causes**:
- Redis not running: `sudo service redis-server start`
- No profitable opportunities detected
- Gas prices too high

**Solution**:
```bash
# Check Redis
redis-cli ping

# Lower profit threshold
echo 'MIN_PROFIT_USD=2.00' >> .env

# Check gas prices
python3 -c "
from ml.brain import OmniBrain
brain = OmniBrain()
brain.initialize()
for cid in [1, 137, 42161]:
    gas = brain._get_gas_price(cid)
    print(f'Chain {cid}: {gas} gwei')
"
```

### Live Trades Rejected

**Check Configuration**:
```bash
# Validate setup
python3 -c "
import os
from dotenv import load_dotenv
load_dotenv()

print('Private Key:', 'SET' if os.getenv('PRIVATE_KEY') and os.getenv('PRIVATE_KEY') != '0xYOUR_REAL_PRIVATE_KEY_HERE' else 'NOT SET')
print('Executor:', os.getenv('EXECUTOR_ADDRESS'))
print('Min Profit:', os.getenv('MIN_PROFIT_USD'))
print('Max Slippage:', os.getenv('MAX_SLIPPAGE_BPS'))
"
```

### Transactions Failing

**Common Issues**:
1. **Insufficient Gas**: Increase `GAS_LIMIT_MULTIPLIER` in .env
2. **Nonce Collision**: Lower `MAX_CONCURRENT_TXS`
3. **Slippage Too High**: Market moved between simulation and execution
4. **Flash Loan Revert**: Insufficient profit to cover flash loan fee + gas

**Debug Mode**:
```bash
# Enable verbose logging
export LOG_LEVEL=DEBUG
python3 ml/brain.py
```

---

## 📈 OPTIMIZATION STRATEGIES

### Maximize Paper Trading Profit

1. **Lower thresholds**: `MIN_PROFIT_USD=2.00`
2. **Increase chains**: Enable all 15 chains
3. **More DEX protocols**: Use all 46 routers
4. **Faster scanning**: Reduce `time.sleep()` in scan loop

### Transition to Live Trading

**Confidence Score Progression**:
```
Week 1: PAPER only (gather data)
Week 2: HYBRID @ 0.95 threshold (very conservative)
Week 3: HYBRID @ 0.90 threshold
Week 4: HYBRID @ 0.85 threshold
Week 5: LIVE mode (if profitable)
```

**Capital Allocation**:
```
Start: $1,000 (test with small capital)
After 50 trades @ >70% win rate: $5,000
After 100 trades @ >75% win rate: $10,000
After 200 trades @ >80% win rate: $50,000+
```

---

## 🎯 PRODUCTION CHECKLIST

Before enabling `EXECUTION_MODE=live`:

- [ ] Paper trading showing consistent profit (>70% win rate)
- [ ] Tested on at least 100 paper trades
- [ ] Contract deployed to target chains
- [ ] Wallet funded with sufficient gas + capital
- [ ] PRIVATE_KEY securely stored (consider hardware wallet)
- [ ] Backup RPC endpoints configured
- [ ] Redis persistence enabled
- [ ] Monitoring/alerting set up (Telegram/Discord)
- [ ] Emergency stop mechanism tested
- [ ] Insurance capital reserved (10% of total)

---

## 🚨 EMERGENCY PROCEDURES

### Stop All Trading

```bash
# 1. Terminate Python process
pkill -f "python3 ml/brain.py"

# 2. Clear pending transactions
redis-cli
> DEL pending_txs
> SAVE

# 3. Switch to paper mode
echo 'EXECUTION_MODE=paper' >> .env
```

### Withdraw Funds from Contract

```solidity
// Use Hardhat console
npx hardhat console --network polygon

const executor = await ethers.getContractAt("OmniArbExecutor", "0xYourContractAddress");
const tx = await executor.emergencyWithdraw("0xTokenAddress", "0xYourWalletAddress");
await tx.wait();
```

---

## 📞 SUPPORT

**Documentation**: `/workspaces/Titan/L2_CONFIGURATION_COMPLETE.md`  
**Validation**: `python3 validate_full_system.py`  
**Configuration**: `/workspaces/Titan/.env`

**Status**: ✅ **ALL EXECUTION MODES FULLY WIRED & PRODUCTION READY**
