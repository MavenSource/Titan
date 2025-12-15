# Multi-Aggregator Strategy Documentation

## Overview

Titan now uses an intelligent multi-aggregator routing system that automatically selects the optimal DEX aggregator for each trade based on specific characteristics like value, speed requirements, chain support, and MEV protection needs.

## Supported Aggregators

| Aggregator | Use Case | Chains | MEV Protection | Speed | Priority |
|------------|----------|--------|----------------|-------|----------|
| **1inch** | High-speed single-chain arbitrage | 10+ (ETH, BSC, etc) | High | <400ms | **CRITICAL** |
| **0x/Matcha** | Multi-chain limit orders & routing | 10+ | Moderate | Fast | **HIGH** |
| **Jupiter** | Solana ecosystem arbitrage | Solana only | Low | Very Fast | **MEDIUM** |
| **CoW Swap** | High-value trades needing MEV protection | ETH + bridges | Very High | Moderate | **HIGH** |
| **Rango** | Cross-chain arbitrage (70+ chains) | 70+ | Moderate | Moderate | **HIGH** |
| **OpenOcean** | Multi-chain best price discovery | 30+ | High | Fast | **MEDIUM** |
| **KyberSwap** | Multi-chain with dynamic routing | 14+ | Moderate | Fast | **MEDIUM** |
| **LiFi** | Intent-based bridging (KEEP) | 15+ chains | Moderate | 30-120s | **KEEP** ✅ |

## Routing Decision Tree

The `AggregatorSelector` class automatically routes trades using the following logic:

### 1. Solana Trades → Jupiter
**Condition:** `trade.chain === 'solana'`  
**Reason:** Jupiter is the only Solana aggregator and provides best-in-class routing for Solana DEXs.

### 2. High-Value Trades → CoW Swap
**Condition:** `trade.valueUSD >= $1,000`  
**Reason:** CoW Protocol provides MEV protection through batch auctions and solver competition. Prevents frontrunning on large trades.

### 3. Cross-Chain Trades → Rango or LiFi
**Condition:** `trade.isCrossChain === true`
- **Exotic chains** (Linea, Scroll, Mantle) → Rango (70+ chain support)
- **Standard chains** → LiFi (intent-based bridging, faster)

### 4. Speed-Critical Trades → 1inch
**Condition:** `trade.priority === 'SPEED'` or fast chains (Polygon, Arbitrum, Optimism)  
**Reason:** 1inch Pathfinder provides <400ms API responses and optimal routing.

### 5. Multi-Chain Price Discovery → OpenOcean
**Condition:** `trade.needsBestPrice && chains > 15`  
**Reason:** OpenOcean aggregates liquidity across 30+ chains for comprehensive price discovery.

### 6. Limit Orders → 0x/Matcha
**Condition:** `trade.isLimitOrder === true`  
**Reason:** 0x protocol specializes in limit orders and RFQ (Request for Quote) systems.

### 7. Rewards-Seeking → KyberSwap
**Condition:** `trade.needsRewards === true`  
**Reason:** KyberSwap offers farming rewards and incentives for trades.

### 8. Default → 1inch
**Fallback:** When no specific conditions are met, use 1inch for general best performance.

## Configuration

### Environment Variables

```bash
# Aggregator API Keys
ONEINCH_API_KEY=your_1inch_api_key
ONEINCH_REFERRER_ADDRESS=0xYourAddress
ZEROX_API_KEY=your_0x_api_key
SOLANA_RPC_URL=https://api.mainnet-beta.solana.com
SOLANA_WALLET_PRIVATE_KEY=your_solana_key
COWSWAP_APP_CODE=titan-arbitrage
RANGO_API_KEY=your_rango_api_key
OPENOCEAN_API_KEY=your_openocean_api_key
KYBERSWAP_CLIENT_ID=titan-bot

# Aggregator Strategy Settings
AGGREGATOR_PREFERENCE=auto  # Options: auto, 1inch, cowswap, openocean, etc.
ENABLE_PARALLEL_QUOTES=true  # Fetch quotes from multiple aggregators
MIN_QUOTE_COMPARISON_COUNT=3  # Minimum quotes to compare
PARALLEL_QUOTE_TIMEOUT=5000  # Timeout in milliseconds
HIGH_VALUE_THRESHOLD_USD=1000  # Threshold for high-value trades
COWSWAP_MIN_VALUE_USD=1000  # Minimum trade value for CoW Swap
```

