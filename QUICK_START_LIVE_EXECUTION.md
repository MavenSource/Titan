# TITAN MAINNET QUICK START GUIDE

## 🚀 LIVE Blockchain Execution — Production Ready

This guide will get Titan running with **live blockchain execution** on Polygon mainnet.

---

## ⚡ QUICK START (5 Minutes)

### Step 1: Install Dependencies

```bash
# Python dependencies
pip install -r requirements.txt

# Node.js dependencies
npm install
```

### Step 2: Configure Environment

Copy `.env.example` to `.env` and configure:

```bash
cp .env.example .env
```

#### Minimum Required Configuration:

```bash
# === EXECUTION MODE ===
EXECUTION_MODE=PAPER  # Start with PAPER mode first!

# === POLYGON RPC (Required) ===
RPC_POLYGON=https://polygon-mainnet.g.alchemy.com/v2/YOUR_ALCHEMY_KEY

# === FOR LIVE MODE (Optional initially) ===
PRIVATE_KEY=0x...  # Your wallet private key (64 hex chars)
EXECUTOR_ADDRESS_POLYGON=0x...  # Your deployed executor contract

# === SAFETY PARAMETERS ===
MAX_BASE_FEE_GWEI=500
MIN_PROFIT_USD=5.0
MAX_SLIPPAGE_BPS=50
```

### Step 3: Validate System

```bash
# Test execution components
node test_execution_system.js

# Run system readiness check
python -m core.system_readiness

# Expected: "System is ready for operation"
```

### Step 4: Start in PAPER Mode

```bash
# Terminal 1: Start Redis (if not running)
redis-server

# Terminal 2: Start Titan orchestrator
python mainnet_orchestrator.py

# Terminal 3: Start execution bot
npm start
```

---

## 🔴 ENABLING LIVE EXECUTION

⚠️ **WARNING**: Live mode executes real transactions with real funds!

### Prerequisites

1. **Deploy Executor Contract** on Polygon:
   ```bash
   npx hardhat run scripts/deploy.js --network polygon
   ```

2. **Fund Your Wallet** with MATIC for gas

3. **Update `.env`**:
   ```bash
   EXECUTION_MODE=LIVE
   PRIVATE_KEY=0x...
   EXECUTOR_ADDRESS_POLYGON=0x...
   ```

4. **Validate Configuration**:
   ```bash
   node test_execution_system.js
   python -m core.system_readiness
   ```

5. **Start With Small Thresholds**:
   ```bash
   MIN_PROFIT_USD=50.0  # Higher threshold initially
   MAX_BASE_FEE_GWEI=200  # Lower gas limit
   ```

6. **Monitor Closely** during first executions

---

## 🛡️ SAFETY FEATURES

### Multi-Layer Execution Gates

✅ **Signal Level** - Rejects non-Polygon signals  
✅ **Transaction Signing** - Hard-blocks Ethereum/Arbitrum  
✅ **Execution Mode** - PAPER mode cannot sign transactions  
✅ **Calldata Limit** - 32KB max enforced  
✅ **Gas Validation** - Fees checked against MAX_BASE_FEE_GWEI  
✅ **Profit Checks** - Must exceed 2x gas cost  
✅ **Simulation** - All transactions simulated before signing  

### Chain Execution Status

- **Polygon (137)**: 🟢 LIVE EXECUTION ENABLED
- **Ethereum (1)**: 🟡 CONFIGURED (Execution Disabled)
- **Arbitrum (42161)**: 🟡 CONFIGURED (Execution Disabled)

---

## 📊 UNDERSTANDING MODES

### PAPER Mode (Safe for Testing)
- ✅ Real-time mainnet data
- ✅ Real arbitrage calculations
- ❌ **NO blockchain execution**
- ❌ No private key needed
- Perfect for: Testing, monitoring, development

### LIVE Mode (Production)
- ✅ Real-time mainnet data
- ✅ Real arbitrage calculations
- ✅ **REAL blockchain execution**
- ✅ Private key required
- ⚠️ **Real funds at risk**
- Only use when: Ready for production

