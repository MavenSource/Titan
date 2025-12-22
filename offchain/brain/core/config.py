import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from offchain directory
ENV_PATH = Path(__file__).parent.parent / ".env"
load_dotenv(ENV_PATH)

# Shared directory paths
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
SHARED_DIR = PROJECT_ROOT / "shared"
SIGNALS_OUTGOING = SHARED_DIR / "signals" / "outgoing"
SIGNALS_PROCESSED = SHARED_DIR / "signals" / "processed"
ABI_DIR = SHARED_DIR / "abi"

# Ensure directories exist
SIGNALS_OUTGOING.mkdir(parents=True, exist_ok=True)
SIGNALS_PROCESSED.mkdir(parents=True, exist_ok=True)
ABI_DIR.mkdir(parents=True, exist_ok=True)

# V3 Vault is deterministic (Same addr on all chains)
BALANCER_V3_VAULT = "0xbA1333333333a1BA1108E8412f11850A5C319bA9"

# Note: Address 0x0000000000000000000000000000000000000000 (zero address) indicates
# that a protocol/router is not available or not deployed on that specific chain.
# The system should check for zero addresses before attempting to interact with these protocols.

CHAINS = {
    1: {  # Ethereum Mainnet
        "name": "ethereum",
        "rpc": os.getenv("RPC_ETHEREUM"),
        "wss": os.getenv("WSS_ETHEREUM"),
        "aave_pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x99a58482BD75cbab83b27EC03CA68fF489b5788f",
        "native": "ETH"
    },
    137: {
        "name": "polygon",
        "rpc": os.getenv("RPC_POLYGON"),
        "wss": os.getenv("WSS_POLYGON"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x445FE580eF8d70FF569aB36e80c647af338db351",  # Curve aave pool on Polygon
        "native": "MATIC"
    },
    42161: {
        "name": "arbitrum",
        "rpc": os.getenv("RPC_ARBITRUM"),
        "wss": os.getenv("WSS_ARBITRUM"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x0000000000000000000000000000000000000000",  # Curve not deployed on Arbitrum
        "native": "ETH"
    },
    10: {
        "name": "optimism",
        "rpc": os.getenv("RPC_OPTIMISM"),
        "wss": os.getenv("WSS_OPTIMISM"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x0000000000000000000000000000000000000000",  # Curve not deployed on Optimism
        "native": "ETH"
    },
    8453: {
        "name": "base",
        "rpc": os.getenv("RPC_BASE"),
        "wss": os.getenv("WSS_BASE"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Base
        "uniswap_router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        "curve_router": "0x0000000000000000000000000000000000000000",  # Curve not deployed on Base
        "native": "ETH"
    },
    56: {
        "name": "bsc",
        "rpc": os.getenv("RPC_BSC"),
        "wss": os.getenv("WSS_BSC"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on BSC
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on BSC (use PancakeSwap)
        "pancake_router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "native": "BNB"
    },
    43114: {
        "name": "avalanche",
        "rpc": os.getenv("RPC_AVALANCHE"),
        "wss": os.getenv("WSS_AVALANCHE"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Avalanche (use TraderJoe)
        "traderjoe_router": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "native": "AVAX"
    },
    250: {
        "name": "fantom",
        "rpc": os.getenv("RPC_FANTOM"),
        "wss": None,
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Fantom
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Fantom (use SpookySwap)
        "spookyswap_router": "0xF491e7B69E4244ad4002BC14e878a34207E38c29",
        "native": "FTM"
    },
    59144: {
        "name": "linea",
        "rpc": os.getenv("RPC_LINEA"),
        "wss": os.getenv("WSS_LINEA"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Linea
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Linea
        "syncswap_router": "0x0000000000000000000000000000000000000000",  # SyncSwap not configured for Linea
        "native": "ETH"
    },
    534352: {
        "name": "scroll",
        "rpc": os.getenv("RPC_SCROLL"),
        "wss": os.getenv("WSS_SCROLL"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Scroll
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Scroll
        "native": "ETH"
    },
    5000: {
        "name": "mantle",
        "rpc": os.getenv("RPC_MANTLE"),
        "wss": os.getenv("WSS_MANTLE"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Mantle
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Mantle
        "native": "MNT"
    },
    324: {
        "name": "zksync",
        "rpc": os.getenv("RPC_ZKSYNC"),
        "wss": os.getenv("WSS_ZKSYNC"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on zkSync
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on zkSync (use SyncSwap)
        "syncswap_router": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
        "native": "ETH"
    },
    81457: {
        "name": "blast",
        "rpc": os.getenv("RPC_BLAST"),
        "wss": os.getenv("WSS_BLAST"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Blast
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Blast
        "thruster_router": "0x0000000000000000000000000000000000000000",  # Thruster not configured for Blast
        "native": "ETH"
    },
    42220: {
        "name": "celo",
        "rpc": os.getenv("RPC_CELO"),
        "wss": None,
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on Celo
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on Celo (use Ubeswap)
        "ubeswap_router": "0xE3D8bd6Aed4F159bc8000a9cD47CffDb95F96121",
        "native": "CELO"
    },
    204: {
        "name": "opbnb",
        "rpc": os.getenv("RPC_OPBNB"),
        "wss": os.getenv("WSS_OPBNB"),
        "aave_pool": "0x0000000000000000000000000000000000000000",  # Aave not available on opBNB
        "uniswap_router": "0x0000000000000000000000000000000000000000",  # Uniswap not deployed on opBNB
        "pancake_router": "0x0000000000000000000000000000000000000000",  # PancakeSwap not configured for opBNB
        "native": "BNB"
    }
    # Add remaining 8 chains here following the pattern
}

# DEX Router Registry - Maps chain IDs to DEX names and their router contract addresses
DEX_ROUTERS = {
    1: {  # Ethereum
        "UNIV2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2 Router
        "SUSHI": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",  # SushiSwap Router
    },
    137: {  # Polygon
        "QUICKSWAP": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickSwap Router
        "SUSHI": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap Router on Polygon
        "APE": "0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607",  # ApeSwap Router on Polygon
    },
    42161: {  # Arbitrum
        "CAMELOT": "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",  # Camelot Router
        "SUSHI": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap Router on Arbitrum
    },
    10: {  # Optimism
        "SUSHI": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap on Optimism
        "VELODROME": "0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858",  # Velodrome V2 Router
    },
    8453: {  # Base
        "SUSHI": "0x6BDED42c6DA8FBf0d2bA55B2fa120C5e0c8D7891",  # SushiSwap on Base
        "BASESWAP": "0x327Df1E6de05895d2ab08513aaDD9313Fe505d86",  # BaseSwap Router
    },
    56: {  # BSC
        "PANCAKE": "0x10ED43C718714eb63d5aA57B78B54704E256024E",  # PancakeSwap V2 Router
        "SUSHI": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap on BSC
        "APE": "0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7",  # ApeSwap on BSC
    },
    43114: {  # Avalanche
        "TRADERJOE": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",  # TraderJoe Router
        "SUSHI": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap on Avalanche
        "PANGOLIN": "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",  # Pangolin Router
    }
}

# ======================================================================
# LIFI BRIDGE CONFIGURATION - Intent-Based Cross-Chain Bridging
# ======================================================================

# Li.Fi supported chains (verified for intent-based bridging)
LIFI_SUPPORTED_CHAINS = [1, 137, 42161, 10, 8453, 56, 43114, 250, 59144, 534352, 5000, 324, 81457, 42220, 204]

# Intent-based bridge protocols (fast settlement via solvers)
INTENT_BASED_BRIDGES = {
    'across': {
        'name': 'Across Protocol',
        'typical_time_seconds': 30,  # 30 seconds average
        'max_time_seconds': 180,     # 3 minutes max
        'fee_range_bps': [5, 30],    # 0.05% - 0.30% fee
        'description': 'Fastest intent-based bridge using solver network'
    },
    'stargate': {
        'name': 'Stargate Finance',
        'typical_time_seconds': 60,  # 1 minute average
        'max_time_seconds': 300,     # 5 minutes max
        'fee_range_bps': [6, 50],    # 0.06% - 0.50% fee
        'description': 'Fast and reliable LayerZero-based bridge'
    },
    'hop': {
        'name': 'Hop Protocol',
        'typical_time_seconds': 120,  # 2 minutes average
        'max_time_seconds': 600,      # 10 minutes max
        'fee_range_bps': [10, 100],   # 0.10% - 1.00% fee (dynamic based on liquidity)
        'description': 'Popular bridge with good liquidity'
    }
}

# Traditional bridges (slower, validator-based)
TRADITIONAL_BRIDGES = {
    'synapse': {
        'name': 'Synapse Protocol',
        'typical_time_seconds': 900,   # 15 minutes
        'max_time_seconds': 1800,      # 30 minutes
        'fee_range_bps': [5, 20]
    },
    'cbridge': {
        'name': 'Celer cBridge',
        'typical_time_seconds': 1200,  # 20 minutes
        'max_time_seconds': 3600,      # 60 minutes
        'fee_range_bps': [10, 30]
    },
    'multichain': {
        'name': 'Multichain (Anyswap)',
        'typical_time_seconds': 600,   # 10 minutes
        'max_time_seconds': 1800,      # 30 minutes
        'fee_range_bps': [10, 50]
    }
}

# Bridge priority for arbitrage (prefer intent-based for speed)
BRIDGE_PRIORITY_FOR_ARBITRAGE = ['across', 'stargate', 'hop', 'synapse', 'cbridge', 'multichain']

# Maximum trade size per chain for intent-based bridges (USD)
# Larger trades may face liquidity constraints from solvers
MAX_INTENT_BASED_TRADE_SIZE = {
    'across': 100000,    # $100k max per trade
    'stargate': 250000,  # $250k max per trade
    'hop': 50000         # $50k max per trade
}