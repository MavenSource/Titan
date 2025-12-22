# RouteData Encoding Specification

## Overview

This document provides the exact, ABI-accurate specification for `routeData` encoding used by the refactored `OmniArbExecutor`.

**CRITICAL**: `routeData` MUST be encoded with `abi.encode(...)` (standard ABI), NOT `abi.encodePacked(...)`. The contract uses `abi.decode(routeData, (...))`, so the layout must match standard ABI encoding.

## Core Concept

A route is executed **hop-by-hop**:

1. **Hop 0** `tokenIn` is implicitly the `loanToken` (passed to `execute()` and received in flash callback)
2. Each **hop i** swaps: `currentToken -> tokenOut[i]`, producing `currentAmount` used as input to next hop
3. Each hop needs:
   - Protocol ID (1/2/3)
   - Router/pool reference (direct address OR resolved from registry enum)
   - Token output address
   - Protocol-specific `extraData`

## RouteEncoding Enum

```solidity
enum RouteEncoding { 
    RAW_ADDRESSES,    // 0
    REGISTRY_ENUMS    // 1
}
```

The first word of `routeData` is always the encoding type (uint8).

---

## Encoding Format 1: RAW_ADDRESSES

**Description**: Explicit routers + explicit tokenOut addresses

### Solidity Decode Shape

```solidity
(
    RouteEncoding enc,
    uint8[] memory protocols,
    address[] memory routersOrPools,
    address[] memory tokenOutPath,
    bytes[] memory extra
) = abi.decode(routeData, (RouteEncoding, uint8[], address[], address[], bytes[]));
```

### Exact ABI Types (off-chain)

```
(uint8, uint8[], address[], address[], bytes[])
```

### Field Meanings

- **`protocols[i]`**:
  - `1` = UniV2 (Quickswap, Sushi, etc.)
  - `2` = UniV3
  - `3` = Curve

- **`routersOrPools[i]`**:
  - UniV2: router address (e.g., Quickswap Router)
  - UniV3: SwapRouter address
  - Curve: pool address (NOT a router)

- **`tokenOutPath[i]`**: Output token for hop `i`

- **`extra[i]`**:
  - UniV2: typically `0x` (empty bytes)
  - UniV3: `abi.encode(uint24 fee)`
  - Curve: `abi.encode(int128 i, int128 j)` (64 bytes)

### Length Rule

**MANDATORY**: All arrays must have the same length `N`:

```
protocols.length == routersOrPools.length == tokenOutPath.length == extra.length
```

### Ethers.js Example (3 hops)

Route:
1. UniV2 Quickswap: USDC -> WETH
2. UniV3: WETH -> USDT with fee 3000
3. Curve pool: USDT -> USDC indices (0,1)

```javascript
import { ethers } from "ethers";

const abi = ethers.AbiCoder.defaultAbiCoder();

// RouteEncoding
const RAW = 0;

// per-hop arrays (same length!)
const protocols = [1, 2, 3];

const routersOrPools = [
  QUICKSWAP_ROUTER,       // UniV2 router
  UNIV3_SWAPROUTER,       // UniV3 router
  CURVE_POOL_ADDRESS      // Curve pool (acts like routerOrPool)
];

const tokenOutPath = [
  WETH,
  USDT,
  USDC
];

const extra = [
  "0x",                                   // UniV2
  abi.encode(["uint24"], [3000]),         // UniV3 fee
  abi.encode(["int128","int128"], [0,1])  // Curve indices
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "address[]", "address[]", "bytes[]"],
  [RAW, protocols, routersOrPools, tokenOutPath, extra]
);
```

---

## Encoding Format 2: REGISTRY_ENUMS

**Description**: DEX + Token enums resolved on-chain

This encoding avoids raw addresses in calldata. The contract resolves:

```solidity
router = dexRouter[chainId][dexId]
tokenOut = tokenRegistry[chainId][tokenId][tokenType]
```

### Solidity Decode Shape

```solidity
(
    RouteEncoding enc,
    uint8[] memory protocols,
    uint8[] memory dexIds,
    uint8[] memory tokenOutIds,
    uint8[] memory tokenOutTypes,
    bytes[] memory extra
) = abi.decode(routeData, (RouteEncoding, uint8[], uint8[], uint8[], uint8[], bytes[]));
```

### Exact ABI Types (off-chain)

```
(uint8, uint8[], uint8[], uint8[], uint8[], bytes[])
```

### Field Meanings

- **`protocols[i]`**: Same protocol IDs as RAW_ADDRESSES

- **`dexIds[i]`**: `uint8(Dex.<NAME>)`
  - Example: `Dex.UniV2 = 0`, `Dex.UniV3 = 1`, `Dex.Curve = 2`

- **`tokenOutIds[i]`**: `uint8(TokenId.<NAME>)`
  - Example: `TokenId.WNATIVE = 0`, `TokenId.USDC = 1`, `TokenId.USDT = 2`, `TokenId.WETH = 4`

- **`tokenOutTypes[i]`**: `uint8(TokenType.<NAME>)`
  - `0` = `CANONICAL` (native on that chain)
  - `1` = `BRIDGED` (e.g., USDC.e, bridged USDT)
  - `2` = `WRAPPED` (WMATIC, WETH, etc.)

- **`extra[i]`**: Same as RAW_ADDRESSES

### Length Rule

**MANDATORY**: All arrays must have the same length `N`:

```
protocols.length == dexIds.length == tokenOutIds.length == tokenOutTypes.length == extra.length
```

### Ethers.js Example (same route but enum-resolved)

Assume enums (from canonical specification):
- `Dex.UniV2 = 0`, `Dex.UniV3 = 1`, `Dex.Curve = 2`
- `TokenId.WNATIVE = 0`, `TokenId.USDC = 1`, `TokenId.USDT = 2`, `TokenId.WETH = 4`
- `TokenType.CANONICAL = 0`

