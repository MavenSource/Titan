# Token Registry Setup Scripts

This directory contains scripts for configuring the OmniArbExecutor token registry system.

## Overview

The OmniArbExecutor uses a **flexible uint8 token registry** (0-255 IDs) instead of hardcoded enums. This allows the system to support 300+ tokens without bloating the Solidity contract.

### Architecture

- **On-Chain**: Tight whitelist registry (20-50 high-liquidity tokens per chain)
- **Off-Chain**: 300+ token graph in Python brain for path discovery
- **Calldata**: Adaptive encoding (RAW_ADDRESSES for rare tokens, REGISTRY_ENUMS for registered tokens)

## Scripts

### setupTokenRegistry.js

Configures the OmniArbExecutor token registry with recommended token IDs.

**Token ID Conventions**:
- `0-10`: Universal tokens (WNATIVE, USDC, USDT, DAI, WBTC, WETH)
- `11-50`: Chain-specific top tokens (UNI, LINK, QUICK, ARB, OP, etc.)
- `51-100`: DeFi protocol tokens (available for expansion)
- `101-200`: Bridge tokens (available for expansion)
- `201-255`: Reserved/Custom

**Usage**:
```bash
# Set executor address
export EXECUTOR_ADDRESS=0x...

# Run on target network
npx hardhat run scripts/setupTokenRegistry.js --network polygon
npx hardhat run scripts/setupTokenRegistry.js --network arbitrum
npx hardhat run scripts/setupTokenRegistry.js --network optimism
npx hardhat run scripts/setupTokenRegistry.js --network base
```

**Supported Chains**:
- Ethereum (Chain ID 1)
- Polygon (Chain ID 137)
- Arbitrum (Chain ID 42161)
- Optimism (Chain ID 10)
- Base (Chain ID 8453)

### configureTokenRanks.js

Configures token rankings for OmniArbDecoder (separate contract using rank-based system).

## Token Registry Design

### Benefits of Flexible uint8 IDs

✅ **No Contract Bloat**: Registry mappings instead of 300-value enums
✅ **Upgradeable**: Add tokens via `setToken()` without redeployment
✅ **Gas Efficient**: Compact calldata with REGISTRY_ENUMS encoding
✅ **Maximum Coverage**: Use RAW_ADDRESSES for any token immediately

### Example: Adding a New Token

```javascript
// On-chain: Register high-liquidity token with ID
await executor.setToken(
  137,    // chainId (Polygon)
  25,     // tokenId (choose available ID in range)
  0,      // tokenType (CANONICAL)
  "0x..." // token address
);

// Off-chain: Brain automatically detects and uses in routes
// Brain will use REGISTRY_ENUMS encoding for ID 25
```

### Example: Using Rare Token

```javascript
// No registration needed!
// Brain uses RAW_ADDRESSES encoding with explicit address
const routeData = encodeRawAddresses(
  [1, 2, 3],                    // protocols
  [router1, router2, pool],     // explicit routers
  [token1, rareToken, token2],  // explicit token addresses
  [extra1, extra2, extra3]
);
```

## Token Type Classification

```javascript
const TokenType = {
  CANONICAL: 0,  // Native to the chain (USDC on Ethereum)
  BRIDGED: 1,    // Bridged version (USDC.e on Polygon)
  WRAPPED: 2     // Wrapped native (WETH, WMATIC, etc.)
};
```

### Multi-Type Support

Some tokens have multiple types on the same chain:

```javascript
// Polygon USDC has both types
{ id: 1, type: CANONICAL, address: "0x3c499..." }  // Native USDC
{ id: 1, type: BRIDGED, address: "0x2791B..." }    // USDC.e (bridged)
```

The contract uses `tokenRegistry[chainId][tokenId][tokenType]` to resolve the correct address.

## Integration with Off-Chain System

### Brain.py Token Discovery

The Python brain discovers 300+ tokens using:

