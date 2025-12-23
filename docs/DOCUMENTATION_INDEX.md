# Titan System Documentation Index

## 📖 Complete Documentation Guide

Welcome to the Titan system documentation! This index helps you navigate all documentation files.

---

## 🌟 New Documentation (This PR)

### 1. **Enum Registry & Token Design** ⭐ PRIMARY DOCUMENT
**File**: [`docs/ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md)

**Complete coverage of:**
- ✅ Chain Enum Registry (A-J System)
- ✅ Token Rank System with allocation ranges
- ✅ DEX Enum Registry
- ✅ Protocol ID System
- ✅ Token Type Classification (CANONICAL, BRIDGED, WRAPPED)
- ✅ Token ID Enum (OmniArbExecutor)
- ✅ USDC Normalization System
- ✅ System Architecture with flow diagrams
- ✅ Route Encoding dual-mode architecture
- ✅ Data flow architecture
- ✅ Integration examples (JavaScript & Python)
- ✅ Security considerations

**Start here for:** Complete understanding of the enum registry and token design

---

### 2. **Architecture Quick Reference** ⭐ QUICK LOOKUP
**File**: [`docs/ARCHITECTURE_QUICK_REFERENCE.md`](./ARCHITECTURE_QUICK_REFERENCE.md)

**Quick access to:**
- ✅ All documentation cross-references
- ✅ Quick lookup tables (Chain enums, Token ranks, Protocol IDs)
- ✅ File organization map
- ✅ Common tasks with examples
- ✅ Getting started guides for different roles
- ✅ Security notes
- ✅ Cross-reference links

**Start here for:** Quick lookups and navigation to detailed docs

---

### 3. **System Visual Diagrams** ⭐ VISUAL GUIDE
**File**: [`docs/SYSTEM_VISUAL_DIAGRAMS.md`](./SYSTEM_VISUAL_DIAGRAMS.md)

**Visual representations of:**
- ✅ System architecture overview
- ✅ Enum registry hierarchy
- ✅ Token design flow
- ✅ Route execution flow
- ✅ Dual encoding modes comparison
- ✅ Token type classification
- ✅ Security architecture

**Start here for:** Visual understanding of system components and flows

---

## 📚 Existing Core Documentation

### Smart Contract Documentation

#### **System Architecture**
**File**: [`contracts/SystemArchitecture.md`](../contracts/SystemArchitecture.md)

**Topics:**
- Contract modules overview
- OmniArbExecutor functionality
- SwapHandler module details
- Flashloan sources (Aave V3, Balancer V3)
- Registry mappings
- Configuration
- Security features
- Emergency functions

---

#### **Route Encoding Specification**
**File**: [`contracts/RouteEncodingSpec.md`](../contracts/RouteEncodingSpec.md)

**Topics:**
- RAW_ADDRESSES encoding format
- REGISTRY_ENUMS encoding format
- Protocol-specific extra data formats
- Token flow interpretation
- Critical sanity checks
- Registry setup
- Complete examples

---

#### **OmniArb Matrix Design**
**File**: [`docs/OMNIARB_MATRIX_DESIGN.md`](./OMNIARB_MATRIX_DESIGN.md)

**Topics:**
- A-J chain enum mapping (deep dive)
- Token rank mapping per chain
- Token ordering (STATIC_ORDER)
- Smart contract implementation
- Payload structure
- Validation rules
- USDC normalization
- Deployment guide
- Testing procedures

---

#### **Canonical Specification**
**File**: [`docs/CANONICAL_SPECIFICATION.md`](./CANONICAL_SPECIFICATION.md)

**Topics:**
- Authoritative enum ordering tables
- RouteData encoding specification
- Per-protocol extra data formats
- Operational guardrails
- Off-chain ABI type constants
- Integration notes

---

## 🔍 Documentation by Use Case

### For Developers

**Getting Started:**
1. [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) - System overview
2. [`CANONICAL_SPECIFICATION.md`](./CANONICAL_SPECIFICATION.md) - Enum values
3. [`contracts/RouteEncodingSpec.md`](../contracts/RouteEncodingSpec.md) - Route encoding

**Reference:**
- [`ARCHITECTURE_QUICK_REFERENCE.md`](./ARCHITECTURE_QUICK_REFERENCE.md) - Quick lookups
- [`SYSTEM_VISUAL_DIAGRAMS.md`](./SYSTEM_VISUAL_DIAGRAMS.md) - Visual guides

---

### For Integrators

**Getting Started:**
1. [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) - Integration Examples section
2. [`CANONICAL_SPECIFICATION.md`](./CANONICAL_SPECIFICATION.md) - Off-Chain ABI Types
3. [`ARCHITECTURE_QUICK_REFERENCE.md`](./ARCHITECTURE_QUICK_REFERENCE.md) - Common Tasks

**Reference:**
- [`contracts/RouteEncodingSpec.md`](../contracts/RouteEncodingSpec.md) - Encoding details
- [`SYSTEM_VISUAL_DIAGRAMS.md`](./SYSTEM_VISUAL_DIAGRAMS.md) - Flow diagrams

---

### For Operations

**Getting Started:**
1. [`OMNIARB_MATRIX_DESIGN.md`](./OMNIARB_MATRIX_DESIGN.md) - Deployment Guide
2. [`contracts/SystemArchitecture.md`](../contracts/SystemArchitecture.md) - Configuration
3. [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) - Security Considerations

**Reference:**
- [`ARCHITECTURE_QUICK_REFERENCE.md`](./ARCHITECTURE_QUICK_REFERENCE.md) - File organization
- Scripts in `scripts/` directory

---

## 📋 Quick Lookup Tables

### Chain Enum (A-J System)
```
A → Ethereum (1)          F → Avalanche (43114)
B → Polygon (137)         G → Fantom (250)
C → Base (8453)           H → Gnosis (100)
D → Arbitrum (42161)      I → Celo (42220)
E → Optimism (10)         J → Linea (59144)
```

### Token Rank Ranges
```
A: 1000-1999   (Ethereum)     F: 6000-6999   (Avalanche)
B: 2000-2999   (Polygon)      G: 7000-7999   (Fantom)
C: 3000-3999   (Base)         H: 8000-8999   (Gnosis)
D: 4000-4999   (Arbitrum)     I: 9000-9999   (Celo)
E: 5000-5999   (Optimism)     J: 10000-10999 (Linea)
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

---

## 🗺️ Documentation Map

```
docs/
├── ENUM_REGISTRY_AND_TOKEN_DESIGN.md  ⭐ NEW: Complete system guide
├── ARCHITECTURE_QUICK_REFERENCE.md    ⭐ NEW: Quick reference
├── SYSTEM_VISUAL_DIAGRAMS.md          ⭐ NEW: Visual diagrams
├── DOCUMENTATION_INDEX.md             ⭐ NEW: This file
├── CANONICAL_SPECIFICATION.md         ✓ Authoritative enum reference
└── OMNIARB_MATRIX_DESIGN.md           ✓ A-J system deep dive

contracts/
├── RouteEncodingSpec.md               ✓ Route encoding guide
├── SystemArchitecture.md              ✓ Contract architecture
├── OmniArbExecutor.sol                ✓ Main executor contract
├── OmniArbDecoder.sol                 ✓ A-J decoder contract
└── modules/
    └── SwapHandler.sol                ✓ Swap primitive

core/
├── enum_matrix.py                     ✓ Python ChainID enum
├── token_loader.py                    ✓ Token utilities
└── token_discovery.py                 ✓ Token discovery

scripts/
├── deployDecoder.js                   ✓ Deploy decoder
├── configureTokenRanks.js             ✓ Configure ranks
└── exampleUsage.js                    ✓ Usage examples
```

---

## 🎯 Recommended Reading Order

### Path 1: Quick Start (30 minutes)
1. [`ARCHITECTURE_QUICK_REFERENCE.md`](./ARCHITECTURE_QUICK_REFERENCE.md) - Overview
2. [`SYSTEM_VISUAL_DIAGRAMS.md`](./SYSTEM_VISUAL_DIAGRAMS.md) - Visual understanding
3. Quick lookup tables (above)

### Path 2: Developer Deep Dive (2 hours)
1. [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) - Complete system
2. [`CANONICAL_SPECIFICATION.md`](./CANONICAL_SPECIFICATION.md) - Enum reference
3. [`contracts/RouteEncodingSpec.md`](../contracts/RouteEncodingSpec.md) - Encoding details
4. [`contracts/SystemArchitecture.md`](../contracts/SystemArchitecture.md) - Contract details

### Path 3: Integration Focus (1 hour)
1. [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) - Integration Examples
2. [`contracts/RouteEncodingSpec.md`](../contracts/RouteEncodingSpec.md) - Ethers.js examples
3. [`ARCHITECTURE_QUICK_REFERENCE.md`](./ARCHITECTURE_QUICK_REFERENCE.md) - Common tasks

### Path 4: Operations & Deployment (1 hour)
1. [`OMNIARB_MATRIX_DESIGN.md`](./OMNIARB_MATRIX_DESIGN.md) - Deployment guide
2. [`contracts/SystemArchitecture.md`](../contracts/SystemArchitecture.md) - Configuration
3. `scripts/deployDecoder.js` and `scripts/configureTokenRanks.js`

---

## 🔗 External Resources

### Smart Contracts
- **Aave V3**: [https://docs.aave.com/developers/core-contracts/pool](https://docs.aave.com/developers/core-contracts/pool)
- **Balancer V3**: [https://docs.balancer.fi/](https://docs.balancer.fi/)
- **Uniswap V3**: [https://docs.uniswap.org/contracts/v3/overview](https://docs.uniswap.org/contracts/v3/overview)
- **Curve**: [https://curve.readthedocs.io/](https://curve.readthedocs.io/)

### Development
- **Hardhat**: [https://hardhat.org/docs](https://hardhat.org/docs)
- **Ethers.js**: [https://docs.ethers.org/v6/](https://docs.ethers.org/v6/)
- **OpenZeppelin**: [https://docs.openzeppelin.com/](https://docs.openzeppelin.com/)

---

## 📝 Key Concepts Summary

### Enum Registry
The system uses enums at multiple levels:
- **Chain Level**: A-J letters for chain identification
- **DEX Level**: Numeric IDs for DEX protocol identification
- **Token Level**: Ranks (ranges) and IDs (enums) for token identification
- **Protocol Level**: IDs for swap protocol selection

### Token Design
Two parallel token identification systems:
1. **OmniArbDecoder**: Uses chain letters (A-J) + token ranks (ranges)
2. **OmniArbExecutor**: Uses token enum + token type (CANONICAL/BRIDGED/WRAPPED)

### Route Encoding
Two encoding modes for flexibility:
1. **RAW_ADDRESSES**: Direct addresses (faster, larger calldata)
2. **REGISTRY_ENUMS**: Enum-based resolution (smaller calldata, centralized control)

### Architecture
Multi-contract system:
- **OmniArbExecutor**: Main execution brain
- **OmniArbDecoder**: A-J decoder (separate deployment)
- **SwapHandler**: Reusable swap primitive
- **Interfaces**: Standardized protocol interfaces

---

## ❓ FAQ Quick Links

**Q: How do chain enums work?**
→ See [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) § Chain Enum Registry

**Q: How do I encode a route?**
→ See [`contracts/RouteEncodingSpec.md`](../contracts/RouteEncodingSpec.md) or [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) § Integration Examples

**Q: What's the difference between token ranks and token IDs?**
→ See [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) § Token Design & Token ID System

**Q: How do I deploy the decoder?**
→ See [`OMNIARB_MATRIX_DESIGN.md`](./OMNIARB_MATRIX_DESIGN.md) § Deployment Guide

**Q: Which encoding mode should I use?**
→ See [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) § Route Encoding Dual-Mode Architecture

**Q: How does USDC normalization work?**
→ See [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) § USDC Normalization System

---

## 🛡️ Security & Best Practices

**Critical Rules:**
- ❌ Never reorder enums (enum values = declaration order)
- ❌ Never reassign chain letters (A-J is immutable)
- ❌ Never reorder STATIC_ORDER (append only)
- ✅ Always use abi.encode (not abi.encodePacked)
- ✅ Always validate array lengths match
- ✅ Always use SafeERC20 for token operations

**See**: [`ENUM_REGISTRY_AND_TOKEN_DESIGN.md`](./ENUM_REGISTRY_AND_TOKEN_DESIGN.md) § Security Considerations

---

## 📞 Support & Contributing

**Questions?**
1. Check this index for relevant documentation
2. Search the specific document using the table of contents
3. Review integration examples
4. Check test files in `test/` and `tests/` directories

**Found an issue?**
1. Check if it's covered in existing documentation
2. Review security considerations
3. Examine the relevant contract code
4. Consult the canonical specification for authoritative values

---

**Last Updated**: 2025-12-22  
**Version**: 1.0.0  
**Status**: Complete ✅

---

## 📈 Documentation Coverage

This documentation set provides **complete coverage** of:
- ✅ Chain identification system (A-J)
- ✅ Token identification system (ranks & enums)
- ✅ DEX registry system
- ✅ Protocol ID system
- ✅ Route encoding (both modes)
- ✅ Token type classification
- ✅ System architecture
- ✅ Integration examples
- ✅ Security considerations
- ✅ Visual diagrams
- ✅ Quick reference guides

**Total Documentation Pages**: 3 new comprehensive documents + existing core docs  
**Total Diagrams**: 7 major visual diagrams  
**Integration Examples**: 15+ complete examples  
**Quick Lookup Tables**: 6+ reference tables
