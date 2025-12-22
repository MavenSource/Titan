# OmniArb Matrix A-J Design - Implementation Documentation

## Overview

The OmniArb Matrix A-J design implements a cross-chain arbitrage system using a deterministic enum-based encoding scheme for chains and tokens. This document describes the implementation of the decoder system.

## Architecture

### 1. Chain Enum Mapping (A-J)

The system uses **`bytes1`** ASCII letters (A-J) to represent chains:

| Letter | Chain      | Chain ID |
|--------|------------|----------|
| A      | Ethereum   | 1        |
| B      | Polygon    | 137      |
| C      | Base       | 8453     |
| D      | Arbitrum   | 42161    |
| E      | Optimism   | 10       |
| F      | Avalanche  | 43114    |
| G      | Fantom     | 250      |
| H      | Gnosis     | 100      |
| I      | Celo       | 42220    |
| J      | Linea      | 59144    |

**Rules:**
- Fixed alphabetical ordering
- Append-only (never reassign letters)
- Stored as `bytes1` in payload (not `uint8`)

### 2. Token Rank Mapping

Each chain has a reserved range for token ranks:

| Chain     | Letter | Range        |
|-----------|--------|--------------|
| Ethereum  | A      | 1000-1999    |
| Polygon   | B      | 2000-2999    |
| Base      | C      | 3000-3999    |
| Arbitrum  | D      | 4000-4999    |
| Optimism  | E      | 5000-5999    |
| Avalanche | F      | 6000-6999    |
| Fantom    | G      | 7000-7999    |
| Gnosis    | H      | 8000-8999    |
| Celo      | I      | 9000-9999    |
| Linea     | J      | 10000-10999  |

**Token Rank Formula:**
```
rank = rangeStart(chainEnum) + index + 1
```

where `index` is the position in the STATIC_ORDER array for that chain.

### 3. Token Ordering (STATIC_ORDER)

Tokens within each chain follow a fixed order. Examples:

**Ethereum (A range 1000-1999):**
1. WETH (1000)
2. USDC (1001)
3. USDT (1002)
4. DAI (1003)
5. WBTC (1004)
... (see `scripts/configureTokenRanks.js` for full list)

**Polygon (B range 2000-2999):**
1. WMATIC (2000)
2. WETH (2001)
3. USDC (2002)
4. USDC.e (2003)
... (see `scripts/configureTokenRanks.js` for full list)

**Stability Rule:** STATIC_ORDER is fixed; new tokens append at the tail without shifting prior ranks.

## Smart Contract Implementation

### OmniArbDecoder.sol

The main decoder contract provides:

#### Key Functions

**Chain Validation:**
```solidity
function getChainId(bytes1 chainEnum) external view returns (uint256)
function isValidChainEnum(bytes1 chainEnum) external view returns (bool)
```

**Token Resolution:**
```solidity
function resolveToken(uint16 tokenRank) external view returns (address)
function getTokenByRank(uint16 tokenRank) external view returns (address)
```

**Payload Decoding:**
```solidity
function decodePayload(bytes calldata payload) external returns (DecodedPayload memory)
```

**Configuration (Owner Only):**
```solidity
function configureTokenRank(uint16 rank, address token) external onlyOwner
function configureTokenRanks(uint16[] calldata ranks, address[] calldata tokens) external onlyOwner
function configureBridgedUSDC(uint256 chainId, address bridged, address canonical) external onlyOwner
function updateRouteRegistryHash(bytes32 newHash) external onlyOwner
```

### Payload Structure

The decoder expects payloads encoded as:

```solidity
(
    bytes1 chainEnum,           // 'A'..'J'
    uint16 tokenRank,           // Chain-specific rank
    uint256 amount,             // Token amount
    bytes routeParams,          // Routing parameters
    uint16 minProfitBps,        // Min profit in basis points
    uint64 expiry,              // Expiry timestamp
    address receiver,           // Receiver address
    bytes32 routeRegistryHash,  // Route registry hash
    uint256 nonce               // Unique nonce
)
```

### Validation Rules

