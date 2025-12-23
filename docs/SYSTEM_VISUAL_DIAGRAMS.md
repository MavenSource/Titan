# Titan System Visual Diagrams

This document provides visual representations of the Titan system architecture, enum registry, and token design.

---

## 1. System Architecture Overview

```
╔══════════════════════════════════════════════════════════════════════════╗
║                     TITAN ARBITRAGE SYSTEM ARCHITECTURE                   ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│                         OFF-CHAIN COMPONENTS                              │
└──────────────────────────────────────────────────────────────────────────┘

    ┌─────────────┐      ┌─────────────┐      ┌─────────────┐
    │   Python    │      │ Aggregator  │      │    Route    │
    │    Brain    │─────▶│  Selector   │─────▶│   Builder   │
    │             │      │             │      │             │
    │ • ML Model  │      │ • DEX pick  │      │ • Encoding  │
    │ • Signals   │      │ • Routing   │      │ • Payload   │
    └─────────────┘      └─────────────┘      └──────┬──────┘
                                                      │
                                                      │ Transaction
                                                      ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                         ON-CHAIN COMPONENTS                               │
└──────────────────────────────────────────────────────────────────────────┘

    ┌───────────────────────────────────────────────────────────────┐
    │                    OmniArbExecutor.sol                         │
    │  ┌──────────────────────────────────────────────────────┐    │
    │  │              execute(flashSource, token, amount,     │    │
    │  │                      routeData)                       │    │
    │  └───────────────────────┬──────────────────────────────┘    │
    │                          │                                     │
    │         ┌────────────────┴────────────────┐                   │
    │         ▼                                 ▼                   │
    │  ┌─────────────┐                 ┌─────────────┐             │
    │  │  Aave V3    │                 │ Balancer V3 │             │
    │  │  Flashloan  │                 │   Unlock    │             │
    │  └──────┬──────┘                 └──────┬──────┘             │
    │         │                               │                     │
    │         └────────────┬──────────────────┘                     │
    │                      ▼                                        │
    │         ┌────────────────────────┐                            │
    │         │    _runRoute()         │                            │
    │         │  (Hop-by-Hop Execute)  │                            │
    │         └────────────┬───────────┘                            │
    │                      │                                        │
    │         ┌────────────┴────────────┐                           │
    │         │     SwapHandler         │                           │
    │         │   (Swap Primitive)      │                           │
    │         │                         │                           │
    │         │  Protocol 1: UniV2      │                           │
    │         │  Protocol 2: UniV3      │                           │
    │         │  Protocol 3: Curve      │                           │
    │         └─────────────────────────┘                           │
    └───────────────────────────────────────────────────────────────┘

    ┌───────────────────────────────────────────────────────────────┐
    │                   OmniArbDecoder.sol                           │
    │                                                                │
    │  • Chain Enum Validation (A-J)                                │
    │  • Token Rank Resolution                                       │
    │  • USDC Normalization                                          │
    │  • Payload Validation                                          │
    └───────────────────────────────────────────────────────────────┘
```

---

## 2. Enum Registry Hierarchy

