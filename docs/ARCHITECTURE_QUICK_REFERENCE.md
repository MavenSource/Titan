# Titan Architecture Quick Reference

## 📚 Complete Documentation Overview

This document provides a quick reference to all architecture documentation in the Titan system.

---

## 🎯 Key Documents

### 1. **Enum Registry & Token Design** (NEW ✨)
**Location**: `docs/ENUM_REGISTRY_AND_TOKEN_DESIGN.md`

**What's Inside:**
- Complete chain enum registry (A-J system)
- Token ID and token rank system
- DEX enum registry
- Protocol ID system
- Token type classification (CANONICAL, BRIDGED, WRAPPED)
- USDC normalization system
- Visual architecture diagrams
- Integration examples

**Use this for:**
- Understanding the enum-based addressing system
- Token rank formula and allocation
- Chain identification (A-J letters)
- Token type distinctions

---

### 2. **System Architecture**
**Location**: `contracts/SystemArchitecture.md`

**What's Inside:**
- Contract component overview
- OmniArbExecutor functionality
- SwapHandler module
- Flashloan sources (Aave V3, Balancer V3)
- Registry mappings
- Security features

**Use this for:**
- Understanding contract interactions
- Flashloan flow
- Swap execution primitives
- Registry configuration

---

### 3. **Route Encoding Specification**
**Location**: `contracts/RouteEncodingSpec.md`

**What's Inside:**
- RAW_ADDRESSES encoding format
- REGISTRY_ENUMS encoding format
- Protocol-specific extra data formats
- Token flow interpretation
- Critical sanity checks

**Use this for:**
- Encoding routes for execution
- Understanding hop-by-hop swaps
- Protocol-specific parameters
- Off-chain integration

---

### 4. **Canonical Specification**
**Location**: `docs/CANONICAL_SPECIFICATION.md`

**What's Inside:**
- Contract modules overview
- Standardized interfaces
- Enum ordering tables (AUTHORITATIVE)
- RouteData encoding specification
- Per-protocol extra data formats
- Operational guardrails

**Use this for:**
- Definitive enum value reference
- ABI type constants
- Integration guidelines
- Enum ordering (never reorder!)

---

### 5. **OmniArb Matrix Design**
**Location**: `docs/OMNIARB_MATRIX_DESIGN.md`

**What's Inside:**
- A-J chain enum mapping
- Token rank mapping per chain
- Token ordering (STATIC_ORDER)
- Deployment guide
- Testing procedures
- Security considerations

**Use this for:**
- A-J system deep dive
- Token rank configuration
- Decoder deployment
- USDC normalization setup

---

## 🔍 Quick Lookup Tables

### Chain Enum (A-J System)
```
A → Ethereum (1)      F → Avalanche (43114)
B → Polygon (137)     G → Fantom (250)
C → Base (8453)       H → Gnosis (100)
D → Arbitrum (42161)  I → Celo (42220)
E → Optimism (10)     J → Linea (59144)
```

### Token Rank Ranges
```
Ethereum:  1000-1999
Polygon:   2000-2999
Base:      3000-3999
Arbitrum:  4000-4999
Optimism:  5000-5999
Avalanche: 6000-6999
Fantom:    7000-7999
Gnosis:    8000-8999
Celo:      9000-9999
Linea:     10000-10999
```

### Protocol IDs
```
1 → UniV2 (Quickswap, Sushiswap, etc.)
2 → UniV3 (Uniswap V3)
3 → Curve (Curve pools)
```

### Token Types
```
0 → CANONICAL (native to chain)
1 → BRIDGED (bridged version, e.g., USDC.e)
2 → WRAPPED (wrapped native, e.g., WETH, WMATIC)
```

### Route Encoding Modes
```
0 → RAW_ADDRESSES (explicit router + token addresses)
1 → REGISTRY_ENUMS (DEX + token enums resolved on-chain)
```

### Flashloan Sources
```
0 → Aave V3 (flashLoanSimple)
1 → Balancer V3 (vault.unlock)
```

---

## 🗂️ File Organization

### Smart Contracts
```
contracts/
├── OmniArbExecutor.sol        # Main executor (flashloan + routing)
├── OmniArbDecoder.sol         # A-J decoder + token rank resolver
├── modules/
│   └── SwapHandler.sol        # System-wide swap primitive
└── interfaces/
    ├── IAaveV3.sol            # Aave V3 interfaces
    ├── IB3.sol                # Balancer V3 interfaces
    ├── IUniV2.sol             # UniswapV2 interface
    ├── IUniV3.sol             # UniswapV3 interface
    └── ICurve.sol             # Curve interface
```