The decoder validates:
1. **Chain Match:** `enumToChainId[chainEnum] == block.chainid`
2. **Token Configured:** `rankToToken[tokenRank] != address(0)`
3. **Not Expired:** `block.timestamp <= expiry`
4. **Nonce Unused:** `!usedNonces[nonce]`
5. **Route Hash:** `routeRegistryHash == contract.routeRegistryHash` (if configured)
6. **Profit Valid:** `minProfitBps <= 10000`

### USDC Normalization

The decoder supports normalizing bridged USDC (e.g., USDC.e) to canonical USDC:

**Chains with USDC variants:**
- Polygon: USDC.e → USDC
- Arbitrum: USDC.e → USDC
- Optimism: USDC.e → USDC
- Avalanche: USDC.e → USDC

This prevents mixing non-fungible variants in arbitrage operations.

## Deployment Guide

### 1. Deploy the Decoder

```bash
npx hardhat run scripts/deployDecoder.js --network <network>
```

Save the deployed address to `.env`:
```
DECODER_ADDRESS=0x...
```

### 2. Configure Token Ranks

```bash
DECODER_ADDRESS=0x... npx hardhat run scripts/configureTokenRanks.js --network <network>
```

This script:
- Detects the current chain
- Configures appropriate token ranks for that chain
- Sets up USDC normalization if applicable

### 3. Verify Configuration

Check chain enum mappings:
```javascript
const decoder = await ethers.getContractAt("OmniArbDecoder", DECODER_ADDRESS);
await decoder.enumToChainId("0x41"); // 'A' → should return 1 (Ethereum)
```

Check token rank mappings:
```javascript
await decoder.rankToToken(2001); // Should return WETH address on Polygon
```

## Usage Examples

### Encoding a Payload

```javascript
const ethers = require('ethers');

function toBytes1(str) {
  return ethers.encodeBytes32String(str).slice(0, 4);
}

const payload = ethers.AbiCoder.defaultAbiCoder().encode(
  ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
  [
    toBytes1("B"),                    // Polygon
    2001,                             // WETH rank on Polygon
    ethers.parseEther("1"),           // 1 WETH
    "0x",                             // routeParams
    100,                              // 1% min profit
    Math.floor(Date.now() / 1000) + 3600, // 1 hour expiry
    receiverAddress,
    ethers.ZeroHash,
    1                                 // nonce
  ]
);
```

### Decoding a Payload

```javascript
const decoded = await decoder.decodePayload(payload);

console.log("Chain:", decoded.chainEnum);
console.log("Token Rank:", decoded.tokenRank);
console.log("Amount:", decoded.amount.toString());
console.log("Receiver:", decoded.receiver);
```

### Resolving a Token

```javascript
const tokenAddress = await decoder.resolveToken(2001); // WETH on Polygon
console.log("Token address:", tokenAddress);
```

## Testing

Run the test suite:

```bash
npx hardhat test test/OmniArbDecoder.test.js
```

The tests cover:
- Chain enum initialization
- Token rank configuration
- Token rank ranges
- USDC normalization
- Payload decoding
- Validation rules
- Edge cases

## Security Considerations

1. **Owner-Only Configuration:** Only the contract owner can configure token ranks and USDC mappings
2. **Nonce Replay Protection:** Each nonce can only be used once
3. **Expiry Validation:** Payloads expire after the specified timestamp
4. **Chain Validation:** Payloads can only execute on the intended chain
5. **Token Validation:** Only configured tokens can be used
6. **Route Registry Validation:** Optional hash verification for route authenticity

## Future Enhancements

1. **Additional Chains:** Add more chains by extending the A-J system (K, L, M, etc.)
2. **Token Updates:** Add new tokens by appending to STATIC_ORDER for each chain
3. **Multi-Signature Configuration:** Add multi-sig control for critical configuration changes
4. **Batch Operations:** Support multiple payloads in a single transaction
5. **Gas Optimization:** Further optimize storage and computation costs

## References

- Smart Contract: `contracts/OmniArbDecoder.sol`
- Deployment Script: `scripts/deployDecoder.js`
- Configuration Script: `scripts/configureTokenRanks.js`
- Tests: `test/OmniArbDecoder.test.js`