```javascript
const REG = 1;

const protocols = [1, 2, 3];
const dexIds = [0, 1, 2];          // UniV2, UniV3, Curve
const tokenOutIds = [4, 2, 1];     // WETH, USDT, USDC
const tokenOutTypes = [0, 0, 0];   // CANONICAL for all

const extra = [
  "0x",
  abi.encode(["uint24"], [3000]),
  abi.encode(["int128","int128"], [0,1])
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "uint8[]", "uint8[]", "uint8[]", "bytes[]"],
  [REG, protocols, dexIds, tokenOutIds, tokenOutTypes, extra]
);
```

---

## Protocol-Specific `extra[i]` Formats

### UniV2 (protocol = 1)

**extraData**: Empty bytes

```javascript
extra[i] = "0x"
```

SwapHandler ignores extraData for UniV2.

### UniV3 (protocol = 2)

**extraData**: `abi.encode(uint24 fee)`

Must be exactly 32 bytes when decoded as uint24.

**Common fees**:
- `500` (0.05%)
- `3000` (0.3%)
- `10000` (1%)

```javascript
extra[i] = abi.encode(["uint24"], [3000])
```

### Curve (protocol = 3) — Curve ON

**extraData**: `abi.encode(int128 i, int128 j)`

Must be exactly 64 bytes.

Assumes pool uses `exchange(int128,int128,uint256,uint256)` signature (common for many Curve pools).

```javascript
extra[i] = abi.encode(["int128","int128"], [0,1])
```

**Note**: If you need Curve pools with `uint256` indices, extend the encoding.

---

## Token Flow Interpretation

Given:
- `loanToken` provided to `execute()`
- `loanAmount` provided

Then route executes:

```
Hop 0: loanToken -> tokenOutPath[0]
Hop 1: tokenOutPath[0] -> tokenOutPath[1]
Hop i: tokenOutPath[i-1] -> tokenOutPath[i]
```

**Important**: The route token array represents `tokenOut` only, not the full path.

---

## Critical Sanity Checks

1. **Array lengths MUST match** or executor reverts with "len mismatch"

2. **UniV3** `extra[i]` must decode as `uint24`
   - If you pass empty bytes `0x`, it will revert

3. **Curve** `extra[i]` must be exactly `(int128, int128)`
   - If you pass `uint256` indices but contract expects `int128`, it will revert

4. **For RAW_ADDRESSES**:
   - Curve hop `routerOrPool` MUST be the pool address, not a router

5. **Don't use `encodePacked`** — it will break decoding

---

## Example Complete Flow

### 1. Off-chain: Encode Route

```javascript
// Example: 3-hop arbitrage on Polygon
const RAW = 0;
const protocols = [1, 2, 3];  // UniV2 -> UniV3 -> Curve

const routersOrPools = [
  "0x...",  // Quickswap router
  "0x...",  // UniV3 router
  "0x..."   // Curve pool
];

const tokenOutPath = [
  WMATIC_ADDRESS,
  USDC_ADDRESS,
  USDT_ADDRESS
];

const extra = [
  "0x",
  abi.encode(["uint24"], [500]),
  abi.encode(["int128","int128"], [1,2])
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "address[]", "address[]", "bytes[]"],
  [RAW, protocols, routersOrPools, tokenOutPath, extra]
);
```

### 2. On-chain: Execute

```javascript
await executor.execute(
  0,              // flashSource (0=AaveV3, 1=BalancerV3)
  USDT_ADDRESS,   // loanToken
  ethers.parseUnits("10000", 6),  // loanAmount (10k USDT)
  routeData
);
```

### 3. On-chain: Route Execution

```
Flash borrow 10,000 USDT
  Hop 0: USDT -> WMATIC via Quickswap (UniV2)
  Hop 1: WMATIC -> USDC via UniV3 (fee 500)
  Hop 2: USDC -> USDT via Curve (indices 1->2)
Repay 10,000 USDT + fee
Profit = final USDT - (10,000 + fee)
```

---

## Registry Setup (REGISTRY_ENUMS only)

Before using REGISTRY_ENUMS, owner must register protocol entry contracts (routers or pools) and tokens:

```solidity
// Register DEX routers / pools (protocol entry contracts)
executor.setDexRouter(137, 0, QUICKSWAP_ROUTER);  // Polygon, UniV2 router (Quickswap example)
executor.setDexRouter(137, 1, UNIV3_ROUTER);      // Polygon, UniV3 router
executor.setDexRouter(137, 2, CURVE_POOL);        // Polygon, Curve pool (stored in dexRouter slot by design)

// Register tokens
executor.setToken(137, 1, 0, USDC_ADDRESS);       // TokenId.USDC = 1, CANONICAL
executor.setToken(137, 2, 0, USDT_ADDRESS);       // TokenId.USDT = 2, CANONICAL
executor.setToken(137, 0, 2, WMATIC_ADDRESS);     // TokenId.WNATIVE = 0, WRAPPED
```

Batch operations also available:

```solidity
executor.batchSetDexRouters(chainIds, dexIds, routers);
executor.batchSetTokens(chainIds, tokenIds, tokenTypes, tokens);
```

---

## Summary

- **Two encoding formats**: RAW_ADDRESSES (explicit) and REGISTRY_ENUMS (resolved)
- **Three protocols**: UniV2 (1), UniV3 (2), Curve (3)
- **Standard ABI encoding** required, not encodePacked
- **Array lengths must match** across all fields
- **Protocol-specific extraData** format must be exact
- **Registry must be populated** before using REGISTRY_ENUMS

This specification ensures off-chain route encoding matches on-chain decoding exactly every time.
