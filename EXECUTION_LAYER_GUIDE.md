# 🚀 Titan Execution Layer - Python-to-Node Communication

## ✅ NO REDIS REQUIRED

The Titan bot now uses **direct HTTP/WebSocket communication** between Python and Node.js, eliminating Redis dependency.

---

## 📊 Architecture

```
┌─────────────────────────┐
│   Python Brain Layer    │
│  (ml/brain.py)          │
│                         │
│  - Opportunity Detection│
│  - Profit Calculation   │
│  - AI Decision Making   │
└────────────┬────────────┘
             │
             │ HTTP/WebSocket
             │ (No Redis!)
             ▼
┌─────────────────────────┐
│  Node.js Execution      │
│  Server                 │
│  (execution_server.js)  │
│                         │
│  - Transaction Building │
│  - Gas Management       │
│  - Simulation           │
│  - Blockchain Execution │
└────────────┬────────────┘
             │
             │ RPC Calls
             ▼
┌─────────────────────────┐
│   Blockchain Networks   │
│                         │
│  Ethereum, Polygon,     │
│  Arbitrum, Base, etc.   │
└─────────────────────────┘
```

---

## 🎯 Execution Modes

### **PAPER Mode (Default)**
- **No real capital required**
- Simulates all transactions
- Tracks profit/loss
- Perfect for testing and development
- Zero risk

```bash
EXECUTION_MODE=PAPER node execution/execution_server.js
```

### **LIVE Mode (Production)**
- **Real capital at risk**
- Executes actual blockchain transactions
- Requires funded wallet
- Private key must be configured
- Use with caution!

```bash
EXECUTION_MODE=LIVE node execution/execution_server.js
```

---

## 🚀 Quick Start

### **Step 1: Install Dependencies**

```bash
# Node.js dependencies
npm install

# Python dependencies
pip install -r requirements.txt
```

### **Step 2: Configure Environment**

```bash
# Copy example environment
cp .env.example .env

# Edit .env file
nano .env
```

Required configuration:
```bash
# Execution Mode
EXECUTION_MODE=PAPER  # or LIVE

# Execution Server
EXECUTION_HOST=localhost
EXECUTION_PORT=8545

# RPC Endpoints (all 15 chains)
RPC_ETHEREUM=https://...
RPC_POLYGON=https://...
# ... etc

# For LIVE mode only:
PRIVATE_KEY=your_private_key_here
EXECUTOR_ADDRESS=0x...  # Your deployed OmniArbExecutor contract
```

### **Step 3: Start Execution Server**

```bash
# Paper trading mode (safe)
npm run start:paper

# OR Live trading mode (requires setup)
npm run start:live
```

You should see:
```
================================================================================
🚀 TITAN EXECUTION SERVER ONLINE
================================================================================
  Mode: PAPER
  HTTP: http://localhost:8545
  WebSocket: ws://localhost:8545
  Chains: 15 configured
  Executor: NOT SET
================================================================================

📡 Endpoints:
  POST /execute        - Execute single trade signal
  POST /execute/batch  - Execute multiple signals
  POST /simulate       - Simulate trade without execution
  GET  /health         - Server health check
  GET  /stats          - Execution statistics
  WS   /               - WebSocket for real-time updates

✅ Ready to receive trade signals from Python brain
```

### **Step 4: Start Python Brain**

In another terminal:

```bash
# Run the brain
python3 ml/brain.py
```

The brain will automatically connect to the execution server via HTTP.

---

## 🧪 Testing

### **Test 1: Server Connection**

```bash
# Test if execution server is healthy
curl http://localhost:8545/health
```

Expected response:
```json
{
  "status": "healthy",
  "mode": "PAPER",
  "chains": 15,
  "uptime": 123.45,
  "stats": {
    "total_signals": 0,
    "executed": 0,
    "failed": 0,
    "paper_executed": 0
  }
}
```

### **Test 2: Python-to-Node Communication**

```bash
# Run comprehensive test suite
python3 test_python_node_communication.py
```