---

## 🔍 MONITORING

### Logs to Watch

**PAPER Mode**:
```
📝 Paper Trade #1 - [timestamp]
   Token: 0x...
   Expected Profit: $25.00
   Status: ✅ SIMULATED
```

**LIVE Mode**:
```
🎯 [LIVE TRADE #1] Chain 137 - [timestamp]
   Token: 0x...
   Expected Profit: $25.00
🔐 Signing transaction...
✅ Transaction signed
🚀 [BLOXROUTE] Bundle submitted successfully
   Bundle Hash: 0x...
```

### Execution Gate Logs

If signal for Ethereum/Arbitrum received:
```
🛑 [EXECUTION GATE] Ethereum execution is DISABLED
   Only Polygon (137) is enabled for live execution
   Signal ignored
```

---

## 🧪 TESTING CHECKLIST

Before going live:

- [ ] `node test_execution_system.js` passes
- [ ] `python -m core.system_readiness` returns "ready"
- [ ] PAPER mode runs for 24+ hours without errors
- [ ] Executor contract deployed on Polygon
- [ ] Wallet funded with MATIC
- [ ] `.env` configured with production values
- [ ] Safety parameters set appropriately
- [ ] Monitoring setup ready

---

## 📋 TROUBLESHOOTING

### "RPC connection failed"
- Check RPC_POLYGON URL in `.env`
- Ensure Alchemy/Infura API key is valid
- Test RPC: `curl -X POST <RPC_URL> -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'`

### "Executor address not configured"
- Set EXECUTOR_ADDRESS_POLYGON in `.env`
- Deploy contract: `npx hardhat run scripts/deploy.js --network polygon`

### "Invalid private key format"
- Ensure 0x prefix + 64 hex characters
- Example: `0x1234...abcd` (66 chars total)

### "EXECUTION BLOCKED" messages
- This is correct! Ethereum/Arbitrum are intentionally blocked
- Only Polygon can execute in LIVE mode

### bloXroute submission fails
- Set BLOXROUTE_AUTH in `.env` (optional)
- System will fallback to public mempool automatically
- Check: `bloxRoute.getConfigStatus()`

---

## 🔗 ARCHITECTURE

```
Python (Orchestrator)
  ↓ Redis Signals
Node.js (Execution)
  ↓ Chain Gate
  ↓ TX Builder (32KB limit)
  ↓ Simulation
  ↓ TX Signer (Polygon only)
  ↓ Merkle Bundle
  ↓ bloXroute (or mempool)
  ↓ Blockchain
```

---

## 📚 KEY FILES

- `core/chain_registry.py` - Chain execution configuration
- `core/system_readiness.py` - Startup validation
- `execution/tx_builder.js` - Transaction construction
- `execution/tx_signer.js` - Signing with gates
- `execution/bot.js` - Execution engine
- `mainnet_orchestrator.py` - System orchestrator
- `test_execution_system.js` - Validation suite

---

## 🎯 NEXT STEPS

1. **Deploy to Production**: Follow "ENABLING LIVE EXECUTION" above
2. **Monitor Closely**: Watch first live executions
3. **Tune Parameters**: Adjust MIN_PROFIT_USD based on gas costs
4. **Enable bloXroute**: Set BLOXROUTE_AUTH for MEV protection
5. **Scale Gradually**: Increase thresholds as confidence grows

---

## 🆘 SUPPORT

For issues or questions:
1. Check `MAINNET_WIRING_COMPLETE.md` for detailed architecture
2. Run `node test_execution_system.js` for component status
3. Run `python -m core.system_readiness` for system health
4. Review logs for explicit error messages

---

**Status**: ✅ Production Ready  
**Chains**: Polygon (LIVE), Ethereum/Arbitrum (Configured)  
**Safety**: Multi-layer execution gates operational  
**Testing**: All components validated

🚀 **Ready to execute on Polygon mainnet!**
