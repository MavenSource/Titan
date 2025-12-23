# OmniArbExecutor - Refactored with Custom Enum Logic

## Overview

The refactored `OmniArbExecutor.sol` implements a comprehensive enum-based registry system for cleaner, more maintainable arbitrage route encoding across multiple chains. This design **prioritizes reusing system-wide components** (SwapHandler module) to minimize technical debt and ensure interoperability.

## Key Features

### 1. **Chain Enum Registry**
Maps `block.chainid` to human-readable chain identifiers:

```solidity
enum Chain {
    ETHEREUM,      // chainId: 1
    POLYGON,       // chainId: 137
    ARBITRUM,      // chainId: 42161
    OPTIMISM,      // chainId: 10
    BASE,          // chainId: 8453
    BSC,           // chainId: 56
    AVALANCHE,     // chainId: 43114
    FANTOM,        // chainId: 250
    LINEA,         // chainId: 59144
    SCROLL,        // chainId: 534352
    MANTLE,        // chainId: 5000
    ZKSYNC,        // chainId: 324
    BLAST,         // chainId: 81457
    CELO,          // chainId: 42220
    OPBNB          // chainId: 204
}
```

### 2. **DEX Enum Registry**
Per-chain router registry with common DEX protocols:

```solidity
enum DEX {
    UNISWAP_V2,
    UNISWAP_V3,
    SUSHISWAP,
    QUICKSWAP,      // Polygon
    PANCAKESWAP,    // BSC
    CURVE,
    BALANCER,
    TRADER_JOE,     // Avalanche
    SPOOKYSWAP,     // Fantom
    AERODROME,      // Base
    VELODROME       // Optimism
}
```

### 3. **Token Enum Registry**
Comprehensive token registry with **WRAPPED + BRIDGED variants**:

```solidity
enum Token {
    // Native wrapped
    WETH, WMATIC, WBNB, WAVAX, WFTM,
    
    // Stablecoins (native)
    USDC, USDT, DAI, FRAX,
    
    // Bridged stablecoins
    USDC_BRIDGED_POLYGON,
    USDC_BRIDGED_ARBITRUM,
    USDC_BRIDGED_OPTIMISM,
    USDC_BRIDGED_BASE,
    // ... etc
    
    // Bridged ETH variants
    WETH_BRIDGED_POLYGON,
    WETH_BRIDGED_ARBITRUM,
    // ... etc
    
    // Other major tokens
    LINK, AAVE, CRV, BAL, SUSHI, WBTC
}
```

## Architecture

### System-Wide Component Reuse

The refactored executor **delegates all swap operations to SwapHandler** (system-wide module):

```solidity
contract OmniArbExecutor is Ownable, ReentrancyGuard, SwapHandler {
    
    function _runRoute(...) internal returns (uint256) {
        // For each hop, delegate to SwapHandler._executeSwap()
        currentAmount = _executeSwap(
            protocols[i],    // Protocol ID (1=UniV2, 2=UniV3, 3=Curve)
            routers[i],      // Router address
            currentToken,    // Input token
            path[i],         // Output token
            currentAmount,   // Input amount
            extra[i]         // Protocol-specific data
        );
    }
}
```

### Flash Loan Support

**Aave V3 Flash Loan:**
```solidity
execute(
    2,                  // flashSource = Aave
    loanToken,
    loanAmount,
    routeData
)
```

**Balancer V3 Flash Loan (Unlock Pattern):**
```solidity
execute(
    1,                  // flashSource = Balancer
    loanToken,
    loanAmount,
    routeData
)
```

## Usage

### Deployment

1. **Deploy OmniArbExecutor:**
```javascript
const OmniArbExecutor = await ethers.deployContract("OmniArbExecutor", [
    balancerVaultAddress,  // Balancer V3 Vault
    aavePoolAddress        // Aave V3 Pool
]);
```

2. **Initialize Registries:**

Deploy `RegistryInitializer.sol` and call initialization functions:

```javascript
const initializer = await ethers.deployContract("RegistryInitializer");

// Initialize Polygon (example)
await initializer.initPolygonTokens(executor.address);
await initializer.initPolygonDEXs(executor.address);
```

Or manually register:

```javascript
// Register tokens
await executor.registerToken(
    Chain.POLYGON,              // Chain enum
    Token.USDC_BRIDGED_POLYGON, // Token enum
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174" // Address
);

// Register DEXs
await executor.registerDEX(
    Chain.POLYGON,              // Chain enum
    DEX.QUICKSWAP,              // DEX enum
    "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff" // Router address
);
```

### Executing Arbitrage

#### Route Data Encoding

Routes are encoded as parallel arrays:

```javascript
const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [
        protocols,  // [1, 2, 3] = [UniV2, UniV3, Curve]
        routers,    // [quickswap, uniV3, curvePool]
        path,       // [USDC, WETH, DAI] (output tokens)
        extra       // Protocol-specific data
    ]
);
```

#### Protocol-Specific Extra Data

**UniV2-style (Quickswap, Sushi, etc.):**
```javascript
extra[i] = "0x"  // Empty bytes (no extra data needed)
```