This will test:
- ✅ Connection to execution server
- ✅ Paper trade execution
- ✅ Multi-chain execution
- ✅ Statistics retrieval

### **Test 3: Manual Trade Submission**

```python
import asyncio
from execution.execution_client import ExecutionManager

async def test():
    manager = ExecutionManager()
    await manager.initialize()
    
    result = await manager.submit_trade(
        chain_id=1,
        token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
        amount="1000000000",  # 1000 USDC
        flash_source=1,  # Balancer V3
        protocols=[0],
        routers=["0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"],
        path=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
        extras=[b''],
        expected_profit=50.0
    )
    
    print(result)
    await manager.close()

asyncio.run(test())
```

---

## 📡 HTTP API Reference

### **POST /execute**
Execute a single trade signal.

**Request:**
```json
{
  "chainId": 1,
  "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  "amount": "1000000000",
  "flashSource": 1,
  "protocols": [0, 1],
  "routers": ["0x...", "0x..."],
  "path": ["0x...", "0x..."],
  "extras": ["0x", "0x"],
  "expected_profit": 50.0
}
```

**Response (PAPER mode):**
```json
{
  "success": true,
  "mode": "PAPER",
  "simulation": {
    "success": true,
    "gasUsed": 450000
  },
  "expected_profit": 50.0,
  "timestamp": "2025-12-09T10:30:00.000Z"
}
```

**Response (LIVE mode):**
```json
{
  "success": true,
  "mode": "LIVE",
  "txHash": "0xabc123...",
  "chainId": 1,
  "expected_profit": 50.0,
  "timestamp": "2025-12-09T10:30:00.000Z"
}
```

### **POST /execute/batch**
Execute multiple trade signals.

**Request:**
```json
{
  "signals": [
    { /* signal 1 */ },
    { /* signal 2 */ },
    { /* signal 3 */ }
  ]
}
```

**Response:**
```json
{
  "total": 3,
  "succeeded": 2,
  "failed": 1,
  "results": [...]
}
```

### **POST /simulate**
Simulate trade without execution.

**Request:** Same as `/execute`

**Response:**
```json
{
  "success": true,
  "simulation": {
    "success": true,
    "gasUsed": 450000,
    "error": null
  },
  "estimated_profit": 50.0
}
```

### **GET /health**
Server health check.

**Response:**
```json
{
  "status": "healthy",
  "mode": "PAPER",
  "chains": 15,
  "uptime": 3600
}
```

### **GET /stats**
Execution statistics.

**Response:**
```json
{
  "total_signals": 100,
  "executed": 50,
  "paper_executed": 50,
  "failed": 0,
  "total_profit": 2500.00,
  "mode": "PAPER",
  "connected_clients": 1,
  "providers": 15
}
```

---

## 🔌 WebSocket API

### **Connect**
```javascript
const ws = new WebSocket('ws://localhost:8545');

ws.on('message', (data) => {
  const message = JSON.parse(data);
  console.log(message.type, message);
});
```

### **Message Types**

**Connected:**
```json
{
  "type": "connected",
  "mode": "PAPER",
  "stats": {...}
}
```

**Paper Execution:**
```json
{
  "type": "paper_execution",
  "signal": {...},
  "simulation": {...},
  "timestamp": "2025-12-09T10:30:00.000Z"
}
```

**Live Execution:**
```json
{
  "type": "live_execution",
  "signal": {...},
  "txHash": "0xabc123...",
  "timestamp": "2025-12-09T10:30:00.000Z"
}
```

---

## 🔧 Python Integration

### **Using ExecutionManager**

```python
from execution.execution_client import ExecutionManager

# Initialize
manager = ExecutionManager(
    host="localhost",
    port=8545,
    mode="PAPER"
)

# Connect
await manager.initialize()

# Submit trade
result = await manager.submit_trade(
    chain_id=1,
    token="0x...",
    amount="1000000000",
    flash_source=1,
    protocols=[0, 1],
    routers=["0x...", "0x..."],
    path=["0x...", "0x..."],
    extras=[b'', b''],
    expected_profit=50.0
)

# Check result
if result['success']:
    print(f"Trade executed: {result['mode']}")
else:
    print(f"Trade failed: {result['error']}")

# Get statistics
stats = await manager.get_statistics()
print(stats)

# Cleanup
await manager.close()
```

