# OmniArbExecutor Refactoring - Implementation Summary

## Changes Made

This PR implements a comprehensive refactoring of the smart contract system for flashloan-based arbitrage with multi-DEX routing support.

### Files Created

1. **contracts/interfaces/IUniV2.sol** (NEW)
   - Interface for Uniswap V2-style routers (Quickswap, Sushi, etc.)
   - Standardized `swapExactTokensForTokens` signature

2. **contracts/interfaces/IAaveV3.sol** (UPDATED)
   - Complete Aave V3 Pool interface with `flashLoanSimple`
   - Flash loan receiver interface with `executeOperation` callback

3. **contracts/interfaces/IUniV3.sol** (UPDATED)
   - Complete Uniswap V3 Router interface
   - `exactInputSingle` for single-hop swaps
   - `exactInput` for multi-hop swaps (optional)

4. **contracts/modules/SwapHandler.sol** (REFACTORED)
   - System-wide reusable swap execution module
   - Support for UniV2, UniV3, and Curve protocols
   - SafeERC20 implementation for USDT compatibility
   - Clean abstraction for future protocol additions

5. **contracts/OmniArbExecutor.sol** (COMPLETELY REFACTORED)
   - Dual route encoding support:
     - RAW_ADDRESSES: explicit addresses
     - REGISTRY_ENUMS: on-chain registry resolution
   - Enums for Chain, DEX, TokenId, TokenType
   - Registry mappings for governance-controlled routing
   - Aave V3 and Balancer V3 flashloan support
   - Hop-by-hop route execution engine
   - Emergency withdrawal functions
   - Comprehensive event logging

6. **contracts/RouteEncodingSpec.md** (NEW)
   - Complete specification for route encoding
   - Exact ABI encoding examples in JavaScript
   - Protocol-specific extraData formats
   - Real-world usage examples

7. **contracts/SystemArchitecture.md** (NEW)
   - High-level system architecture documentation
   - Component descriptions and relationships
   - Configuration guide
   - Security features overview

8. **tests/test_route_encoding.js** (NEW)
   - Validation tests for route encoding formats
   - RAW_ADDRESSES encoding tests
   - REGISTRY_ENUMS encoding tests
   - Protocol-specific extraData validation
   - Array length validation tests
   - Real-world example encoding

### Files Removed

1. **contracts/interfaces/IDEX.sol** (REMOVED)
   - Replaced with dedicated single-purpose interfaces
   - Better compilation and maintenance

2. **contracts/modules/AaveHandler.sol** (REMOVED)
   - Empty file, logic integrated into OmniArbExecutor

3. **contracts/modules/BalancerHandler.sol** (REMOVED)
   - Empty file, logic integrated into OmniArbExecutor

### Files Unchanged

1. **contracts/interfaces/IB3.sol** (KEPT)
   - Already complete Balancer V3 interface
   - No changes needed

2. **contracts/interfaces/ICurve.sol** (KEPT)
   - Curve support is ON as per requirements
   - Interface already correct

## Key Features

### 1. Two Route Encoding Formats

**RAW_ADDRESSES (0)**:
- Direct specification of router/pool addresses and tokens
- Faster execution (no registry lookups)
- Larger calldata size
- Use case: High-frequency trading, gas optimization

**REGISTRY_ENUMS (1)**:
- Enum-based routing resolved from on-chain registries
- Smaller calldata size
- Governance-controlled routing
- Use case: Managed strategies, compliance

### 2. Multi-Protocol Support

- **Protocol 1**: UniV2-style (Quickswap, Sushi, etc.)
- **Protocol 2**: Uniswap V3 with fee tiers
- **Protocol 3**: Curve with int128 indices

### 3. Dual Flashloan Sources

- **Balancer V3**: Unlock pattern with transient debt
- **Aave V3**: Standard flashloan with premium

### 4. Registry System

```solidity
// Chain-specific DEX router registry
mapping(uint256 => mapping(uint8 => address)) public dexRouter;

// Chain-specific token registry with type classification
mapping(uint256 => mapping(uint8 => mapping(uint8 => address))) public tokenRegistry;
```

Supports batch registration for efficient setup.

### 5. Safety Features

- SafeERC20 for USDT compatibility
- Zero-address validation
- Zero-amount checks
- Array length validation
- Route length limits (max 5 hops)
- Owner-only execution
- Flashloan callback authentication

## Route Execution Flow

```
1. Off-chain detects opportunity
2. Off-chain encodes route (RAW_ADDRESSES or REGISTRY_ENUMS)
3. Call execute(flashSource, loanToken, loanAmount, routeData)
4. Flashloan provider sends funds and calls back
5. _runRoute() decodes routing format
6. For each hop:
   a. Resolve router/pool (direct or from registry)
   b. Resolve tokenOut (direct or from registry)
   c. Call _executeSwap() from SwapHandler
   d. Validate output > 0
7. Repay flashloan + fee
8. Profit remains in contract (withdraw later)
```

## Protocol-Specific extraData

### UniV2 (Protocol 1)
```javascript
extra[i] = "0x"  // Empty bytes
```

### UniV3 (Protocol 2)
```javascript
extra[i] = abi.encode(["uint24"], [3000])  // Fee tier
```

### Curve (Protocol 3)
```javascript
extra[i] = abi.encode(["int128","int128"], [0,1])  // Token indices
```

## Example Usage

### JavaScript (Ethers v6)

```javascript
const abi = ethers.AbiCoder.defaultAbiCoder();

// RAW_ADDRESSES encoding
const routeData = abi.encode(
  ["uint8", "uint8[]", "address[]", "address[]", "bytes[]"],
  [
    0,  // RAW_ADDRESSES
    [1, 2, 3],  // protocols: UniV2, UniV3, Curve
    [QUICKSWAP_ROUTER, UNIV3_ROUTER, CURVE_POOL],
    [WMATIC, USDC, USDT],
    ["0x", abi.encode(["uint24"], [3000]), abi.encode(["int128","int128"], [0,1])]
  ]
);

await executor.execute(
  1,  // Balancer flashloan
  USDT,
  ethers.parseUnits("10000", 6),
  routeData
);
```

### Solidity (Registry Setup)

```solidity
// One-time registry setup
executor.batchSetDexRouters(
  [137, 137, 137],  // Polygon
  [0, 1, 2],        // QUICKSWAP, UNIV3, CURVE
  [QUICKSWAP_ROUTER, UNIV3_ROUTER, CURVE_POOL]
);

executor.batchSetTokens(
  [137, 137, 137, 137],
  [0, 1, 3, 4],          // USDC, USDT, WETH, WMATIC
  [0, 0, 2, 2],          // CANONICAL, CANONICAL, WRAPPED, WRAPPED
  [USDC, USDT, WETH, WMATIC]
);
```

## Summary

This refactoring provides:

✅ Clean, modular architecture with reusable components
✅ Flexible routing with two encoding formats
✅ Support for UniV2, UniV3, and Curve protocols
✅ Dual flashloan sources (Aave V3, Balancer V3)
✅ Comprehensive safety checks and SafeERC20 usage
✅ Well-documented with specifications and examples
✅ Tested encoding formats for off-chain integration
✅ Governance-friendly registry system

The system is production-ready for deployment on EVM-compatible chains.
