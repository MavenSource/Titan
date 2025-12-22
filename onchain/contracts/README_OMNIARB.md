# OmniArb Matrix A-J System

A deterministic chain and token encoding system for cross-chain arbitrage operations.

## Quick Start

### 1. Deploy the Decoder

```bash
npx hardhat run scripts/deployDecoder.js --network polygon
```

Save the deployed address:
```bash
export DECODER_ADDRESS=0x...
```

### 2. Configure Token Ranks

```bash
DECODER_ADDRESS=0x... npx hardhat run scripts/configureTokenRanks.js --network polygon
```

### 3. Use the Encoder

```javascript
const encoder = require('./scripts/omniArbEncoder');

// Encode a payload
const payload = encoder.encodePayload({
  chainEnum: 'B',        // Polygon
  tokenRank: 2001,       // WETH on Polygon
  amount: ethers.parseEther("1"),
  minProfitBps: 100,     // 1% minimum profit
  expiry: Math.floor(Date.now() / 1000) + 3600,
  receiver: receiverAddress,
  nonce: Date.now()
});

// Decode a payload
const decoded = encoder.decodePayload(payload);
console.log(decoded);
```

## Chain Enum Mapping

| Letter | Chain      | Chain ID | Token Range    |
|--------|------------|----------|----------------|
| A      | Ethereum   | 1        | 1000-1999      |
| B      | Polygon    | 137      | 2000-2999      |
| C      | Base       | 8453     | 3000-3999      |
| D      | Arbitrum   | 42161    | 4000-4999      |
| E      | Optimism   | 10       | 5000-5999      |
| F      | Avalanche  | 43114    | 6000-6999      |
| G      | Fantom     | 250      | 7000-7999      |
| H      | Gnosis     | 100      | 8000-8999      |
| I      | Celo       | 42220    | 9000-9999      |
| J      | Linea      | 59144    | 10000-10999    |

## Token Rank System

Each chain has 1000 reserved slots for tokens. Token ranks are calculated as:

```
rank = rangeStart + tokenIndex
```

Example for Polygon (B):
- WMATIC: 2000 (index 0)
- WETH: 2001 (index 1)
- USDC: 2002 (index 2)
- USDC.e: 2003 (index 3)

## USDC Normalization

The system automatically normalizes bridged USDC to canonical USDC on supported chains:

- **Polygon**: USDC.e (2003) → USDC (2002)
- **Arbitrum**: USDC.e (4002) → USDC (4001)
- **Optimism**: USDC.e (5002) → USDC (5001)
- **Avalanche**: USDC.e (6002) → USDC (6001)

## Payload Structure

Payloads are encoded with the following fields:

```solidity
struct DecodedPayload {
    bytes1 chainEnum;           // A-J
    uint16 tokenRank;           // 1000-10999
    uint256 amount;             // Token amount
    bytes routeParams;          // Routing data
    uint16 minProfitBps;        // Min profit (0-10000)
    uint64 expiry;              // Unix timestamp
    address receiver;           // Receiver address
    bytes32 routeRegistryHash;  // Route verification
    uint256 nonce;              // Replay protection
}
```

## Security Features

- ✅ Chain validation (prevents cross-chain replay)
- ✅ Nonce tracking (prevents same-chain replay)
- ✅ Expiry validation (time-limited payloads)
- ✅ Token rank validation (only configured tokens)
- ✅ Owner-only configuration
- ✅ Route registry hash verification

## Files

- **Contract**: `contracts/OmniArbDecoder.sol`
- **Tests**: `test/OmniArbDecoder.test.js`
- **Deployment**: `scripts/deployDecoder.js`
- **Configuration**: `scripts/configureTokenRanks.js`
- **Encoder**: `scripts/omniArbEncoder.js`
- **Example**: `scripts/exampleUsage.js`
- **Documentation**: `docs/OMNIARB_MATRIX_DESIGN.md`

## Testing

Run the test suite:

```bash
npx hardhat test test/OmniArbDecoder.test.js
```

Run the encoder utility:

```bash
node scripts/omniArbEncoder.js
```

Run the example:

```bash
npx hardhat run scripts/exampleUsage.js --network polygon
```

## API Reference

### Encoder Utility

```javascript
const encoder = require('./scripts/omniArbEncoder');

// Convert letter to bytes1
encoder.toBytes1('B') // → '0x42000...'

// Get chain info
encoder.getChainId('B') // → 137
encoder.getChainEnum(137) // → 'B'
encoder.getChainName('B') // → 'Polygon'

// Token rank utilities
encoder.calculateTokenRank('B', 1) // → 2001
encoder.validateTokenRank('B', 2001) // → true

// Encode/decode payloads
encoder.encodePayload({ chainEnum, tokenRank, ... })
encoder.decodePayload(payload)
```

### Smart Contract

```solidity
// Read functions
decoder.enumToChainId(bytes1 chainEnum) → uint256
decoder.rankToToken(uint16 tokenRank) → address
decoder.isValidChainEnum(bytes1 chainEnum) → bool
decoder.getTokenByRank(uint16 tokenRank) → address
decoder.resolveToken(uint16 tokenRank) → address

// Write functions (owner only)
decoder.configureTokenRank(uint16 rank, address token)
decoder.configureTokenRanks(uint16[] ranks, address[] tokens)
decoder.configureBridgedUSDC(uint256 chainId, address bridged, address canonical)
decoder.updateRouteRegistryHash(bytes32 newHash)

// Payload decoding
decoder.decodePayload(bytes payload) → DecodedPayload
```

## Design Principles

1. **Deterministic**: Fixed ordering never changes
2. **Append-Only**: New tokens/chains append to the tail
3. **Range-Based**: Each chain has dedicated token rank range
4. **Validation**: Multiple layers of on-chain validation
5. **Normalization**: Automatic USDC variant handling

## Contributing

When adding new chains or tokens:

1. **Chains**: Add to the next available letter (K, L, M...)
2. **Tokens**: Append to the STATIC_ORDER for that chain
3. **Never**: Reassign letters or reorder existing tokens
4. **Always**: Update documentation and tests

## License

MIT