```
╔══════════════════════════════════════════════════════════════════════════╗
║                        ENUM REGISTRY SYSTEM                               ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│                      CHAIN ENUM LAYER (A-J)                               │
└──────────────────────────────────────────────────────────────────────────┘

       A          B          C          D          E
   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
   │Ethereum││Polygon ││  Base  ││Arbitrum││Optimism│
   │  (1)   ││ (137)  ││ (8453) ││(42161) ││  (10)  │
   └────────┘└────────┘└────────┘└────────┘└────────┘

       F          G          H          I          J
   ┌────────┐┌────────┐┌────────┐┌────────┐┌────────┐
   │Avalanche│ Fantom │ Gnosis │  Celo  │ Linea  │
   │(43114) ││ (250)  ││ (100)  ││(42220) ││(59144) │
   └────────┘└────────┘└────────┘└────────┘└────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                      TOKEN RANK LAYER (Ranges)                            │
└──────────────────────────────────────────────────────────────────────────┘

  Chain A (Ethereum)          Chain B (Polygon)         Chain C (Base)
  ┌──────────────┐           ┌──────────────┐          ┌──────────────┐
  │ 1000-1999    │           │ 2000-2999    │          │ 3000-3999    │
  │              │           │              │          │              │
  │ 1000: WETH   │           │ 2000: WMATIC │          │ 3000: WETH   │
  │ 1001: USDC   │           │ 2001: WETH   │          │ 3001: USDC   │
  │ 1002: USDT   │           │ 2002: USDC   │          │ 3002: USDT   │
  │ 1003: DAI    │           │ 2003: USDC.e │          │ 3003: DAI    │
  │ 1004: WBTC   │           │ 2004: USDT   │          │ ...          │
  │ ...          │           │ ...          │          │              │
  └──────────────┘           └──────────────┘          └──────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                       DEX REGISTRY LAYER                                  │
└──────────────────────────────────────────────────────────────────────────┘

  Per-Chain DEX Registry: dexRouter[chainId][dexId] → address

  Polygon (137):
  ┌────┬──────────────┬──────────────────────────────────────────┐
  │ ID │    DEX       │           Router Address                 │
  ├────┼──────────────┼──────────────────────────────────────────┤
  │ 0  │ UNISWAP_V2   │ 0x... (Quickswap Router)                │
  │ 1  │ UNISWAP_V3   │ 0x... (UniV3 SwapRouter)                │
  │ 2  │ CURVE        │ 0x... (Curve Pool Address)              │
  │ 3  │ SUSHISWAP    │ 0x... (Sushi Router)                    │
  └────┴──────────────┴──────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────────┐
│                      TOKEN REGISTRY LAYER                                 │
└──────────────────────────────────────────────────────────────────────────┘

  tokenRegistry[chain][tokenId][tokenType] → address

  Example: Polygon (Chain.POLYGON)
  ┌─────────┬──────────────┬────────────────────────────────────┐
  │ TokenId │  TokenType   │        Address                     │
  ├─────────┼──────────────┼────────────────────────────────────┤
  │ WMATIC  │ WRAPPED (2)  │ 0x0d500B1d8E8eF31E21C99d1Db9A6444d│
  │ USDC    │ CANONICAL(0) │ 0x2791Bca1f2de4661ED88A30C99A7a94│
  │ USDC    │ BRIDGED (1)  │ 0x... (USDC.e)                    │
  │ WETH    │ BRIDGED (1)  │ 0x7ceB23fD6bC0adD59E62ac25578270c│
  └─────────┴──────────────┴────────────────────────────────────┘
```

---

## 3. Token Design Flow

```
╔══════════════════════════════════════════════════════════════════════════╗
║                        TOKEN RESOLUTION FLOW                              ║
╚══════════════════════════════════════════════════════════════════════════╝

TWO SYSTEMS: OmniArbDecoder (A-J + Rank) vs OmniArbExecutor (Enum + Type)

┌──────────────────────────────────────────────────────────────────────────┐
│            SYSTEM 1: OmniArbDecoder (A-J Token Ranks)                    │
└──────────────────────────────────────────────────────────────────────────┘

  Input: chainEnum (A-J) + tokenRank (uint16)
         ↓
  Step 1: Validate chainEnum matches current chain
         A-J → Chain ID lookup
         ↓
  Step 2: Resolve token address from rank
         tokenRank → rankToToken[tokenRank]
         ↓
  Step 3: Apply USDC normalization
         If bridged USDC → return canonical USDC
         Else → return original token
         ↓
  Output: Token Address

  Example (Polygon):
    Input:  chainEnum = 'B', tokenRank = 2003
    Step 1: 'B' → 137 (Polygon) ✓
    Step 2: 2003 → 0x... (USDC.e address)
    Step 3: USDC.e → 0x... (Canonical USDC)
    Output: Canonical USDC address

┌──────────────────────────────────────────────────────────────────────────┐
│            SYSTEM 2: OmniArbExecutor (Token Enum + Type)                 │
└──────────────────────────────────────────────────────────────────────────┘

  Input: chain (enum), tokenId (enum), tokenType (enum)
         ↓
  Step 1: Get current chain from block.chainid
         block.chainid → Chain enum
         ↓
  Step 2: Resolve token address from registry
         tokenRegistry[chain][tokenId][tokenType] → address
         ↓
  Output: Token Address

  Example (Polygon):
    Input:  tokenId = Token.USDC, tokenType = TokenType.BRIDGED
    Step 1: block.chainid = 137 → Chain.POLYGON
    Step 2: tokenRegistry[POLYGON][USDC][BRIDGED] → 0x... (USDC.e)
    Output: USDC.e address
```

---

## 4. Route Execution Flow