**UniV3:**
```javascript
extra[i] = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint24"],
    [3000]  // Fee tier: 100, 500, 3000, 10000
);
```

**Curve:**
```javascript
extra[i] = ethers.AbiCoder.defaultAbiCoder().encode(
    ["int128", "int128"],
    [0, 1]  // Pool indices (i, j)
);
```

#### Example: 3-hop Arbitrage on Polygon

```javascript
// Route: USDC -> WETH (QuickSwap) -> WMATIC (UniV3) -> USDC (Curve)

const protocols = [1, 2, 3];  // UniV2, UniV3, Curve

const routers = [
    "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff", // Quickswap
    "0xE592427A0AEce92De3Edee1F18E0157C05861564", // UniV3
    "0x445FE580eF8d70FF569aB36e80c647af338db351"  // Curve aTriCrypto
];

const path = [
    "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619", // WETH
    "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270", // WMATIC
    "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"  // USDC (back)
];

const extra = [
    "0x",                                            // QuickSwap: no extra
    ethers.AbiCoder.defaultAbiCoder().encode(["uint24"], [3000]),  // UniV3: 0.3% fee
    ethers.AbiCoder.defaultAbiCoder().encode(["int128", "int128"], [1, 0])  // Curve: indices
];

const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extra]
);

// Execute with Balancer flash loan
await executor.execute(
    1,                    // Balancer flash loan
    usdcAddress,          // Loan token
    ethers.parseUnits("10000", 6),  // 10,000 USDC
    routeData
);
```

## Registry Management

### Query Functions

```solidity
// Get current chain enum
Chain chain = executor.getCurrentChain();

// Resolve token enum to address
address usdc = executor.resolveToken(Token.USDC_BRIDGED_POLYGON);

// Resolve DEX enum to router
address quickswap = executor.resolveDEX(DEX.QUICKSWAP);
```

### Batch Registration

```javascript
await executor.batchRegisterTokens(
    Chain.POLYGON,
    [Token.WMATIC, Token.USDC_BRIDGED_POLYGON, Token.WETH],
    ["0x0d5...", "0x279...", "0x7ce..."]
);

await executor.batchRegisterDEXs(
    Chain.POLYGON,
    [DEX.QUICKSWAP, DEX.SUSHISWAP, DEX.UNISWAP_V3],
    ["0xa5E...", "0x1b0...", "0xE59..."]
);
```

## Gas Optimization

- **Registry lookups** are O(1) mapping operations
- **SwapHandler reuse** eliminates duplicate swap logic
- **Enum-based encoding** reduces calldata size vs string identifiers
- **SafeERC20** handles token approvals efficiently (USDT-compatible)

## Security Features

- **ReentrancyGuard** on `execute()` function
- **onlyOwner** access control
- **Input validation** (zero addresses, array lengths, protocol IDs)
- **Flash loan callback authentication** (checks `msg.sender`)
- **Sanity checks** on swap outputs (50% loss threshold)

## Integration with Node.js Executor

```javascript
// Off-chain route calculation
const route = await calculateOptimalRoute(inputToken, amount);

// Encode route
const routeData = encodeRoute(route);

// Execute on-chain
const tx = await executor.execute(
    flashSource,
    loanToken,
    loanAmount,
    routeData
);

// Monitor events
executor.on("ArbitrageExecuted", (source, token, amount, profit) => {
    console.log(`Profit: ${ethers.formatUnits(profit, 6)} USDC`);
});
```

## Benefits vs. Previous Implementation

✅ **System-wide component reuse** (SwapHandler module)  
✅ **Cleaner route encoding** with enums vs raw addresses  
✅ **Multi-chain support** with chain-aware registries  
✅ **Wrapped + bridged token variants** properly distinguished  
✅ **Batch registration** for efficient deployment  
✅ **Gas optimized** with SafeERC20 and minimal storage  
✅ **Enhanced security** with ReentrancyGuard and validation  

## Supported Chains

| Chain | Chain ID | Status |
|-------|----------|--------|
| Ethereum | 1 | ✅ Ready |
| Polygon | 137 | ✅ Ready |
| Arbitrum | 42161 | ✅ Ready |
| Optimism | 10 | ✅ Ready |
| Base | 8453 | ✅ Ready |
| BSC | 56 | ✅ Ready |
| Avalanche | 43114 | ✅ Ready |
| Fantom | 250 | ✅ Ready |
| Linea | 59144 | 🔧 Add registries |
| Scroll | 534352 | 🔧 Add registries |
| Mantle | 5000 | 🔧 Add registries |
| zkSync | 324 | 🔧 Add registries |
| Blast | 81457 | 🔧 Add registries |
| Celo | 42220 | 🔧 Add registries |
| opBNB | 204 | 🔧 Add registries |

## Next Steps

1. ✅ Deploy to testnet (Polygon Mumbai / Ethereum Sepolia)
2. ✅ Initialize registries with production addresses
3. ✅ Test 2-hop and 3-hop routes
4. ✅ Integrate with existing Node.js executor (`execution/bot.js`)
5. ✅ Monitor gas costs and optimize if needed
6. ✅ Add support for additional DEX protocols (Velodrome, Aerodrome, etc.)

## License

MIT
