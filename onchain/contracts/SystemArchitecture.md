# OmniArbExecutor System Architecture

## Overview

This document provides a comprehensive summary of the refactored smart contract system for flashloan-based arbitrage with multi-DEX routing support.

## System Components

### 1. OmniArbExecutor.sol (Refactored Core Executor)

**Role**: The single execution brain that can take a flashloan, run a multi-hop swap route across DEXs, and repay—all atomically.

**Key Features**:

#### Flashloan Source Support
- **Aave V3**: via `flashLoanSimple` + `executeOperation` callback
- **Balancer V3**: via `vault.unlock()` + `sendTo()` (creates debt) + `settle()` (repays debt)

#### Route Engine
- Runs a sequence of swaps hop-by-hop
- Each hop uses a protocol selector:
  - `1` = UniV2 (Quickswap/Sushi/etc.)
  - `2` = UniV3
  - `3` = Curve

#### Custom Registry Enum Logic

**Chain Enum** (based on `block.chainid`):
```solidity
enum Chain {
    ETHEREUM,     // 0 = chainId 1
    POLYGON,      // 1 = chainId 137
    ARBITRUM,     // 2 = chainId 42161
    OPTIMISM,     // 3 = chainId 10
    BASE,         // 4 = chainId 8453
    BSC,          // 5 = chainId 56
    AVALANCHE,    // 6 = chainId 43114
    FANTOM        // 7 = chainId 250
}
```

**DEX Enum**:
```solidity
enum Dex {
    QUICKSWAP,    // 0
    UNIV3,        // 1
    CURVE,        // 2
    SUSHISWAP,    // 3
    BALANCER,     // 4
    PANCAKESWAP,  // 5
    TRADER_JOE    // 6
}
```

**TokenId + TokenType Enums**:
```solidity
enum TokenId {
    USDC,         // 0
    USDT,         // 1
    DAI,          // 2
    WETH,         // 3
    WMATIC,       // 4
    WBTC,         // 5
    FRAX          // 6
}

enum TokenType {
    CANONICAL,    // 0: Native to the chain
    BRIDGED,      // 1: Bridged version (e.g., USDC.e)
    WRAPPED       // 2: Wrapped native (WETH, WMATIC, etc.)
}
```

#### Two Route Encodings

**RAW_ADDRESSES (0)**:
- Explicit router + tokenOut addresses provided
- Direct execution without registry lookup

**REGISTRY_ENUMS (1)**:
- Hops specify DEX ID + TokenId/TokenType
- Contract resolves addresses from on-chain mappings
- Requires registry setup via `setDexRouter()` and `setToken()`

**Why it matters**: Keeps execution flexible and fast while giving clean governance/control via registries (set once, route by enums).

#### Registry Mappings

```solidity
mapping(uint256 => mapping(uint8 => address)) public dexRouter;
mapping(uint256 => mapping(uint8 => mapping(uint8 => address))) public tokenRegistry;
```

- `dexRouter[chainId][dexId] = router address`
- `tokenRegistry[chainId][tokenId][tokenType] = token address`

---

### 2. SwapHandler.sol (System-Wide Swap Module)

**Role**: A reusable, centralized swap execution primitive used by the executor (and any future modules). This is the "don't rewrite swap logic everywhere" component.

**Protocol Support**:

#### UniV2-style routers (protocol 1)
- Covers Quickswap, SushiSwap, and most Polygon DEX forks
- Uses `swapExactTokensForTokens`
- extraData: empty (`0x`)

#### UniV3 routers (protocol 2)
- Uses `exactInputSingle` with fee from extraData
- extraData: `abi.encode(uint24 fee)`
- Common fees: 500 (0.05%), 3000 (0.3%), 10000 (1%)

#### Curve pools (protocol 3) ✅ Curve ON
- Uses `exchange(i, j, dx, minDy)` with `(int128 i, int128 j)` in extraData
- extraData: `abi.encode(int128 i, int128 j)`

#### Safety Upgrade
- **SafeERC20 approvals** with reset-to-zero logic to avoid USDT-style approval failures
- Uses `safeIncreaseAllowance` and `safeApprove(0)` pattern

---

### 3. Interfaces (Standardized, Single-Purpose)

We moved away from a "mega interface" (IDEX.sol) and replaced it with clean single-purpose interfaces for better compilation and maintenance.

#### IAaveV3.sol
- `IAavePoolV3.flashLoanSimple(...)`
- `IAaveFlashLoanSimpleReceiver.executeOperation(...)`

#### IB3.sol (Balancer V3)
- `IVaultV3.unlock(...)`
- `sendTo(...)` + `settle(...)` transient debt pattern (Balancer V3 flash-style flow)

#### IUniV3.sol
- `IUniswapV3Router.exactInputSingle(...)`
- (Optional) `exactInput(...)` multihop bytes-path support

#### IUniV2.sol
- `swapExactTokensForTokens(...)`

#### ICurve.sol ✅ Kept because Curve is ON
- Curve pool `exchange(...)` overloads

**Decision**: 
- ✅ Curve is ON → ICurve.sol stays, Curve branch stays in SwapHandler
- ✅ IDEX.sol is NOT needed → removed and import the dedicated interfaces directly
- ✅ Reuse system-wide components first → SwapHandler is the canonical swap primitive

---

## Route Execution Flow

### High-Level Flow