```
╔══════════════════════════════════════════════════════════════════════════╗
║                         ROUTE EXECUTION FLOW                              ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│  Example: 3-Hop Arbitrage Route on Polygon                               │
│  Loan: 10,000 USDT                                                       │
└──────────────────────────────────────────────────────────────────────────┘

         Flashloan Borrow
         10,000 USDT
              │
              ▼
    ┌─────────────────────┐
    │  Hop 1: UniV2       │
    │  USDT → WMATIC      │
    │  Protocol: 1        │
    │  Router: Quickswap  │
    │  Extra: 0x          │
    └──────────┬──────────┘
               │ Output: X WMATIC
               ▼
    ┌─────────────────────┐
    │  Hop 2: UniV3       │
    │  WMATIC → USDC      │
    │  Protocol: 2        │
    │  Router: UniV3      │
    │  Extra: fee=500     │
    └──────────┬──────────┘
               │ Output: Y USDC
               ▼
    ┌─────────────────────┐
    │  Hop 3: Curve       │
    │  USDC → USDT        │
    │  Protocol: 3        │
    │  Pool: Aave Pool    │
    │  Extra: i=0, j=1    │
    └──────────┬──────────┘
               │ Output: Z USDT
               ▼
         Repay Flashloan
         10,000 USDT + Fee
              │
              ▼
         Profit = Z - (10,000 + Fee)
         (Retained in contract)

Token Flow:
  currentToken = loanToken (USDT)
  └→ Hop 1: currentToken → tokenOutPath[0] (WMATIC)
     └→ Hop 2: currentToken → tokenOutPath[1] (USDC)
        └→ Hop 3: currentToken → tokenOutPath[2] (USDT)
           └→ finalToken = USDT
```

---

## 5. Dual Encoding Modes

```
╔══════════════════════════════════════════════════════════════════════════╗
║                    RAW_ADDRESSES vs REGISTRY_ENUMS                        ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│                MODE 0: RAW_ADDRESSES (Explicit)                           │
└──────────────────────────────────────────────────────────────────────────┘

  Payload Structure:
  ┌──────────────────────────────────────────────────────────────┐
  │ RouteEncoding: 0 (RAW_ADDRESSES)                             │
  ├──────────────────────────────────────────────────────────────┤
  │ protocols:      [1, 2, 3]         (uint8[])                  │
  │ routersOrPools: [0xAAA..., 0xBBB..., 0xCCC...] (address[])  │
  │ tokenOutPath:   [0xDDD..., 0xEEE..., 0xFFF...] (address[])  │
  │ extra:          [0x, feeBytes, indicesBytes]   (bytes[])     │
  └──────────────────────────────────────────────────────────────┘
                           ↓
  On-Chain Processing:
  ┌──────────────────────────────────────────────────────────────┐
  │ Direct Usage (No Registry Lookup)                            │
  │ • Use provided router addresses directly                     │
  │ • Use provided token addresses directly                      │
  │ • Fast execution                                             │
  └──────────────────────────────────────────────────────────────┘

  Pros: ✓ Faster execution        Cons: ✗ Larger calldata
        ✓ No registry setup              ✗ No centralized control
        ✓ Flexible addresses             ✗ Address changes need new tx

┌──────────────────────────────────────────────────────────────────────────┐
│                MODE 1: REGISTRY_ENUMS (Resolved)                          │
└──────────────────────────────────────────────────────────────────────────┘

  Payload Structure:
  ┌──────────────────────────────────────────────────────────────┐
  │ RouteEncoding: 1 (REGISTRY_ENUMS)                            │
  ├──────────────────────────────────────────────────────────────┤
  │ protocols:       [1, 2, 3]       (uint8[])                   │
  │ dexIds:          [0, 1, 2]       (uint8[])                   │
  │ tokenOutIds:     [4, 1, 2]       (uint8[])                   │
  │ tokenOutTypes:   [0, 0, 0]       (uint8[])                   │
  │ extra:           [0x, feeBytes, indicesBytes] (bytes[])      │
  └──────────────────────────────────────────────────────────────┘
                           ↓
  On-Chain Processing:
  ┌──────────────────────────────────────────────────────────────┐
  │ Registry Lookup Required                                      │
  │ • router = dexRouter[chainId][dexId]                         │
  │ • token = tokenRegistry[chainId][tokenId][tokenType]         │
  │ • Centralized management                                     │
  └──────────────────────────────────────────────────────────────┘

  Pros: ✓ Smaller calldata        Cons: ✗ Registry setup needed
        ✓ Centralized governance         ✗ Slightly slower (lookup)
        ✓ Easy address updates           ✗ Registry must be maintained
```

