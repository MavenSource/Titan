# 📚 Enum Registry & Token Design Documentation

## Quick Navigation

Looking for information about the **enum registry**, **token design**, **token ID system**, or **architecture**?

👉 **Start here**: [`docs/DOCUMENTATION_INDEX.md`](docs/DOCUMENTATION_INDEX.md)

---

## 📖 New Comprehensive Documentation

This repository now includes complete documentation for the Titan enum registry and token design:

### Primary Documents

1. **[Enum Registry & Token Design](docs/ENUM_REGISTRY_AND_TOKEN_DESIGN.md)** ⭐
   - Complete chain enum registry (A-J system)
   - Token rank allocation and formula
   - DEX enum registry
   - Token type classification
   - USDC normalization
   - Integration examples

2. **[Architecture Quick Reference](docs/ARCHITECTURE_QUICK_REFERENCE.md)** 🔍
   - Quick lookup tables
   - Common tasks
   - File organization
   - Cross-references

3. **[System Visual Diagrams](docs/SYSTEM_VISUAL_DIAGRAMS.md)** 📊
   - Architecture diagrams
   - Flow diagrams
   - Token resolution flows
   - Security architecture

4. **[Documentation Index](docs/DOCUMENTATION_INDEX.md)** 📑
   - Master index of all docs
   - Reading paths
   - FAQ with links
   - Coverage summary

---

## 🎯 Quick Lookup

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
Ethereum:  1000-1999    Avalanche: 6000-6999
Polygon:   2000-2999    Fantom:    7000-7999
Base:      3000-3999    Gnosis:    8000-8999
Arbitrum:  4000-4999    Celo:      9000-9999
Optimism:  5000-5999    Linea:     10000-10999
```

### Protocol IDs
```
1 → UniV2 (Quickswap, Sushiswap, etc.)
2 → UniV3 (Uniswap V3)
3 → Curve (Curve pools)
```

---

## 🚀 For Different Users

### Developers
Start with: [ENUM_REGISTRY_AND_TOKEN_DESIGN.md](docs/ENUM_REGISTRY_AND_TOKEN_DESIGN.md)

### Integrators
Start with: [Integration Examples](docs/ENUM_REGISTRY_AND_TOKEN_DESIGN.md#integration-examples)

### Operations
Start with: [OMNIARB_MATRIX_DESIGN.md](docs/OMNIARB_MATRIX_DESIGN.md) - Deployment Guide

---

## 📂 File Structure

### Smart Contracts
```
contracts/
├── OmniArbExecutor.sol        # Main executor
├── OmniArbDecoder.sol         # A-J decoder
└── modules/SwapHandler.sol    # Swap primitive
```

### Python Core
```
core/
├── enum_matrix.py             # ChainID enum
├── token_loader.py            # Token utilities
└── token_discovery.py         # Token discovery
```

### Documentation
```
docs/
├── ENUM_REGISTRY_AND_TOKEN_DESIGN.md  # Complete guide
├── ARCHITECTURE_QUICK_REFERENCE.md    # Quick reference
├── SYSTEM_VISUAL_DIAGRAMS.md          # Visual diagrams
└── DOCUMENTATION_INDEX.md             # Master index
```

---

## 📖 Full Documentation Index

For the complete documentation index with all links, FAQ, and reading paths:

👉 **[docs/DOCUMENTATION_INDEX.md](docs/DOCUMENTATION_INDEX.md)**

---

**Last Updated**: 2025-12-22  
**Version**: 1.0.0
