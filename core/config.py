import os
from dotenv import load_dotenv
load_dotenv()

# V3 Vault is deterministic (Same addr on all chains)
BALANCER_V3_VAULT = "0xbA1333333333a1BA1108E8412f11850A5C319bA9"

CHAINS = {
    137: {
        "name": "polygon",
        "rpc": os.getenv("RPC_POLYGON"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x445FE580eF8d70FF569aB36e80c647af338db351",  # Curve aave pool on Polygon
        "native": "MATIC"
    },
    42161: {
        "name": "arbitrum",
        "rpc": os.getenv("RPC_ARBITRUM"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x7544Fe3d184b6B55D6B36c3FCA1157eE0Ba30287",  # Curve tricrypto pool on Arbitrum
        "native": "ETH"
    }
    # Add remaining 8 chains here following the pattern
}

# DEX Router Registry - Maps DEX names to router contract addresses
DEX_ROUTERS = {
    # Polygon DEXs
    "QUICKSWAP": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",  # QuickSwap Router
    "SUSHI": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap Router on Polygon
    "APE": "0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607",  # ApeSwap Router on Polygon
    
    # Arbitrum DEXs  
    "CAMELOT": "0xc873fEcbd354f5A56E00E710B90EF4201db2448d",  # Camelot Router
    "SUSHI_ARB": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",  # SushiSwap Router on Arbitrum
}