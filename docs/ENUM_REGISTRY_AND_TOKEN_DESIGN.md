# Titan Enum Registry & Token Design Documentation

## Table of Contents
1. [System Overview](#system-overview)
2. [Enum Registry System](#enum-registry-system)
3. [Token Design & Token ID System](#token-design--token-id-system)
4. [System Architecture](#system-architecture)
5. [Integration Examples](#integration-examples)

---

## System Overview

Titan uses a sophisticated enum-based registry system for cross-chain arbitrage execution. The system features:

- **Chain Enum System**: A-J letter-based chain identification
- **Token Rank System**: Deterministic token identification using ranges
- **Multi-Protocol Support**: UniV2, UniV3, Curve DEX protocols
- **Dual Encoding**: RAW_ADDRESSES and REGISTRY_ENUMS modes

---

## Enum Registry System

### 1. Chain Enum Registry (A-J System)

The OmniArbDecoder uses **bytes1 ASCII letters (A-J)** to represent blockchain networks:

```
┌─────────────────────────────────────────────────────────────┐
│             CHAIN ENUM MAPPING (A-J System)                 │
├────────┬─────────────────┬──────────┬─────────────────────┤
│ Letter │ Chain           │ Chain ID │ Token Range         │
├────────┼─────────────────┼──────────┼─────────────────────┤
│   A    │ Ethereum        │     1    │ 1000-1999           │
│   B    │ Polygon         │   137    │ 2000-2999           │
│   C    │ Base            │  8453    │ 3000-3999           │
│   D    │ Arbitrum        │ 42161    │ 4000-4999           │
│   E    │ Optimism        │    10    │ 5000-5999           │
│   F    │ Avalanche       │ 43114    │ 6000-6999           │
│   G    │ Fantom          │   250    │ 7000-7999           │
│   H    │ Gnosis          │   100    │ 8000-8999           │
│   I    │ Celo            │ 42220    │ 9000-9999           │
│   J    │ Linea           │ 59144    │ 10000-10999         │
└────────┴─────────────────┴──────────┴─────────────────────┘
```

**Implementation (Solidity):**
```solidity
// OmniArbDecoder.sol
mapping(bytes1 => uint256) public enumToChainId;

// Initialization
enumToChainId[bytes1("A")] = 1;        // Ethereum
enumToChainId[bytes1("B")] = 137;      // Polygon
enumToChainId[bytes1("C")] = 8453;     // Base
// ... etc.
```

**Implementation (Python):**
```python
# core/enum_matrix.py
from enum import IntEnum

class ChainID(IntEnum):
    ETHEREUM = 1
    POLYGON = 137
    ARBITRUM = 42161
    OPTIMISM = 10
    BASE = 8453
    BSC = 56
    AVALANCHE = 43114
    FANTOM = 250
    LINEA = 59144
    SCROLL = 534352
    MANTLE = 5000
    ZKSYNC = 324
    CELO = 42220
    OPBNB = 204
```

**Key Rules:**
- ✅ Fixed alphabetical ordering (A-J)
- ✅ Append-only (never reassign letters)
- ✅ Stored as `bytes1` in payload (not `uint8`)
- ✅ Validates chain match on-chain

---

### 2. DEX Enum Registry

The OmniArbExecutor uses numeric enums for DEX identification:

```
┌─────────────────────────────────────────────────────────────┐
│                    DEX ENUM REGISTRY                         │
├────────┬─────────────────────────┬────────────────────────┤
│   ID   │ DEX Name                │ Protocol Type          │
├────────┼─────────────────────────┼────────────────────────┤
│   0    │ UNISWAP_V2 / UniV2      │ UniswapV2-style       │
│   1    │ UNISWAP_V3 / UniV3      │ Uniswap V3            │
│   2    │ CURVE                   │ Curve pools           │
│   3    │ SUSHISWAP               │ UniswapV2-style       │
│   4    │ QUICKSWAP               │ UniswapV2-style       │
│   5    │ PANCAKESWAP             │ UniswapV2-style       │
│   6    │ BALANCER                │ Balancer pools        │
│   7    │ TRADER_JOE              │ UniswapV2-style       │
│   8    │ SPOOKYSWAP              │ UniswapV2-style       │
│   9    │ AERODROME               │ Solidly-style         │
│   10   │ VELODROME               │ Solidly-style         │
└────────┴─────────────────────────┴────────────────────────┘
```

**Mapping Structure:**
```solidity
// OmniArbExecutor.sol
mapping(uint256 => mapping(uint8 => address)) public dexRouter;

// Usage: dexRouter[chainId][dexId] = router address
dexRouter[137][0] = QUICKSWAP_ROUTER;  // Polygon, UniV2
dexRouter[137][1] = UNIV3_ROUTER;      // Polygon, UniV3
dexRouter[137][2] = CURVE_POOL;        // Polygon, Curve
```

---

### 3. Protocol ID System

Each swap hop specifies a protocol identifier:

```
┌─────────────────────────────────────────────────────────────┐
│                  PROTOCOL ID SYSTEM                          │
├────────┬─────────────────┬────────────────────────────────┤
│   ID   │ Protocol        │ Extra Data Format              │
├────────┼─────────────────┼────────────────────────────────┤
│   1    │ UniV2           │ 0x (empty)                     │
│   2    │ UniV3           │ abi.encode(uint24 fee)         │
│   3    │ Curve           │ abi.encode(int128 i, int128 j) │
└────────┴─────────────────┴────────────────────────────────┘
```

**Protocol-Specific Details:**

- **UniV2 (Protocol 1)**
  - Uses: Quickswap, SushiSwap, PancakeSwap, etc.
  - Method: `swapExactTokensForTokens()`
  - Extra Data: Empty bytes `0x`

- **UniV3 (Protocol 2)**
  - Uses: Uniswap V3 routers
  - Method: `exactInputSingle()`
  - Extra Data: `abi.encode(uint24 fee)`
  - Common fees: 500 (0.05%), 3000 (0.3%), 10000 (1%)

- **Curve (Protocol 3)**
  - Uses: Curve pools directly
  - Method: `exchange(int128, int128, uint256, uint256)`
  - Extra Data: `abi.encode(int128 i, int128 j)` (pool indices)

---

## Token Design & Token ID System

### 1. Token Rank System

Each chain has a **reserved range** for token ranks:

```
┌──────────────────────────────────────────────────────────────────────┐
│                    TOKEN RANK ALLOCATION SYSTEM                      │
├────────┬─────────────────┬─────────────┬──────────────────────────┤
│ Chain  │ Letter          │ Range       │ Examples                 │
├────────┼─────────────────┼─────────────┼──────────────────────────┤
│ ETH    │ A               │ 1000-1999   │ 1000=WETH, 1001=USDC     │
│ POL    │ B               │ 2000-2999   │ 2000=WMATIC, 2001=WETH   │
│ BASE   │ C               │ 3000-3999   │ 3000=WETH, 3001=USDC     │
│ ARB    │ D               │ 4000-4999   │ 4000=WETH, 4001=USDC     │
│ OPT    │ E               │ 5000-5999   │ 5000=WETH, 5001=USDC     │
│ AVAX   │ F               │ 6000-6999   │ 6000=WAVAX, 6001=USDC    │
│ FTM    │ G               │ 7000-7999   │ 7000=WFTM, 7001=USDC     │
│ GNO    │ H               │ 8000-8999   │ 8000=WXDAI, 8001=USDC    │
│ CELO   │ I               │ 9000-9999   │ 9000=CELO, 9001=USDC     │
│ LINEA  │ J               │ 10000-10999 │ 10000=WETH, 10001=USDC   │
└────────┴─────────────────┴─────────────┴──────────────────────────┘
```

**Token Rank Formula:**
```
rank = rangeStart(chainEnum) + index + 1
```

where:
- `rangeStart(A) = 1000`
- `rangeStart(B) = 2000`
- `index` = position in STATIC_ORDER array for that chain

**Example - Polygon (Chain B):**
```
STATIC_ORDER = [WMATIC, WETH, USDC, USDC.e, USDT, DAI, ...]

Token Ranks:
- WMATIC → 2000 (2000 + 0)
- WETH   → 2001 (2000 + 1)
- USDC   → 2002 (2000 + 2)
- USDC.e → 2003 (2000 + 3)
- USDT   → 2004 (2000 + 4)
```

---

### 2. Token Type System

Tokens are classified by their nature on each chain:

```
┌─────────────────────────────────────────────────────────────┐
│                   TOKEN TYPE ENUM                            │
├────────┬─────────────────┬────────────────────────────────┤
│   ID   │ Type            │ Description                    │
├────────┼─────────────────┼────────────────────────────────┤
│   0    │ CANONICAL       │ Native to the chain            │
│   1    │ BRIDGED         │ Bridged version (e.g., USDC.e) │
│   2    │ WRAPPED         │ Wrapped native (WETH, WMATIC)  │
└────────┴─────────────────┴────────────────────────────────┘
```

**Examples by Chain:**

**Ethereum (Chain A):**
- WETH: WRAPPED (native ETH wrapped)
- USDC: CANONICAL (native USDC)
- USDT: CANONICAL (native USDT)

**Polygon (Chain B):**
- WMATIC: WRAPPED (native MATIC wrapped)
- USDC: CANONICAL (native Polygon USDC)
- USDC.e: BRIDGED (bridged from Ethereum)
- WETH: BRIDGED (bridged from Ethereum)

**Arbitrum (Chain D):**
- WETH: WRAPPED (native ETH wrapped)
- USDC: CANONICAL (native Arbitrum USDC)
- USDC.e: BRIDGED (bridged USDC)

---

### 3. Token ID Enum (OmniArbExecutor)

The executor contract uses a unified token enum:

```
┌─────────────────────────────────────────────────────────────┐
│              TOKEN ENUM (OmniArbExecutor)                    │
├────────┬──────────────────────────┬──────────────────────┤
│   ID   │ Token Symbol             │ Category             │
├────────┼──────────────────────────┼──────────────────────┤
│   0    │ WETH                     │ Native Wrapped       │
│   1    │ WMATIC                   │ Native Wrapped       │
│   2    │ WBNB                     │ Native Wrapped       │
│   3    │ WAVAX                    │ Native Wrapped       │
│   4    │ WFTM                     │ Native Wrapped       │
│   5    │ USDC                     │ Stablecoin (native)  │
│   6    │ USDT                     │ Stablecoin (native)  │
│   7    │ DAI                      │ Stablecoin (native)  │
│   8    │ FRAX                     │ Stablecoin (native)  │
│   9    │ USDC_BRIDGED_POLYGON     │ Bridged Stablecoin   │
│   10   │ USDT_BRIDGED_POLYGON     │ Bridged Stablecoin   │
│   11   │ DAI_BRIDGED_POLYGON      │ Bridged Stablecoin   │
│   12   │ USDC_BRIDGED_ARBITRUM    │ Bridged Stablecoin   │
│   13   │ USDT_BRIDGED_ARBITRUM    │ Bridged Stablecoin   │
│   14   │ DAI_BRIDGED_ARBITRUM     │ Bridged Stablecoin   │
│   15   │ USDC_BRIDGED_OPTIMISM    │ Bridged Stablecoin   │
│   16   │ USDT_BRIDGED_OPTIMISM    │ Bridged Stablecoin   │
│   17   │ DAI_BRIDGED_OPTIMISM     │ Bridged Stablecoin   │
│   18   │ USDC_BRIDGED_BASE        │ Bridged Stablecoin   │
│   19   │ WETH_BRIDGED_POLYGON     │ Bridged ETH          │
│   20   │ WETH_BRIDGED_ARBITRUM    │ Bridged ETH          │
│   21   │ WETH_BRIDGED_OPTIMISM    │ Bridged ETH          │
│   22   │ WETH_BRIDGED_BASE        │ Bridged ETH          │
│   23   │ WETH_BRIDGED_AVALANCHE   │ Bridged ETH          │
│   24   │ WBTC                     │ Bridged BTC          │
│   25   │ WBTC_BRIDGED_POLYGON     │ Bridged BTC          │
│   26   │ WBTC_BRIDGED_ARBITRUM    │ Bridged BTC          │
│   27   │ LINK                     │ Other Major Token    │
│   28   │ AAVE                     │ Other Major Token    │
│   29   │ CRV                      │ Other Major Token    │
│   30   │ BAL                      │ Other Major Token    │
│   31   │ SUSHI                    │ Other Major Token    │
└────────┴──────────────────────────┴──────────────────────┘
```

**Token Registry Mapping:**
```solidity
// OmniArbExecutor.sol
mapping(Chain => mapping(Token => address)) public tokenRegistry;

// Usage: tokenRegistry[chain][token] = address
tokenRegistry[Chain.POLYGON][Token.WMATIC] = 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270;
tokenRegistry[Chain.POLYGON][Token.USDC] = 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174;
```

---

### 4. USDC Normalization System

The decoder supports normalizing bridged USDC variants to canonical USDC:

```
┌─────────────────────────────────────────────────────────────┐
│               USDC NORMALIZATION MAPPING                     │
├────────────────┬──────────────────┬─────────────────────────┤
│ Chain          │ Bridged USDC     │ Canonical USDC          │
├────────────────┼──────────────────┼─────────────────────────┤
│ Polygon        │ USDC.e           │ USDC                    │
│ Arbitrum       │ USDC.e           │ USDC                    │
│ Optimism       │ USDC.e           │ USDC                    │
│ Avalanche      │ USDC.e           │ USDC                    │
│ Base           │ USDbC            │ USDC                    │
└────────────────┴──────────────────┴─────────────────────────┘
```

**Implementation:**
```solidity
// OmniArbDecoder.sol
mapping(uint256 => mapping(address => address)) public bridgedToCanonical;

// Configure bridged → canonical mapping
bridgedToCanonical[137][USDC_E_ADDRESS] = USDC_ADDRESS;

// Automatic resolution
function resolveToken(uint16 tokenRank) external view returns (address token) {
    token = rankToToken[tokenRank];
    address canonical = bridgedToCanonical[block.chainid][token];
    if (canonical != address(0)) {
        return canonical;
    }
    return token;
}
```

---

## System Architecture

### 1. Overall System Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     TITAN ARBITRAGE SYSTEM FLOW                          │
└─────────────────────────────────────────────────────────────────────────┘

   ┌─────────────────┐
   │   Off-Chain     │
   │   Opportunity   │
   │   Detection     │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  Route Encoding │
   │  (RAW/REGISTRY) │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────┐
   │  execute() call │
   │  on Executor    │
   └────────┬────────┘
            │
            ▼
   ┌─────────────────────────────────────────┐
   │         FLASHLOAN SOURCES               │
   ├─────────────────────────────────────────┤
   │  ┌──────────────┐   ┌────────────────┐ │
   │  │  Aave V3     │   │  Balancer V3   │ │
   │  │ flashLoanSimple│ │  vault.unlock()│ │
   │  └──────┬───────┘   └───────┬────────┘ │
   └─────────┼───────────────────┼──────────┘
            │                   │
            └────────┬──────────┘
                     ▼
         ┌───────────────────────┐
         │  Flashloan Callback   │
         │  (executeOperation /  │
         │   onBalancerUnlock)   │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────┐
         │    _runRoute()        │
         │  Multi-Hop Execution  │
         └───────────┬───────────┘
                     │
                     ▼
         ┌───────────────────────────────────────┐
         │      Hop-by-Hop Swap Execution        │
         │  (via SwapHandler module)             │
         ├───────────────────────────────────────┤
         │  Hop 1: Token A → Token B (UniV2)     │
         │  Hop 2: Token B → Token C (UniV3)     │
         │  Hop 3: Token C → Token A (Curve)     │
         └───────────────────┬───────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │      Repay Flashloan + Fee            │
         └───────────────────┬───────────────────┘
                             │
                             ▼
         ┌───────────────────────────────────────┐
         │     Profit Retained in Contract       │
         │     (withdraw via withdraw())         │
         └───────────────────────────────────────┘
```

---

### 2. Contract Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    CONTRACT ARCHITECTURE                              │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                       OmniArbExecutor.sol                             │
│  (Main Execution Brain - Owns entire arbitrage lifecycle)            │
├──────────────────────────────────────────────────────────────────────┤
│  • Flashloan Management (Aave V3 / Balancer V3)                      │
│  • Route Orchestration (Multi-hop execution)                         │
│  • Registry Management (DEX routers, Tokens)                         │
│  • Profit Collection & Withdrawal                                    │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            │ inherits
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                       SwapHandler.sol                                 │
│  (System-Wide Swap Primitive - Reusable across all modules)          │
├──────────────────────────────────────────────────────────────────────┤
│  • Protocol 1: UniV2 swap execution                                  │
│  • Protocol 2: UniV3 swap execution                                  │
│  • Protocol 3: Curve swap execution                                  │
│  • SafeERC20 token approvals                                         │
└───────────────────────────┬──────────────────────────────────────────┘
                            │
                            │ uses
                            ▼
┌──────────────────────────────────────────────────────────────────────┐
│                     Standardized Interfaces                           │
├──────────────────────────────────────────────────────────────────────┤
│  IAaveV3.sol    │ Aave V3 flashloan interfaces                       │
│  IB3.sol        │ Balancer V3 vault interfaces                       │
│  IUniV2.sol     │ UniswapV2 router interface                         │
│  IUniV3.sol     │ UniswapV3 router interface                         │
│  ICurve.sol     │ Curve pool interface                               │
└──────────────────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│                       OmniArbDecoder.sol                              │
│  (A-J Chain Enum & Token Rank Decoder - Separate deployment)         │
├──────────────────────────────────────────────────────────────────────┤
│  • Chain enum validation (A-J → Chain ID)                            │
│  • Token rank resolution (rank → address)                            │
│  • USDC normalization (bridged → canonical)                          │
│  • Payload validation (expiry, nonce, profit)                        │
└──────────────────────────────────────────────────────────────────────┘
```

---

### 3. Route Encoding Dual-Mode Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│               ROUTE ENCODING: TWO MODES                               │
└──────────────────────────────────────────────────────────────────────┘

MODE 0: RAW_ADDRESSES
═══════════════════════
┌────────────────────────────────────────────────────────────┐
│  Off-Chain Encoding                                        │
├────────────────────────────────────────────────────────────┤
│  protocols:       [1, 2, 3]                                │
│  routersOrPools:  [0xRouter1, 0xRouter2, 0xPool]           │
│  tokenOutPath:    [0xWETH, 0xUSDC, 0xUSDT]                 │
│  extra:           [0x, fee_bytes, indices_bytes]           │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│  On-Chain Execution                                        │
├────────────────────────────────────────────────────────────┤
│  • Direct address usage (no registry lookup)               │
│  • Faster execution                                        │
│  • Larger calldata size                                    │
└────────────────────────────────────────────────────────────┘

MODE 1: REGISTRY_ENUMS
═══════════════════════
┌────────────────────────────────────────────────────────────┐
│  Off-Chain Encoding                                        │
├────────────────────────────────────────────────────────────┤
│  protocols:       [1, 2, 3]                                │
│  dexIds:          [0, 1, 2]  (QUICKSWAP, UNIV3, CURVE)     │
│  tokenOutIds:     [4, 1, 2]  (WETH, USDC, USDT)            │
│  tokenOutTypes:   [0, 0, 0]  (CANONICAL, CANONICAL, ...)   │
│  extra:           [0x, fee_bytes, indices_bytes]           │
└────────────────────────────────────────────────────────────┘
                       │
                       ▼
┌────────────────────────────────────────────────────────────┐
│  On-Chain Execution                                        │
├────────────────────────────────────────────────────────────┤
│  • Registry lookup:                                        │
│    router = dexRouter[chainId][dexId]                      │
│    token = tokenRegistry[chainId][tokenId][tokenType]      │
│  • Smaller calldata size                                   │
│  • Centralized governance via registry                     │
└────────────────────────────────────────────────────────────┘
```

**When to use each mode:**

- **RAW_ADDRESSES**: 
  - Fast execution needed
  - One-off routes
  - Testing/development
  
- **REGISTRY_ENUMS**:
  - Production deployment
  - Centralized governance
  - Reduced calldata costs
  - Consistent address management

---

### 4. Data Flow Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                    DATA FLOW THROUGH SYSTEM                           │
└──────────────────────────────────────────────────────────────────────┘

Off-Chain Components:
┌────────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Python Brain      │───▶│ Aggregator       │───▶│ Route Builder   │
│  (ml/brain.py)     │    │ Selector         │    │ (execution/)    │
│  • Opportunity     │    │ • DEX selection  │    │ • Encode route  │
│    detection       │    │ • Price routing  │    │ • Build payload │
│  • ML predictions  │    │ • Gas estimation │    │                 │
└────────────────────┘    └──────────────────┘    └────────┬────────┘
                                                            │
                                                            ▼
On-Chain Execution:                              ┌──────────────────┐
                                                 │  Transaction     │
                                                 │  Submission      │
                                                 └────────┬─────────┘
                                                          │
                                                          ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    OmniArbExecutor.execute()                          │
├──────────────────────────────────────────────────────────────────────┤
│  Input:                                                               │
│    • flashSource (0=Aave, 1=Balancer)                                │
│    • loanToken (address)                                             │
│    • loanAmount (uint256)                                            │
│    • routeData (bytes) ─────────┐                                    │
└─────────────────────────────────┼────────────────────────────────────┘
                                  │
                ┌─────────────────┴─────────────────┐
                ▼                                   ▼
        [RAW_ADDRESSES]                     [REGISTRY_ENUMS]
        Decode addresses                    Resolve from registry
                │                                   │
                └───────────────┬───────────────────┘
                                ▼
                    ┌─────────────────────┐
                    │   _runRoute()       │
                    │   Loop over hops    │
                    └──────────┬──────────┘
                               │
                ┌──────────────┴──────────────┐
                ▼                             ▼
        ┌───────────────┐            ┌───────────────┐
        │ Hop 1: Swap   │───────────▶│ Hop 2: Swap   │───────▶ ...
        │ via SwapHandler│            │ via SwapHandler│
        └───────────────┘            └───────────────┘
                                               │
                                               ▼
                                    ┌──────────────────┐
                                    │  Final Token     │
                                    │  Balance Check   │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  Repay Flashloan │
                                    └────────┬─────────┘
                                             │
                                             ▼
                                    ┌──────────────────┐
                                    │  Profit Retained │
                                    └──────────────────┘
```

---

## Integration Examples

### Example 1: Encoding with A-J Chain System

```javascript
// OmniArbDecoder payload encoding (using A-J system)
const ethers = require('ethers');
const abi = ethers.AbiCoder.defaultAbiCoder();

function toBytes1(str) {
  return ethers.encodeBytes32String(str).slice(0, 4);
}

// Encode payload for Polygon (Chain B)
const payload = abi.encode(
  ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
  [
    toBytes1("B"),                           // Chain B = Polygon
    2001,                                     // Token rank: WETH on Polygon
    ethers.parseEther("1"),                  // 1 WETH
    "0x",                                     // routeParams
    100,                                      // 1% min profit (100 bps)
    Math.floor(Date.now() / 1000) + 3600,    // Expiry: 1 hour
    receiverAddress,                          // Receiver
    ethers.ZeroHash,                         // Route registry hash
    1                                         // Nonce
  ]
);

// Decode on-chain
const decoded = await decoder.decodePayload(payload);
console.log("Chain Enum:", decoded.chainEnum);  // 'B'
console.log("Token Rank:", decoded.tokenRank);  // 2001
```

---

### Example 2: RAW_ADDRESSES Route Encoding

```javascript
// 3-hop arbitrage on Polygon using RAW_ADDRESSES
const RAW = 0;

const protocols = [1, 2, 3];  // UniV2 → UniV3 → Curve

const routersOrPools = [
  "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  // Quickswap router
  "0xE592427A0AEce92De3Edee1F18E0157C05861564",  // UniV3 SwapRouter
  "0x445FE580eF8d70FF569aB36e80c647af338db351"   // Curve pool (aave)
];

const tokenOutPath = [
  "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  // WMATIC
  "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  // USDC
  "0xc2132D05D31c914a87C6611C10748AEb04B58e8F"   // USDT
];

const extra = [
  "0x",                                  // UniV2: empty
  abi.encode(["uint24"], [500]),         // UniV3: 0.05% fee
  abi.encode(["int128","int128"], [0,1]) // Curve: indices 0→1
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "address[]", "address[]", "bytes[]"],
  [RAW, protocols, routersOrPools, tokenOutPath, extra]
);

// Execute
await executor.execute(
  0,                      // Aave V3 flashloan
  USDT_ADDRESS,          // Loan token
  ethers.parseUnits("10000", 6),  // 10,000 USDT
  routeData
);
```

---

### Example 3: REGISTRY_ENUMS Route Encoding

```javascript
// Same route but using REGISTRY_ENUMS
const REG = 1;

const protocols = [1, 2, 3];
const dexIds = [3, 1, 5];          // QUICKSWAP, UNIV3, CURVE (enum IDs)
const tokenOutIds = [1, 1, 2];     // WMATIC, USDC, USDT (Token enum IDs)
const tokenOutTypes = [2, 0, 0];   // WRAPPED, CANONICAL, CANONICAL

const extra = [
  "0x",
  abi.encode(["uint24"], [500]),
  abi.encode(["int128","int128"], [0,1])
];

const routeData = abi.encode(
  ["uint8", "uint8[]", "uint8[]", "uint8[]", "uint8[]", "bytes[]"],
  [REG, protocols, dexIds, tokenOutIds, tokenOutTypes, extra]
);

// Must configure registry first (owner only):
await executor.setDexRouter(137, 3, QUICKSWAP_ROUTER);
await executor.setDexRouter(137, 1, UNIV3_ROUTER);
await executor.setDexRouter(137, 5, CURVE_POOL);
await executor.setToken(137, 1, 2, WMATIC_ADDRESS);  // TokenId 1, Type 2 (WRAPPED)
await executor.setToken(137, 1, 0, USDC_ADDRESS);    // TokenId 1, Type 0 (CANONICAL)
await executor.setToken(137, 2, 0, USDT_ADDRESS);    // TokenId 2, Type 0 (CANONICAL)

// Execute with same parameters
await executor.execute(0, USDT_ADDRESS, loanAmount, routeData);
```

---

### Example 4: Python Integration

```python
# core/enum_matrix.py integration
from core.enum_matrix import ChainID, ProviderManager

# Get provider for a chain
provider = ProviderManager.get_provider(ChainID.POLYGON)
if provider:
    block_number = provider.eth.block_number
    print(f"Polygon block: {block_number}")

# Test connection to all chains
for chain_id in [ChainID.ETHEREUM, ChainID.POLYGON, ChainID.ARBITRUM]:
    ProviderManager.test_connection(chain_id)

# Get all active providers
providers = ProviderManager.get_all_providers()
for chain_id, provider in providers.items():
    print(f"Chain {chain_id}: Connected")
```

---

## Security Considerations

### 1. Enum Registry Security

- **Immutable Chain Enum**: Chain A-J mappings are set in constructor (cannot be changed)
- **Owner-Only Token Config**: Only contract owner can configure token ranks
- **Nonce Replay Protection**: Each nonce can only be used once
- **Expiry Validation**: Payloads must be executed before expiry timestamp

### 2. Token Security

- **USDC Normalization**: Prevents mixing non-fungible USDC variants
- **Zero Address Checks**: Validates token addresses are configured
- **Token Type Validation**: Ensures correct token type classification

### 3. Execution Security

- **Flash Loan Callback Auth**: Validates callback is from flashloan provider
- **Profit Validation**: Checks final amount covers loan + fee
- **Owner-Only Execution**: Only contract owner can trigger arbitrage
- **Reentrancy Protection**: Uses OpenZeppelin's ReentrancyGuard

---

## References

### Smart Contracts
- **OmniArbDecoder.sol**: `contracts/OmniArbDecoder.sol`
- **OmniArbExecutor.sol**: `contracts/OmniArbExecutor.sol`
- **SwapHandler.sol**: `contracts/modules/SwapHandler.sol`

### Documentation
- **Route Encoding Spec**: `contracts/RouteEncodingSpec.md`
- **System Architecture**: `contracts/SystemArchitecture.md`
- **OmniArb Matrix Design**: `docs/OMNIARB_MATRIX_DESIGN.md`
- **Canonical Specification**: `docs/CANONICAL_SPECIFICATION.md`

### Scripts
- **Deploy Decoder**: `scripts/deployDecoder.js`
- **Configure Token Ranks**: `scripts/configureTokenRanks.js`
- **Example Usage**: `scripts/exampleUsage.js`

### Python Core
- **Enum Matrix**: `core/enum_matrix.py`
- **Token Loader**: `core/token_loader.py`
- **Token Discovery**: `core/token_discovery.py`

---

**Last Updated**: 2025-12-22  
**Version**: 1.0.0  
**Status**: Complete ✅