### Manual Aggregator Selection

You can override automatic selection by setting:
```bash
AGGREGATOR_PREFERENCE=1inch,openocean,zerox
```

This will try 1inch first, then OpenOcean, then 0x.

## Parallel Quote Fetching

When `ENABLE_PARALLEL_QUOTES=true`, the system queries multiple aggregators simultaneously and selects the best quote:

```javascript
const quotes = await aggregatorSelector.getMultiAggregatorQuotes(trade);
// Returns: { aggregator: 'ONEINCH', quote: { destAmount: '...' } }
```

**Benefits:**
- Always get the best available price
- Automatic fallback if primary aggregator fails
- Cross-validation of quotes
- Better price discovery

**Performance:**
- Queries 3-5 aggregators in parallel with 5-second timeout
- Total time: ~5 seconds (same as single aggregator due to parallelization)
- Success rate: Higher due to multiple fallback options

## Fallback Mechanism

If the primary aggregator fails, the system automatically tries fallback aggregators:

**Fallback Chain:**
1. 1inch
2. OpenOcean
3. 0x/Matcha
4. KyberSwap

Example log:
```
🎯 Selected aggregator: COWSWAP
❌ COWSWAP execution failed: Network timeout
🔄 Trying fallback: ONEINCH
✅ Fallback successful with ONEINCH
```

## Usage Examples

### Example 1: Standard Trade on Ethereum

```javascript
const aggregatorSelector = new AggregatorSelector(1, provider); // Ethereum

const trade = {
    chainId: 1,
    token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48', // USDC
    destToken: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2', // WETH
    amount: '1000000000', // 1000 USDC
    userAddress: '0x...',
    valueUSD: 1000,
    priority: 'SPEED'
};

const result = await aggregatorSelector.executeTrade(trade);
```

**Result:** Routes to **1inch** (speed-critical)

### Example 2: High-Value Trade

```javascript
const trade = {
    chainId: 1,
    token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    destToken: '0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2',
    amount: '5000000000000', // 5,000,000 USDC
    userAddress: '0x...',
    valueUSD: 5000000,
    priority: 'STANDARD'
};

const result = await aggregatorSelector.executeTrade(trade);
```

**Result:** Routes to **CoW Swap** (MEV protection for $5M trade)

### Example 3: Cross-Chain Trade

```javascript
const trade = {
    chainId: 1,
    source_chain: 1, // Ethereum
    dest_chain: 137, // Polygon
    token: '0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48',
    amount: '1000000000',
    userAddress: '0x...',
    isCrossChain: true
};

const result = await aggregatorSelector.executeTrade(trade);
```

**Result:** Routes to **LiFi** (intent-based bridging)

## API Rate Limits

| Aggregator | Free Tier Limit | Enterprise Tier | Notes |
|------------|-----------------|-----------------|-------|
| 1inch | 1 req/sec | Unlimited | API key required |
| 0x | 10 req/sec | Custom | API key recommended |
| Jupiter | Unlimited | Unlimited | Public API |
| CoW Swap | Unlimited | Unlimited | No API key needed |
| Rango | 1 req/sec | 10 req/sec | API key required |
| OpenOcean | 5 req/sec | Custom | API key recommended |
| KyberSwap | Unlimited | Unlimited | No API key needed |
| LiFi | 10 req/sec | Custom | API key recommended |

## Performance Benchmarks

### Speed (Average API Response Time)

- **1inch:** 200-400ms
- **Jupiter:** 100-300ms (Solana)
- **0x:** 300-500ms
- **OpenOcean:** 400-600ms
- **KyberSwap:** 300-500ms
- **CoW Swap:** 2-5s (batch auction)
- **LiFi:** 1-3s (route calculation)
- **Rango:** 1-2s (multi-chain)

### Gas Optimization

- **1inch:** ⭐⭐⭐⭐⭐ (Pathfinder algorithm)
- **0x:** ⭐⭐⭐⭐ (Good optimization)
- **OpenOcean:** ⭐⭐⭐⭐ (Split routing)
- **KyberSwap:** ⭐⭐⭐⭐ (Dynamic routing)
- **CoW Swap:** ⭐⭐⭐⭐⭐ (Gasless trades)

