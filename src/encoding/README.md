# Titan Encoding Module

This directory contains TypeScript encoding utilities for the Titan arbitrage system.

## Files

### titanEnums.ts
Locked enum constants that match the on-chain Solidity enums. These should never be reordered - only appended to.

```typescript
import { FlashSource, RouteEncoding, SwapProtocol, Dex, TokenType, TokenId } from './titanEnums';

// Example: Use FlashSource.AaveV3 (0) or FlashSource.BalancerV3 (1)
```

### routeEncoder.ts
Encodes multi-hop routes using REGISTRY_ENUMS format.

```typescript
import { encodeRegistryRoute, RegistryHop } from './routeEncoder';
import { SwapProtocol, Dex, TokenId, TokenType } from './titanEnums';

const hops: RegistryHop[] = [
  {
    protocol: SwapProtocol.UNIV3,
    dexId: Dex.UniV3,
    tokenOutId: TokenId.USDC,
    tokenOutType: TokenType.CANONICAL,
    extra: ethers.AbiCoder.defaultAbiCoder().encode(['uint24'], [3000]) // fee tier
  }
];

const routeData = encodeRegistryRoute(hops);
```

### ajTranslator.ts
Translates A-J matrix data into RegistryHop format, preventing protocol/DEX mismatches.

```typescript
import { matrixRowToHop, dexToHop, tokenToIdType } from './ajTranslator';

// Convert a matrix row to a hop
const hop = matrixRowToHop({
  dexCompatibility: "Uniswap V3",
  nativeToken: "USDC",
  wrappedEquivalent: "USDC",
  feeTier: 3000
});

// Or manually convert DEX compatibility string
const { protocol, dexId } = dexToHop("Curve");
```

## Usage with OmniArbExecutor

```typescript
import { ethers } from 'ethers';
import { FlashSource } from './src/encoding/titanEnums';
import { encodeRegistryRoute } from './src/encoding/routeEncoder';

// Create route hops using the translator
const hops = [/* your hops */];
const routeData = encodeRegistryRoute(hops);

// Execute arbitrage
await executor.execute(
  FlashSource.AaveV3,
  loanTokenAddress,
  loanAmount,
  routeData
);
```

## Important Notes

1. **Never reorder enums** - Always append new values to the end
2. **Match protocol IDs** - Use SwapProtocol constants (UNIV2=1, UNIV3=2, CURVE=3)
3. **Curve pools** - Store pool addresses in dexRouter registry or use RAW_ADDRESSES encoding
4. **Extra data format**:
   - UniV2: `0x` (empty)
   - UniV3: `abi.encode(['uint24'], [fee])`
   - Curve: `abi.encode(['int128', 'int128'], [i, j])`