### **Using Standalone Function**

```python
from execution.execution_client import execute_trade

result = await execute_trade(
    chain_id=1,
    token="0x...",
    amount="1000000000",
    flash_source=1,
    protocols=[0],
    routers=["0x..."],
    path=["0x..."],
    extras=[b''],
    expected_profit=50.0
)
```

---

## 🛡️ Security Considerations

### **PAPER Mode (Safe)**
- ✅ No private keys required
- ✅ No real transactions
- ✅ Safe for development
- ✅ Safe for testing

### **LIVE Mode (Dangerous)**
- ⚠️ Real private keys required
- ⚠️ Real capital at risk
- ⚠️ Real blockchain transactions
- ⚠️ Losses are permanent

**Before going LIVE:**
1. ✅ Test extensively in PAPER mode
2. ✅ Verify contract deployment
3. ✅ Fund wallet with minimal capital
4. ✅ Test with small amounts first
5. ✅ Monitor all transactions
6. ✅ Have kill switch ready

---

## 📊 Monitoring

### **Real-time Monitoring**

```bash
# Watch server logs
node execution/execution_server.js | tee execution.log

# Watch statistics
watch -n 1 'curl -s http://localhost:8545/stats | jq'
```

### **Statistics Dashboard**

The execution server provides real-time statistics:

- **Total Signals:** Number of trade signals received
- **Executed:** Successful live executions
- **Paper Executed:** Successful paper trades
- **Failed:** Failed executions
- **Total Profit:** Cumulative profit (paper or real)

---

## 🐛 Troubleshooting

### **"Failed to connect to execution server"**

**Solution:**
1. Make sure execution server is running:
   ```bash
   node execution/execution_server.js
   ```
2. Check port 8545 is not in use
3. Verify `.env` has correct EXECUTION_PORT

### **"Chain X not configured"**

**Solution:**
Add RPC endpoint for chain in `.env`:
```bash
RPC_ETHEREUM=https://eth-mainnet.g.alchemy.com/v2/YOUR_KEY
```

### **"No wallet configured for LIVE execution"**

**Solution:**
Set PRIVATE_KEY in `.env`:
```bash
PRIVATE_KEY=0x...your_private_key...
```

### **"Simulation failed"**

**Possible causes:**
- Insufficient liquidity
- Invalid router addresses
- Gas price too high
- Contract not deployed

**Solution:**
1. Check contract deployment
2. Verify router addresses
3. Check token balances
4. Review simulation error in logs

---

## 📈 Performance

### **Latency**

- HTTP Request: ~5-10ms (local)
- Trade Simulation: ~100-500ms
- Live Execution: ~1-5s (depends on chain)

### **Throughput**

- Paper mode: ~100 trades/second
- Live mode: Limited by chain block time

### **Scalability**

- Supports concurrent connections
- ThreadPoolExecutor with 20 workers
- Handles multiple chains simultaneously

---

## ✅ Production Checklist

Before deploying to production:

- [ ] Test extensively in PAPER mode
- [ ] Deploy OmniArbExecutor contract
- [ ] Fund wallet with minimal capital
- [ ] Configure all 15 chain RPCs
- [ ] Set up monitoring/alerting
- [ ] Test with small amounts
- [ ] Have emergency shutdown plan
- [ ] Back up private keys securely
- [ ] Monitor gas prices
- [ ] Review all logs

---

## 📝 Summary

**Old Architecture (Redis):**
```
Python → Redis → Node.js → Blockchain
```

**New Architecture (Direct):**
```
Python → HTTP/WS → Node.js → Blockchain
```

**Benefits:**
- ✅ No Redis installation required
- ✅ Simpler deployment
- ✅ Lower latency
- ✅ Better error handling
- ✅ Real-time feedback
- ✅ Easier debugging

---

**Status:** ✅ Fully operational - PAPER and LIVE modes ready

**Last Updated:** December 9, 2025
