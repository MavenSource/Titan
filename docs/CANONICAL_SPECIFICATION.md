# Titan Canonical Specification

This document consolidates the **canonical refactored specification** for the OmniArbExecutor and SwapHandler system, including exact enum orderings, routeData encoding formats, and interface standards.

---

## Table of Contents

1. [Contract Modules Overview](#contract-modules-overview)
2. [Standardized Interfaces](#standardized-interfaces)
3. [Enum Ordering Tables](#enum-ordering-tables)
4. [RouteData Encoding Specification](#routedata-encoding-specification)
5. [Per-Protocol Extra Data Formats](#per-protocol-extra-data-formats)
6. [Operational Guardrails](#operational-guardrails)
7. [Off-Chain ABI Type Constants](#off-chain-abi-type-constants)

---

## Contract Modules Overview

### OmniArbExecutor.sol (Refactored Core)

**Role:** Atomic flashloan arbitrage executor. Takes a flashloan (Aave or Balancer), runs an N-hop route, repays, keeps profit.

**Flash sources supported:**
- **Aave V3**: `flashLoanSimple()` → callback `executeOperation()`
- **Balancer V3**: `vault.unlock()` → callback `onBalancerUnlock()` using transient debt `sendTo()` + `settle()`

**Swap execution:**
- Delegates each hop swap into **system-wide SwapHandler** `_executeSwap()`

**Registry mode:**
- Supports **route encoding that references enums**, resolving router/token addresses on-chain via mappings.

---

### SwapHandler.sol (System-Wide Swap Primitive)

**Role:** Central swap executor used by the executor and future modules. Avoids duplicated DEX logic.

**Protocol IDs (refactored standard):**
- `1 = UniV2` (Quickswap/Sushiswap/etc.)
- `2 = UniV3` (SwapRouter exactInputSingle)
- `3 = Curve` (pool exchange)

**Safety:** Uses `SafeERC20.forceApprove` pattern (compatible with OpenZeppelin v5) with reset-to-zero when needed.

---

## Standardized Interfaces

### IAaveV3.sol
- `IAavePoolV3.flashLoanSimple(...)`
- `IAaveFlashLoanSimpleReceiver.executeOperation(...)`

### IB3.sol (Balancer V3)
- `IVaultV3.unlock(bytes)`
- `sendTo(token, to, amount)` (creates debt)
- `settle(token, amount)` (repays debt)

### IUniV3.sol
- `exactInputSingle(params)`
- Optional: `exactInput(path)`

### IUniV2.sol
- `swapExactTokensForTokens(...)`

### ICurve.sol
- `exchange(int128, int128, uint256, uint256)`
- Optional overload: `exchange(uint256, uint256, uint256, uint256)`

---

## Enum Ordering Tables

> **CRITICAL:** Solidity assigns enum values by declaration order starting at 0.
> **Never reorder**; only append new members.

### FlashSource

```solidity
enum FlashSource { AaveV3, BalancerV3 }
```

| Name | Value | Description |
|------|-------|-------------|
| AaveV3 | 0 | Aave V3 flashLoanSimple |
| BalancerV3 | 1 | Balancer V3 unlock pattern |

---

### RouteEncoding

```solidity
enum RouteEncoding { RAW_ADDRESSES, REGISTRY_ENUMS }
```

| Name | Value | Description |
|------|-------|-------------|
| RAW_ADDRESSES | 0 | Explicit router + token addresses |
| REGISTRY_ENUMS | 1 | DEX + Token enums resolved on-chain |

---

### Dex

```solidity
enum Dex { UniV2, UniV3, Curve, Balancer, Dodo, Unknown }
```

| Name | Value | Description |
|------|-------|-------------|
| UniV2 | 0 | UniswapV2-style (Quickswap, Sushiswap, etc.) |
| UniV3 | 1 | Uniswap V3 |
| Curve | 2 | Curve pools |
| Balancer | 3 | Balancer |
| Dodo | 4 | Dodo |
| Unknown | 5 | Unknown/Other DEX |

---

### TokenId

```solidity
enum TokenId { WNATIVE, USDC, USDT, DAI, WETH, WBTC }
```

| Name | Value | Description |
|------|-------|-------------|
| WNATIVE | 0 | Wrapped native token (WETH, WMATIC, etc.) |
| USDC | 1 | USD Coin |
| USDT | 2 | Tether USD |
| DAI | 3 | Dai Stablecoin |
| WETH | 4 | Wrapped Ether |
| WBTC | 5 | Wrapped Bitcoin |

---

### TokenType

```solidity
enum TokenType { CANONICAL, BRIDGED, WRAPPED }
```

| Name | Value | Description |
|------|-------|-------------|
| CANONICAL | 0 | Native to the chain |
| BRIDGED | 1 | Bridged version (e.g., USDC.e) |
| WRAPPED | 2 | Wrapped native (WETH, WMATIC, etc.) |

---

## RouteData Encoding Specification

### Golden Rule

- Must be encoded with `abi.encode(...)` (standard ABI)
- Never use `abi.encodePacked(...)`
- Arrays must be same length for all per-hop vectors.

---

### RAW_ADDRESSES routeData (explicit routers + tokenOut)

**Solidity decode shape:**

```solidity
(RouteEncoding enc,
 uint8[] protocols,
 address[] routersOrPools,
 address[] tokenOutPath,
 bytes[] extra)
= abi.decode(routeData, (RouteEncoding, uint8[], address[], address[], bytes[]));
```

**Off-chain ABI types:**
```text
(uint8, uint8[], address[], address[], bytes[])
```

**Per-hop meaning:**
- `protocols[i]`: swap protocol id (1/2/3)
- `routersOrPools[i]`: router/pool address for hop i
  - UniV2: router address
  - UniV3: SwapRouter address
  - Curve: **pool address**
- `tokenOutPath[i]`: tokenOut for hop i
- `extra[i]`: protocol-specific bytes

**Token flow:**
- hop0 tokenIn = loan token
- hop i tokenIn = previous hop tokenOut

**Length constraint:**
```text
protocols.length == routersOrPools.length == tokenOutPath.length == extra.length
```

---

### REGISTRY_ENUMS routeData (resolve dex + token on-chain)

**Solidity decode shape:**

```solidity
(RouteEncoding enc,
 uint8[] protocols,
 uint8[] dexIds,
 uint8[] tokenOutIds,
 uint8[] tokenOutTypes,
 bytes[] extra)
= abi.decode(routeData, (RouteEncoding, uint8[], uint8[], uint8[], uint8[], bytes[]));
```

**Off-chain ABI types:**
```text
(uint8, uint8[], uint8[], uint8[], uint8[], bytes[])
```

**Per-hop meaning:**
- `protocols[i]`: swap protocol id (1/2/3)
- `dexIds[i]`: `uint8(Dex.<NAME>)` resolved to router via `dexRouter[chainId][dexId]`
- `tokenOutIds[i]`: `uint8(TokenId.<NAME>)` resolved via `tokenRegistry[chainId][tokenId][tokenType]`
- `tokenOutTypes[i]`: `uint8(TokenType.<NAME>)` canonical/bridged/wrapped
- `extra[i]`: protocol-specific bytes

**Length constraint:**
```text
protocols.length == dexIds.length == tokenOutIds.length == tokenOutTypes.length == extra.length
```

---

## Per-Protocol Extra Data Formats

### UniV2 (protocol = 1)
```
extra[i] = 0x (empty)
```

### UniV3 (protocol = 2)
```
extra[i] = abi.encode(uint24 fee)
```
Examples: 500, 3000, 10000

### Curve (protocol = 3)
```
extra[i] = abi.encode(int128 i, int128 j)
```
Indexes into the pool's coin array

---

## Operational Guardrails

1. **Never reorder enums.** Append-only to maintain backward compatibility.
2. **Always encode with abi.encode.** Never use `abi.encodePacked`.
3. **Always keep arrays aligned.** All array parameters must have the same length.
4. **Curve hop uses pool address as routerOrPool.** Not a router address.
5. **UniV3 hop requires fee bytes.** Must be encoded in `extra[i]`.
6. **Use forceApprove for OpenZeppelin v5.** `safeApprove` is deprecated.

---

## Off-Chain ABI Type Constants

### RAW_ADDRESSES ABI
```text
(uint8, uint8[], address[], address[], bytes[])
```

### REGISTRY_ENUMS ABI
```text
(uint8, uint8[], uint8[], uint8[], uint8[], bytes[])
```

---

## Integration Notes

### For Bot/Off-Chain Integration:

1. Use the enum ordering tables above to map names → numeric IDs
2. Use the ABI types to ensure routeData matches on-chain `abi.decode`
3. Use the per-protocol extra data formats to build the exact `extra[i]` bytes per hop
4. When calling `execute()`, use `FlashSource` enum value (0 or 1)

### Example Usage:

```javascript
// RAW_ADDRESSES example
const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
  ['uint8', 'uint8[]', 'address[]', 'address[]', 'bytes[]'],
  [
    0, // RAW_ADDRESSES
    [1, 2], // protocols: UniV2, UniV3
    [uniV2Router, uniV3Router], // routers
    [tokenB, tokenC], // tokenOut path
    ['0x', ethers.AbiCoder.defaultAbiCoder().encode(['uint24'], [3000])] // extra
  ]
);

// Execute with Aave V3 flashloan
await executor.execute(
  0, // FlashSource.AaveV3
  tokenA,
  loanAmount,
  routeData
);
```

---

**Last Updated:** 2025-12-22
**Version:** 1.0.0
