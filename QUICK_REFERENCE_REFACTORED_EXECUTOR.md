# Quick Reference: Using Refactored OmniArbExecutor

## TL;DR
The refactored executor uses **enum-based registries** for cleaner route encoding while maintaining backward compatibility with raw addresses. All swaps delegate to the **SwapHandler module** (system-wide component).

## Basic Usage

### 1. Execute Arbitrage (Simple 2-hop)

```javascript
const { ethers } = require("ethers");

// Setup
const executor = await ethers.getContractAt("OmniArbExecutor", EXECUTOR_ADDRESS);

// Define route: USDC -> WETH -> USDC
const protocols = [1, 1];  // UniV2, UniV2 (Quickswap, Sushi)
const routers = [
    "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  // Quickswap
    "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506"   // Sushi
];
const path = [
    "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",  // WETH (output of hop 1)
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"   // USDC (output of hop 2)
];
const extra = ["0x", "0x"];  // No extra data for UniV2

// Encode route
const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extra]
);

// Execute with Balancer flash loan
await executor.execute(
    1,  // Balancer
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  // USDC
    ethers.parseUnits("10000", 6),  // 10k USDC
    routeData
);
```

### 2. Protocol IDs

```javascript
const PROTOCOL = {
    UNIV2: 1,  // Quickswap, Sushi, Pancake, etc.
    UNIV3: 2,  // Uniswap V3
    CURVE: 3   // Curve pools
};
```

### 3. Extra Data Encoding

**UniV2 (Quickswap, Sushi, etc.):**
```javascript
const extra = "0x";  // No extra data needed
```

**UniV3:**
```javascript
const extra = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint24"],
    [3000]  // Fee tier: 100, 500, 3000, or 10000
);
```

**Curve:**
```javascript
const extra = ethers.AbiCoder.defaultAbiCoder().encode(
    ["int128", "int128"],
    [0, 1]  // Pool indices (i=0, j=1)
);
```

## Registry Usage

### Query Token Address
```javascript
// Get USDC address on current chain
const usdc = await executor.resolveToken(Token.USDC_BRIDGED_POLYGON);
```

### Query DEX Router
```javascript
// Get Quickswap router on current chain
const quickswap = await executor.resolveDEX(DEX.QUICKSWAP);
```

### Register New Token
```javascript
await executor.registerToken(
    Chain.POLYGON,
    Token.CUSTOM_TOKEN,
    "0x..."
);
```

### Batch Register
```javascript
await executor.batchRegisterTokens(
    Chain.POLYGON,
    [Token.WMATIC, Token.USDC, Token.WETH],
    ["0x0d5...", "0x279...", "0x7ce..."]
);
```

## Common Patterns

### 3-Hop Arbitrage (Mixed DEXs)
```javascript
// Route: USDC -> WETH (Quickswap) -> WMATIC (UniV3) -> USDC (Curve)
const protocols = [1, 2, 3];
const routers = [QUICKSWAP, UNIV3, CURVE_POOL];
const path = [WETH, WMATIC, USDC];
const extra = [
    "0x",
    ethers.AbiCoder.defaultAbiCoder().encode(["uint24"], [3000]),
    ethers.AbiCoder.defaultAbiCoder().encode(["int128", "int128"], [1, 0])
];
```

### Monitor Events
```javascript
executor.on("ArbitrageExecuted", (source, token, amount, profit) => {
    console.log(`Flash source: ${source}`);
    console.log(`Token: ${token}`);
    console.log(`Amount: ${ethers.formatUnits(amount, 6)}`);
    console.log(`Profit: ${ethers.formatUnits(profit, 6)}`);
});
```

### Adjust Deadline
```javascript
// Set to 5 minutes (default is 3 min)
await executor.setSwapDeadline(300);
```

## Flash Loan Selection

### Balancer (Recommended)
```javascript
await executor.execute(1, token, amount, routeData);
```
- **Pros:** Lower fees, higher liquidity
- **Cons:** Limited to tokens in Balancer pools

### Aave
```javascript
await executor.execute(2, token, amount, routeData);
```
- **Pros:** Wide token support
- **Cons:** 0.09% fee

## Safety Checks

The contract includes:
- ✅ ReentrancyGuard (prevents reentrancy attacks)
- ✅ onlyOwner (only you can execute)
- ✅ Input validation (checks all addresses and amounts)
- ✅ Loss threshold (reverts if >50% loss)
- ✅ Callback authentication (flash loans)

## Gas Optimization Tips

1. **Use UniV2 when possible** (lowest gas)
2. **Minimize hops** (max 5, but 2-3 is optimal)
3. **Batch register** tokens/DEXs during setup
4. **Check gas before execution**:
   ```javascript
   const gasEstimate = await executor.execute.estimateGas(...);
   console.log(`Estimated gas: ${gasEstimate}`);
   ```

## Emergency Functions

### Withdraw Profits
```javascript
await executor.withdraw(tokenAddress);
```

### Withdraw Native
```javascript
await executor.withdrawNative();
```

## Deployment Addresses (Mainnet)

### Balancer V3 Vault (Universal)
```
0xbA1333333333a1BA1108E8412f11850A5C319bA9
```

### Aave V3 Pool (per chain)
- Ethereum: `0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2`
- Polygon: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- Arbitrum: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- Optimism: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`
- Base: `0xA238Dd80C259a72e81d7e4664a9801593F98d1c5`

## Common Tokens (Polygon)

```javascript
const TOKENS = {
    WMATIC: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
    USDC: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
    USDT: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
    DAI: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
    WETH: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
    WBTC: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6"
};
```

## Common DEX Routers (Polygon)

```javascript
const DEX = {
    QUICKSWAP: "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
    SUSHISWAP: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
    UNISWAP_V3: "0xE592427A0AEce92De3Edee1F18E0157C05861564"
};
```

## Testing Checklist

Before mainnet:
- [ ] Deploy to testnet
- [ ] Initialize registries
- [ ] Test 2-hop route with small amount
- [ ] Test 3-hop route
- [ ] Test both flash loan sources
- [ ] Monitor gas usage
- [ ] Verify profit calculations
- [ ] Test emergency withdraw

## Troubleshooting

**"Swap returned zero"**
- Check token approvals
- Verify router addresses
- Ensure pools have liquidity

**"Suspicious loss detected"**
- Route is losing >50% value
- Check pool reserves
- Verify token decimals

**"Invalid router"**
- Router not registered
- Call `registerDEX()` first

**"Token not registered"**
- Token address not in registry
- Call `registerToken()` first

## Need Help?

1. Check `REFACTORED_EXECUTOR_README.md` for detailed guide
2. Review `IMPLEMENTATION_SUMMARY_REFACTORED_EXECUTOR.md`
3. Examine test cases (when added)
4. Ask in team chat

## Pro Tips

💡 **Test routes off-chain first** using simulation  
💡 **Start with 2-hop routes** before attempting complex arbitrage  
💡 **Monitor mempool** for front-running  
💡 **Use MEV protection** (Flashbots, bloxRoute) for valuable trades  
💡 **Keep executor funded** with gas tokens  
💡 **Set up monitoring** for ArbitrageExecuted events  