1. **Off-chain**: Detect arbitrage opportunity
2. **Off-chain**: Encode route using RAW_ADDRESSES or REGISTRY_ENUMS format
3. **On-chain**: Call `execute(flashSource, loanToken, loanAmount, routeData)`
4. **On-chain**: Flashloan provider calls back
5. **On-chain**: `_runRoute()` executes hop-by-hop swaps via SwapHandler
6. **On-chain**: Repay flashloan + fee
7. **On-chain**: Profit remains in contract (withdraw via `withdraw()`)

### Token Flow

Given:
- `loanToken` provided to `execute()`
- `loanAmount` provided
- Route with N hops

Then:
```
Hop 0: loanToken -> tokenOutPath[0]
Hop 1: tokenOutPath[0] -> tokenOutPath[1]
Hop i: tokenOutPath[i-1] -> tokenOutPath[i]
```

**Important**: The route token array represents `tokenOut` only, not the full path. The first hop's `tokenIn` is always the `loanToken`.

---

## Configuration

### Registry Setup (for REGISTRY_ENUMS)

Before using REGISTRY_ENUMS encoding, the owner must register DEX routers and tokens:

```solidity
// Register single DEX router
executor.setDexRouter(137, 0, QUICKSWAP_ROUTER);  // Polygon, QUICKSWAP

// Register single token
executor.setToken(137, 0, 0, USDC_ADDRESS);       // Polygon, USDC, CANONICAL

// Batch register multiple routers
executor.batchSetDexRouters(chainIds, dexIds, routers);

// Batch register multiple tokens
executor.batchSetTokens(chainIds, tokenIds, tokenTypes, tokens);
```

### Swap Deadline

```solidity
executor.setSwapDeadline(180);  // 3 minutes (default)
```

---

## Security Features

1. **Owner-only execution**: Only contract owner can trigger arbitrage
2. **Flashloan callback authentication**: Validates msg.sender is flashloan provider
3. **SafeERC20 usage**: Prevents approval/transfer failures
4. **Zero-amount checks**: Validates swap outputs are non-zero
5. **Length validation**: Ensures all route arrays match in length
6. **Address validation**: Checks for zero addresses in routers/tokens
7. **Route length limits**: Maximum 5 hops to prevent gas exhaustion

---

## Emergency Functions

```solidity
// Withdraw ERC20 tokens
executor.withdraw(tokenAddress);

// Withdraw native ETH/MATIC
executor.withdrawNative();
```

---

## File Structure

```
contracts/
├── OmniArbExecutor.sol          # Main executor contract
├── interfaces/
│   ├── IAaveV3.sol              # Aave V3 interfaces
│   ├── IB3.sol                  # Balancer V3 interfaces
│   ├── IUniV2.sol               # UniV2 router interface
│   ├── IUniV3.sol               # UniV3 router interface
│   └── ICurve.sol               # Curve pool interface
├── modules/
│   ├── SwapHandler.sol          # Reusable swap execution module
│   ├── AaveHandler.sol          # (Optional) Aave-specific logic
│   └── BalancerHandler.sol      # (Optional) Balancer-specific logic
├── RouteEncodingSpec.md         # Detailed encoding specification
└── SystemArchitecture.md        # This file
```

---

## Usage Examples

### Example 1: RAW_ADDRESSES Encoding

```javascript
const abi = ethers.AbiCoder.defaultAbiCoder();

const RAW = 0;
const protocols = [1, 2, 3];  // UniV2, UniV3, Curve

const routersOrPools = [
  QUICKSWAP_ROUTER,
  UNIV3_ROUTER,
  CURVE_POOL
];

const tokenOutPath = [
  WMATIC,
  USDC,
  USDT
];

const extra = [
  "0x",
  abi.encode(["uint24"], [3000]),
  abi.encode(["int128","int128"], [0,1])
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "address[]", "address[]", "bytes[]"],
  [RAW, protocols, routersOrPools, tokenOutPath, extra]
);

await executor.execute(1, USDT, amount, routeData);
```

### Example 2: REGISTRY_ENUMS Encoding

```javascript
const REG = 1;
const protocols = [1, 2, 3];
const dexIds = [0, 1, 2];          // QUICKSWAP, UNIV3, CURVE
const tokenOutIds = [4, 0, 1];     // WMATIC, USDC, USDT
const tokenOutTypes = [2, 0, 0];   // WRAPPED, CANONICAL, CANONICAL

const extra = [
  "0x",
  abi.encode(["uint24"], [3000]),
  abi.encode(["int128","int128"], [0,1])
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "uint8[]", "uint8[]", "uint8[]", "bytes[]"],
  [REG, protocols, dexIds, tokenOutIds, tokenOutTypes, extra]
);

await executor.execute(1, USDT, amount, routeData);
```

---

## Testing

Run route encoding tests:
```bash
npx hardhat test tests/test_route_encoding.js
```

Compile contracts:
```bash
npx hardhat compile
```

---

## Future Enhancements

1. Support for additional DEX protocols (Balancer pools, Velodrome, etc.)
2. Multi-asset flashloans (beyond single-asset)
3. Dynamic slippage calculation on-chain
4. Circuit breaker for emergency pause
5. Profit distribution mechanisms
6. Gas optimization passes

---

## Summary

The refactored system provides:

✅ **Modular design**: Reusable SwapHandler, clean interfaces
✅ **Flexible routing**: RAW_ADDRESSES for speed, REGISTRY_ENUMS for governance
✅ **Multi-protocol support**: UniV2, UniV3, Curve (with room for expansion)
✅ **Dual flashloan sources**: Aave V3 and Balancer V3
✅ **Safety first**: SafeERC20, validation checks, owner-only execution
✅ **Well-documented**: Comprehensive specs for off-chain integration

This architecture keeps execution flexible and fast while giving clean governance/control via registries and standardized interfaces.
