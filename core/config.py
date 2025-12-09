import os
from dotenv import load_dotenv
load_dotenv()

# V3 Vault is deterministic (Same addr on all chains)
BALANCER_V3_VAULT = "0xbA1333333333a1BA1108E8412f11850A5C319bA9"

CHAINS = {
    1: {
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
        "curve_router": "0x3c0FACA5cE5FBDA102C32F3C0F4e10e3131B2b2f",
        "native": "MATIC"
    },
    42161: {
        "name": "arbitrum",
        "rpc": os.getenv("RPC_ARBITRUM"),
        "wss": os.getenv("WSS_ARBITRUM"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x0000000000000000000000000000000000000000",
        "native": "ETH"
    },
    10: {
        "name": "optimism",
        "rpc": os.getenv("RPC_OPTIMISM"),
        "wss": os.getenv("WSS_OPTIMISM"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "curve_router": "0x0000000000000000000000000000000000000000",
        "native": "ETH"
    },
    8453: {
        "name": "base",
        "rpc": os.getenv("RPC_BASE"),
        "wss": os.getenv("WSS_BASE"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        "curve_router": "0x0000000000000000000000000000000000000000",
        "native": "ETH"
    },
    56: {
        "name": "bsc",
        "rpc": os.getenv("RPC_BSC"),
        "wss": os.getenv("WSS_BSC"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "pancake_router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "native": "BNB"
    },
    43114: {
        "name": "avalanche",
        "rpc": os.getenv("RPC_AVALANCHE"),
        "wss": os.getenv("WSS_AVALANCHE"),
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "traderjoe_router": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "native": "AVAX"
    },
    250: {
        "name": "fantom",
        "rpc": os.getenv("RPC_FANTOM"),
        "wss": None,
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "spookyswap_router": "0xF491e7B69E4244ad4002BC14e878a34207E38c29",
        "native": "FTM"
    },
    59144: {
        "name": "linea",
        "rpc": os.getenv("RPC_LINEA"),
        "wss": os.getenv("WSS_LINEA"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "syncswap_router": "0x0000000000000000000000000000000000000000",
        "native": "ETH"
    },
    534352: {
        "name": "scroll",
        "rpc": os.getenv("RPC_SCROLL"),
        "wss": os.getenv("WSS_SCROLL"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "native": "ETH"
    },
    5000: {
        "name": "mantle",
        "rpc": os.getenv("RPC_MANTLE"),
        "wss": os.getenv("WSS_MANTLE"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "native": "MNT"
    },
    324: {
        "name": "zksync",
        "rpc": os.getenv("RPC_ZKSYNC"),
        "wss": os.getenv("WSS_ZKSYNC"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "syncswap_router": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
        "native": "ETH"
    },
    81457: {
        "name": "blast",
        "rpc": os.getenv("RPC_BLAST"),
        "wss": os.getenv("WSS_BLAST"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "thruster_router": "0x0000000000000000000000000000000000000000",
        "native": "ETH"
    },
    42220: {
        "name": "celo",
        "rpc": os.getenv("RPC_CELO"),
        "wss": None,
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "ubeswap_router": "0xE3D8bd6Aed4F159bc8000a9cD47CffDb95F96121",
        "native": "CELO"
    },
    204: {
        "name": "opbnb",
        "rpc": os.getenv("RPC_OPBNB"),
        "wss": os.getenv("WSS_OPBNB"),
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_router": "0x0000000000000000000000000000000000000000",
        "pancake_router": "0x0000000000000000000000000000000000000000",
        "native": "BNB"
    }
}

# DEX Router Registry (for multi-protocol support)
DEX_ROUTERS = {
    "uniswap_v3": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    "uniswap_v2": "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    "sushiswap": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
    "curve": "0x99a58482BD75cbab83b27EC03CA68fF489b5788f",
    "balancer_v2": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    "quickswap": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
    "pancakeswap": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
    "traderjoe": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
    "spookyswap": "0xF491e7B69E4244ad4002BC14e878a34207E38c29"
}