---

## 6. Token Type Classification

```
╔══════════════════════════════════════════════════════════════════════════╗
║                      TOKEN TYPE CLASSIFICATION                            ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│                        Type 0: CANONICAL                                  │
│                     (Native to the chain)                                 │
└──────────────────────────────────────────────────────────────────────────┘

  Examples:
    Ethereum:  USDC, USDT, DAI (originated on Ethereum)
    Polygon:   Native Polygon USDC (Circle-issued)
    Arbitrum:  Native Arbitrum USDC (Circle-issued)
    Base:      Native Base USDC (Circle-issued)

  Characteristics:
    ✓ Highest liquidity
    ✓ Most trusted
    ✓ Direct issuance
    ✓ Primary trading pairs

┌──────────────────────────────────────────────────────────────────────────┐
│                        Type 1: BRIDGED                                    │
│                   (Bridged from another chain)                            │
└──────────────────────────────────────────────────────────────────────────┘

  Examples:
    Polygon:   USDC.e (bridged from Ethereum), WETH (bridged)
    Arbitrum:  USDC.e (bridged from Ethereum)
    Optimism:  USDC.e (bridged from Ethereum)
    Avalanche: USDC.e (bridged from Ethereum)

  Characteristics:
    ⚠ Lower liquidity than canonical
    ⚠ Depends on bridge security
    ⚠ May trade at slight discount
    ⚠ Migration path to canonical

┌──────────────────────────────────────────────────────────────────────────┐
│                        Type 2: WRAPPED                                    │
│                  (Wrapped native gas token)                               │
└──────────────────────────────────────────────────────────────────────────┘

  Examples:
    Ethereum:  WETH (Wrapped ETH)
    Polygon:   WMATIC (Wrapped MATIC)
    BSC:       WBNB (Wrapped BNB)
    Avalanche: WAVAX (Wrapped AVAX)
    Fantom:    WFTM (Wrapped FTM)

  Characteristics:
    ✓ 1:1 peg with native token
    ✓ ERC20 compatible
    ✓ Highest liquidity
    ✓ Most trading pairs

USDC Normalization Example:
  ┌───────────────────────────────────────────────────┐
  │  Polygon: USDC.e (BRIDGED) → USDC (CANONICAL)    │
  │  Reason: Prevent mixing non-fungible variants     │
  └───────────────────────────────────────────────────┘
```

---

## 7. Security Architecture

```
╔══════════════════════════════════════════════════════════════════════════╗
║                        SECURITY ARCHITECTURE                              ║
╚══════════════════════════════════════════════════════════════════════════╝

┌──────────────────────────────────────────────────────────────────────────┐
│                      MULTI-LAYER SECURITY MODEL                           │
└──────────────────────────────────────────────────────────────────────────┘

Layer 1: Access Control
├─ Owner-only execution (Ownable)
├─ Owner-only registry configuration
└─ Emergency withdrawal functions

Layer 2: Validation
├─ Chain enum validation (must match current chain)
├─ Token rank validation (must be configured)
├─ Expiry validation (timestamp check)
├─ Nonce uniqueness (prevent replay)
├─ Route registry hash verification (optional)
└─ Profit validation (minProfitBps check)

Layer 3: Flashloan Security
├─ Callback authentication (validate msg.sender)
├─ Reentrancy guard (ReentrancyGuard)
└─ Profit validation (ensure repayment + profit)

Layer 4: Token Security
├─ SafeERC20 usage (safe transfers)
├─ Zero address checks
├─ USDC normalization (prevent variant mixing)
└─ Token type validation

Layer 5: Execution Security
├─ Array length validation (all arrays must match)
├─ Zero amount checks (validate swap outputs)
├─ Route length limits (max 5 hops)
├─ Slippage protection (deadline parameter)
└─ Gas optimization (avoid excessive operations)

Immutability Guarantees:
┌────────────────────────────────────────────────────────┐
│ NEVER CHANGE:                                          │
│ • Chain enum letters (A-J mapping)                    │
│ • Enum value ordering (declaration order = value)     │
│ • Token rank ranges (1000-1999, 2000-2999, ...)       │
│ • STATIC_ORDER sequence (append only, never reorder)  │
└────────────────────────────────────────────────────────┘
```

---

**Last Updated**: 2025-12-22  
**Version**: 1.0.0  
**Status**: Complete ✅