```python
# Load tokens from 1inch API
tokens_list = TokenLoader.get_tokens(chain_id)

# Build comprehensive graph
for token in tokens_list[:100]:
    inventory[chain_id][token['symbol']] = token

# Tiered scanning strategy
tier1_tokens = ['USDC', 'USDT', 'DAI', 'WETH', 'WBTC']  # Every cycle
tier2_tokens = ['UNI', 'LINK', 'AAVE', ...]              # Every 2nd cycle
tier3_tokens = [all other discovered tokens]             # Every 5th cycle
```

### Encoding Selection

Brain automatically chooses optimal encoding:

```javascript
// Check if token is in registry
if (isTokenRegistered(chainId, tokenAddress)) {
    // Use REGISTRY_ENUMS (compact calldata)
    encoding = REGISTRY_ENUMS;
    tokenIds = [1, 2, 3];  // Registry IDs
} else {
    // Use RAW_ADDRESSES (explicit addresses)
    encoding = RAW_ADDRESSES;
    tokenAddresses = [addr1, addr2, addr3];
}
```

## Adding Support for New Chains

To add a new chain:

1. **Update setupTokenRegistry.js**:
```javascript
// Add chain configuration
const CHAIN_CONFIGS = {
  // ... existing chains ...
  
  // New chain
  250: {  // Fantom
    tokens: [
      { id: 0, type: TokenType.WRAPPED, address: "0x21be..." },  // WFTM
      { id: 1, type: TokenType.CANONICAL, address: "0x04068..." }, // USDC
      // ... more tokens
    ]
  }
};
```

2. **Run script on new chain**:
```bash
export EXECUTOR_ADDRESS=0x...
npx hardhat run scripts/setupTokenRegistry.js --network fantom
```

3. **Update brain.py** (if needed):
```python
# Add chain to CHAINS config
CHAINS = {
    # ... existing chains ...
    250: {
        'name': 'Fantom',
        'rpc': 'https://rpc.ftm.tools',
        'tokens': {...}
    }
}
```

## Maintenance

### Viewing Current Registry

```javascript
// Check if token is registered
const address = await executor.tokenRegistry(
  chainId,    // e.g., 137 for Polygon
  tokenId,    // e.g., 1 for USDC
  tokenType   // e.g., 0 for CANONICAL
);

if (address !== "0x0000000000000000000000000000000000000000") {
  console.log(`Token ID ${tokenId} is registered:`, address);
}
```

### Updating Token Addresses

Only the contract owner can update the registry:

```javascript
// Update existing registration
await executor.setToken(chainId, tokenId, tokenType, newAddress);
```

### Batch Operations

For efficiency, use batch operations:

```javascript
await executor.batchSetTokens(
  [137, 137, 137],        // chainIds
  [1, 2, 3],              // tokenIds
  [0, 0, 0],              // tokenTypes
  [addr1, addr2, addr3]   // addresses
);
```

## Security Considerations

### Owner Control

✅ Only contract owner can call `setToken()` and `batchSetTokens()`
✅ Token assignments emit events for transparency
✅ Registry is publicly readable for verification

### Token ID Collisions

⚠️ Owner must avoid assigning same (tokenId, tokenType) twice on same chain
✅ Follow documented ID ranges to maintain consistency
✅ Use `setToken()` to update if needed (replaces existing registration)

### Validation

- REGISTRY_ENUMS encoding reverts if token not registered
- RAW_ADDRESSES encoding requires no validation (explicit addresses)
- Standard ERC20 checks apply during swap execution

## Related Documentation

- [TOKEN_REGISTRY_DESIGN.md](../contracts/TOKEN_REGISTRY_DESIGN.md) - Comprehensive design document
- [RouteEncodingSpec.md](../contracts/RouteEncodingSpec.md) - Route encoding specification
- [SystemArchitecture.md](../contracts/SystemArchitecture.md) - System architecture overview