### Core Python
```
core/
├── enum_matrix.py             # ChainID enum + ProviderManager
├── token_loader.py            # Token loading utilities
└── token_discovery.py         # Token discovery system
```

### Documentation
```
docs/
├── ENUM_REGISTRY_AND_TOKEN_DESIGN.md     # NEW: Complete enum & token docs
├── CANONICAL_SPECIFICATION.md            # Authoritative enum reference
├── OMNIARB_MATRIX_DESIGN.md              # A-J system deep dive
└── ARCHITECTURE_QUICK_REFERENCE.md       # This file
```

```
contracts/
├── RouteEncodingSpec.md                  # Route encoding specification
└── SystemArchitecture.md                 # Contract architecture
```

---

## 🚀 Getting Started

### For Developers
1. Start with `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` for system overview
2. Review `CANONICAL_SPECIFICATION.md` for enum values
3. Use `RouteEncodingSpec.md` for route encoding
4. Reference `SystemArchitecture.md` for contract details

### For Integrators
1. Read `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` - Integration Examples section
2. Check `CANONICAL_SPECIFICATION.md` - Off-Chain ABI Type Constants
3. Use the Quick Lookup Tables above for encoding

### For Operations
1. Review `OMNIARB_MATRIX_DESIGN.md` - Deployment Guide
2. Check `SystemArchitecture.md` - Configuration section
3. Use `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` - Security Considerations

---

## 📋 Common Tasks

### Encoding a Route (RAW_ADDRESSES)
```javascript
const routeData = abi.encode(
  ["uint8", "uint8[]", "address[]", "address[]", "bytes[]"],
  [0, protocols, routers, tokenPath, extra]
);
```
**See**: `RouteEncodingSpec.md` → RAW_ADDRESSES Format

### Encoding a Route (REGISTRY_ENUMS)
```javascript
const routeData = abi.encode(
  ["uint8", "uint8[]", "uint8[]", "uint8[]", "uint8[]", "bytes[]"],
  [1, protocols, dexIds, tokenIds, tokenTypes, extra]
);
```
**See**: `RouteEncodingSpec.md` → REGISTRY_ENUMS Format

### Encoding a Decoder Payload
```javascript
const payload = abi.encode(
  ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
  [chainEnum, tokenRank, amount, routeParams, minProfitBps, expiry, receiver, routeHash, nonce]
);
```
**See**: `OMNIARB_MATRIX_DESIGN.md` → Payload Structure

### Getting Chain Provider (Python)
```python
from core.enum_matrix import ChainID, ProviderManager
provider = ProviderManager.get_provider(ChainID.POLYGON)
```
**See**: `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` → Python Integration

---

## 🔗 Cross-References

### Chain Enums
- Solidity A-J: `OmniArbDecoder.sol` lines 99-138
- Python ChainID: `core/enum_matrix.py` lines 8-28
- Documentation: `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` → Chain Enum Registry

### Token Ranks
- Solidity mapping: `OmniArbDecoder.sol` line 50
- Configuration: `scripts/configureTokenRanks.js`
- Documentation: `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` → Token Rank System

### DEX Registry
- Solidity mapping: `OmniArbExecutor.sol` line 143
- Documentation: `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` → DEX Enum Registry

### Token Registry
- Solidity mapping: `OmniArbExecutor.sol` line 149
- Documentation: `ENUM_REGISTRY_AND_TOKEN_DESIGN.md` → Token Type System

---

## 🛡️ Security Notes

- **Never reorder enums** - Enum values are deterministic by declaration order
- **Append-only chain letters** - A-J system is immutable (append K, L, M... if needed)
- **Token rank stability** - STATIC_ORDER is fixed; new tokens append at tail
- **USDC normalization** - Always use canonical USDC to prevent fungibility issues
- **Nonce uniqueness** - Each decoder nonce can only be used once
- **Expiry validation** - Payloads must be executed before expiry timestamp

---

## 📞 Support

For questions or issues:
1. Check the relevant documentation above
2. Review integration examples in `ENUM_REGISTRY_AND_TOKEN_DESIGN.md`
3. Examine test files in `test/` and `tests/` directories
4. Review deployment scripts in `scripts/` directory

---

**Last Updated**: 2025-12-22  
**Version**: 1.0.0  
**Status**: Complete ✅