### MEV Protection

- **CoW Swap:** ⭐⭐⭐⭐⭐ (Batch auction, no public mempool)
- **1inch:** ⭐⭐⭐⭐ (Private transaction support)
- **OpenOcean:** ⭐⭐⭐ (Standard protection)
- **Others:** ⭐⭐ (Standard mempool)

## Troubleshooting

### Issue: "No aggregator route available"

**Causes:**
- All aggregators failed to find a route
- Insufficient liquidity for the token pair
- API keys not configured
- Network connectivity issues

**Solutions:**
1. Check API keys in `.env`
2. Verify token addresses are correct
3. Try reducing trade amount
4. Check aggregator status pages
5. Enable debug logging

### Issue: "Aggregator timeout"

**Causes:**
- Network latency
- Aggregator API slow or down
- Timeout setting too low

**Solutions:**
1. Increase `PARALLEL_QUOTE_TIMEOUT` (default: 5000ms)
2. Check aggregator status: https://status.1inch.io/, etc.
3. Use fallback mechanism (automatic)

### Issue: "CoW Swap not available"

**Causes:**
- CoW Swap only supports Ethereum mainnet and Gnosis Chain
- Trade value below minimum

**Solutions:**
1. Use different chain (ETH mainnet)
2. Increase trade value above $1,000
3. Set `AGGREGATOR_PREFERENCE=1inch` to force different aggregator

## Migration from ParaSwap

### What Changed

1. **Removed:** `@paraswap/sdk` package (deprecated)
2. **Added:** 7 new aggregator SDKs with intelligent routing
3. **Improved:** Automatic aggregator selection based on trade characteristics
4. **New Feature:** Parallel quote fetching for best prices

### Code Changes

**Before:**
```javascript
const { ParaSwapManager } = require('./paraswap_manager');
const pm = new ParaSwapManager(chainId, provider);
const swap = await pm.getBestSwap(srcToken, destToken, amount, userAddress);
```

**After:**
```javascript
const { AggregatorSelector } = require('./aggregator_selector');
const selector = new AggregatorSelector(chainId, provider);
const swap = await selector.executeTrade(trade);
```

### Backward Compatibility

The bot still respects the `use_paraswap` flag but now routes through the new aggregator system:

```javascript
if (signal.use_aggregator || signal.use_paraswap) {
    // Routes through AggregatorSelector
}
```

## Security Considerations

1. **API Keys:** Never commit API keys to git. Use `.env` file.
2. **Private Keys:** Solana wallet key required for Jupiter. Store securely.
3. **MEV Protection:** Use CoW Swap for high-value trades ($1000+).
4. **Slippage:** Default 1% (100 bps). Adjust based on volatility.
5. **Quote Validation:** All quotes are validated before execution.
6. **Simulation:** Transactions are simulated before submission.

## Support and Resources

### Official Documentation

- [1inch API Docs](https://docs.1inch.io/)
- [0x API Docs](https://0x.org/docs/api)
- [Jupiter Docs](https://docs.jup.ag/)
- [CoW Protocol Docs](https://docs.cow.fi/)
- [Rango Docs](https://docs.rango.exchange/)
- [OpenOcean Docs](https://docs.openocean.finance/)
- [KyberSwap Docs](https://docs.kyberswap.com/)
- [LiFi Docs](https://docs.li.fi/)

### Getting API Keys

1. **1inch:** https://portal.1inch.dev/
2. **0x:** https://0x.org/docs/introduction/getting-started
3. **Rango:** https://rango.exchange/developers
4. **OpenOcean:** https://docs.openocean.finance/

### Status Pages

- 1inch: https://status.1inch.io/
- 0x: https://status.0x.org/
- Jupiter: https://status.jup.ag/

## Changelog

### Version 4.2.0 (Current)
- ✅ Added 7 new DEX aggregators
- ✅ Removed deprecated ParaSwap SDK
- ✅ Implemented intelligent routing system
- ✅ Added parallel quote fetching
- ✅ Added automatic fallback mechanism
- ✅ Updated documentation

### Version 4.1.0 (Previous)
- Used ParaSwap as primary aggregator

---

**Note:** This is an advanced feature. Start with automatic routing (`AGGREGATOR_PREFERENCE=auto`) and monitor performance before customizing settings.
