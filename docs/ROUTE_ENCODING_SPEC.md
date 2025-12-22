# Route Encoding Specification

## Overview

This document describes the ABI encoding specification for route data used in the Titan arbitrage execution system. Route data is encoded using Ethereum's ABI encoding standard to pass execution parameters to smart contracts efficiently.

## Encoding Format

Routes are encoded using the `ethers.AbiCoder.defaultAbiCoder().encode()` method with the following structure:

```javascript
routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extras]
);
```

### Parameters

#### 1. `protocols` (uint8[])
An array of protocol identifiers indicating which DEX/protocol to use for each hop in the route.

**Protocol IDs:**
- `0`: Uniswap V2
- `1`: Uniswap V3
- `2`: Curve
- `3`: Balancer
- `4`: External Aggregator (1inch, 0x, etc.)
- Additional protocols can be added as needed

#### 2. `routers` (address[])
An array of router contract addresses corresponding to each protocol in the route.

**Requirements:**
- Must be the same length as the `protocols` array
- Each address must be a valid Ethereum address (not zero address)
- Addresses must be checksummed

**Example Routers:**
- Uniswap V2: `0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D`
- Uniswap V3: `0xE592427A0AEce92De3Edee1F18E0157C05861564`
- Curve: Varies by pool
- Aggregators: Varies by service

#### 3. `path` (address[])
An array of token addresses representing the swap path through the route.

**Requirements:**
- Must include all intermediate tokens
- First token is the input token
- Last token is the output token
- For multi-hop routes, includes all intermediate tokens

**Example:**
```javascript
// Single hop: USDC -> WETH
path = [
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
]

// Multi-hop: USDC -> DAI -> WETH
path = [
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
    "0x6B175474E89094C44Da98b954EedeAC495271d0F", // DAI
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
]
```

#### 4. `extras` (bytes[])
An array of additional encoded data for each hop, such as pool IDs, fees, or aggregator-specific calldata.

**Requirements:**
- Must be the same length as the `protocols` array
- Can be empty bytes (`0x`) if no additional data needed
- For Uniswap V3: encodes the fee tier
- For Curve: encodes pool-specific parameters
- For External Aggregators: encodes the full swap calldata

## Usage Examples

### Example 1: Standard Uniswap V2 Route

```javascript
const { ethers } = require('ethers');

// Single hop USDC -> WETH on Uniswap V2
const protocols = [0]; // Uniswap V2
const routers = ["0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"];
const path = [
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
];
const extras = ["0x"]; // No extra data needed

const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extras]
);
```

### Example 2: Uniswap V3 Route with Fee Tier

```javascript
// USDC -> WETH on Uniswap V3 with 0.3% fee tier
const protocols = [1]; // Uniswap V3
const routers = ["0xE592427A0AEce92De3Edee1F18E0157C05861564"];
const path = [
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
];
// Encode fee tier (3000 = 0.3%)
const feeData = ethers.AbiCoder.defaultAbiCoder().encode(["uint24"], [3000]);
const extras = [feeData];

const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extras]
);
```

### Example 3: External Aggregator (1inch, 0x, etc.)

```javascript
// Using an external aggregator for the swap
const protocols = [4]; // External Aggregator
const routers = [aggregatorAddress]; // Address from aggregator API
const path = [tokenIn]; // Only input token needed for aggregators
const extras = [swapCalldata]; // Full calldata from aggregator

const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extras]
);
```

### Example 4: Multi-Hop Route

```javascript
// USDC -> DAI (Curve) -> WETH (Uniswap V3)
const protocols = [2, 1]; // Curve, then Uniswap V3
const routers = [
    "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7", // Curve 3pool
    "0xE592427A0AEce92De3Edee1F18E0157C05861564"  // Uniswap V3 Router
];
const path = [
    "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
    "0x6B175474E89094C44Da98b954EedeAC495271d0F", // DAI
    "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
];
const curvePoolData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["int128", "int128"], 
    [1, 0] // USDC to DAI in 3pool
);
const uniV3FeeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint24"], 
    [3000] // 0.3% fee
);
const extras = [curvePoolData, uniV3FeeData];

const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    [protocols, routers, path, extras]
);
```

## Validation Rules

When constructing route data, the following validation must be performed:

1. **Array Length Consistency:**
   - `protocols.length === routers.length === extras.length`
   - `path.length >= 2` (at least input and output token)
   - `path.length === protocols.length + 1` (for simple routes)

2. **Address Validation:**
   - All addresses in `routers` and `path` must be valid Ethereum addresses
   - No zero addresses (`0x0000000000000000000000000000000000000000`)
   - Addresses should be checksummed

3. **Protocol ID Validation:**
   - Protocol IDs must be valid and supported by the executor contract
   - Unknown protocol IDs will cause transaction reversion

4. **Data Consistency:**
   - For external aggregators (protocol 4), only the input token is required in `path`
   - `extras` data must match the expected format for each protocol

## Decoding

To decode route data:

```javascript
const decoded = ethers.AbiCoder.defaultAbiCoder().decode(
    ["uint8[]", "address[]", "address[]", "bytes[]"],
    routeData
);

const [protocols, routers, path, extras] = decoded;
```

## Gas Optimization

- Minimize the number of hops in a route to reduce gas costs
- Use single-hop routes when possible
- Prefer aggregators for complex routes as they handle optimization internally
- Empty `extras` arrays use less gas than populated ones

## Security Considerations

1. **Router Validation:** Always validate router addresses against a whitelist
2. **Slippage Protection:** Routes should be executed with appropriate slippage limits
3. **Deadline Enforcement:** Transactions should include deadline parameters
4. **Reentrancy Guards:** Executor contracts must implement reentrancy protection
5. **Input Validation:** Validate all encoded parameters before execution

## Version History

- **v1.0** (Current): Initial specification with support for Uniswap V2/V3, Curve, and external aggregators
