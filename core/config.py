"""
🔧 APEX-OMEGA TITAN: MASTER CONFIGURATION MODULE
Complete multi-chain configuration for mainnet production deployment
Version: 4.2.0 Production-Ready
"""

import os
from dotenv import load_dotenv
load_dotenv()

# ==============================================================================
# DEFAULT CHAIN CONFIGURATION
# ==============================================================================
DEFAULT_CHAIN_ID = 137  # Polygon - Primary network for operations
DEFAULT_CHAIN_NAME = "polygon"

# ==============================================================================
# FLASH LOAN PROVIDERS (Universal Addresses)
# ==============================================================================

# Balancer V3 Vault - Deterministic address across all chains
BALANCER_V3_VAULT = "0xbA1333333333a1BA1108E8412f11850A5C319bA9"

# ==============================================================================
# MULTI-CHAIN CONFIGURATION (15 Chains)
# Polygon (137) is the DEFAULT_CHAIN_ID and primary network
# ==============================================================================

CHAINS = {
    # ========== TIER 0: PRIMARY NETWORK (POLYGON) ==========
    # Note: Chain ID 137 defined below in original order
    
    # ========== TIER 1: MAJOR CHAINS ==========
    1: {
        "name": "ethereum",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_ETHEREUM"),
        "wss": os.getenv("WSS_ETHEREUM"),
        "rpc_backup": os.getenv("ALCHEMY_RPC_ETH"),
        "wss_backup": os.getenv("ALCHEMY_WSS_ETH"),
        "native": "ETH",
        "wrapped_native": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
        "aave_pool": "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2",
        "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "uniswap_v3_quoter": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "uniswap_v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "sushiswap_router": "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        "curve_registry": "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
        "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "paraswap_router": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "explorer": "https://etherscan.io",
        "gas_multiplier": 1.3,
        "max_gas_price_gwei": 150,
        "block_time": 12
    },
    
    137: {
        "name": "polygon",
        "symbol": "MATIC",
        "rpc": os.getenv("RPC_POLYGON"),
        "wss": os.getenv("WSS_POLYGON"),
        "rpc_backup": os.getenv("ALCHEMY_RPC_POLY"),
        "wss_backup": os.getenv("ALCHEMY_WSS_POLY"),
        "native": "MATIC",
        "wrapped_native": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "uniswap_v3_quoter": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "uniswap_v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "quickswap_router": "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff",
        "quickswap_v3_router": "0xf5b509bB0909a69B1c207E495f687a596C168E12",
        "sushiswap_router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "curve_router": "0x8e1B5eDb16694b3064AA4B6726153CeC4A5E4321",
        "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "paraswap_router": "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        "explorer": "https://polygonscan.com",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 500,
        "block_time": 2
    },
    
    42161: {
        "name": "arbitrum",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_ARBITRUM"),
        "wss": os.getenv("WSS_ARBITRUM"),
        "rpc_backup": os.getenv("ALCHEMY_RPC_ARB"),
        "wss_backup": os.getenv("ALCHEMY_WSS_ARB"),
        "native": "ETH",
        "wrapped_native": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "uniswap_v3_quoter": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "uniswap_v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "sushiswap_router": "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        "camelot_router": "0x1aB1E8E7A97790345e94b807b6E6cb57D6E89E3C",
        "curve_router": "0x445FE580eF8d70FF569aB36e80c647af338db351",
        "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "explorer": "https://arbiscan.io",
        "gas_multiplier": 1.15,
        "max_gas_price_gwei": 10,
        "block_time": 0.25
    },
    
    10: {
        "name": "optimism",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_OPTIMISM"),
        "wss": os.getenv("WSS_OPTIMISM"),
        "rpc_backup": os.getenv("ALCHEMY_RPC_OPT"),
        "wss_backup": os.getenv("ALCHEMY_WSS_OPT"),
        "native": "ETH",
        "wrapped_native": "0x4200000000000000000000000000000000000006",
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "uniswap_v3_quoter": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "uniswap_v3_factory": "0x1F98431c8aD98523631AE4a59f267346ea31F984",
        "velodrome_router": "0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858",
        "curve_router": "0x0000000000000000000000000000000000000000",
        "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "explorer": "https://optimistic.etherscan.io",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 5,
        "block_time": 2
    },
    
    8453: {
        "name": "base",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_BASE"),
        "wss": os.getenv("WSS_BASE"),
        "rpc_backup": os.getenv("ALCHEMY_RPC_BASE"),
        "wss_backup": os.getenv("ALCHEMY_WSS_BASE"),
        "native": "ETH",
        "wrapped_native": "0x4200000000000000000000000000000000000006",
        "aave_pool": "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5",
        "uniswap_v3_router": "0x2626664c2603336E57B271c5C0b26F421741e481",
        "uniswap_v3_quoter": "0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a",
        "uniswap_v3_factory": "0x33128a8fC17869897dcE68Ed026d694621f6FDfD",
        "aerodrome_router": "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
        "balancer_vault": "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "explorer": "https://basescan.org",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 3,
        "block_time": 2
    },
    
    # ========== TIER 2: SECONDARY CHAINS ==========
    56: {
        "name": "bsc",
        "symbol": "BNB",
        "rpc": os.getenv("RPC_BSC"),
        "wss": os.getenv("WSS_BSC"),
        "native": "BNB",
        "wrapped_native": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "pancakeswap_router": "0x10ED43C718714eb63d5aA57B78B54704E256024E",
        "pancakeswap_v3_router": "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        "biswap_router": "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
        "apeswap_router": os.getenv("APE_SWAP_ROUTER"),
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "explorer": "https://bscscan.com",
        "gas_multiplier": 1.1,
        "max_gas_price_gwei": 20,
        "block_time": 3
    },
    
    43114: {
        "name": "avalanche",
        "symbol": "AVAX",
        "rpc": os.getenv("RPC_AVALANCHE"),
        "wss": os.getenv("WSS_AVALANCHE"),
        "native": "AVAX",
        "wrapped_native": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
        "aave_pool": "0x794a61358D6845594F94dc1DB02A252b5b4814aD",
        "uniswap_v3_router": "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "uniswap_v3_quoter": "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",
        "traderjoe_router": "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
        "pangolin_router": "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",
        "curve_router": "0x8e1B5eDb16694b3064AA4B6726153CeC4A5E4321",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "explorer": "https://snowtrace.io",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 100,
        "block_time": 2
    },
    
    250: {
        "name": "fantom",
        "symbol": "FTM",
        "rpc": os.getenv("RPC_FANTOM"),
        "native": "FTM",
        "wrapped_native": "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "spookyswap_router": "0xF491e7B69E4244ad4002BC14e878a34207E38c29",
        "spiritswap_router": "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52",
        "curve_router": "0x0000000000000000000000000000000000000000",
        "one_inch_router": "0x1111111254EEB25477B68fb85Ed929f73A960582",
        "explorer": "https://ftmscan.com",
        "gas_multiplier": 1.15,
        "max_gas_price_gwei": 500,
        "block_time": 1
    },
    
    # ========== TIER 3: L2 EMERGING CHAINS ==========
    59144: {
        "name": "linea",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_LINEA"),
        "wss": os.getenv("WSS_LINEA"),
        "native": "ETH",
        "wrapped_native": "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_v3_router": "0x0000000000000000000000000000000000000000",
        "lynex_router": "0x0000000000000000000000000000000000000000",
        "explorer": "https://lineascan.build",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 5,
        "block_time": 2
    },
    
    534352: {
        "name": "scroll",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_SCROLL"),
        "wss": os.getenv("WSS_SCROLL"),
        "native": "ETH",
        "wrapped_native": "0x5300000000000000000000000000000000000004",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "uniswap_v3_router": "0x0000000000000000000000000000000000000000",
        "explorer": "https://scrollscan.com",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 5,
        "block_time": 3
    },
    
    5000: {
        "name": "mantle",
        "symbol": "MNT",
        "rpc": os.getenv("RPC_MANTLE"),
        "wss": os.getenv("WSS_MANTLE"),
        "native": "MNT",
        "wrapped_native": "0x78c1b0C915c4FAA5FffA6CAbf0219DA63d7f4cb8",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "fusion_router": "0x0000000000000000000000000000000000000000",
        "explorer": "https://explorer.mantle.xyz",
        "gas_multiplier": 1.15,
        "max_gas_price_gwei": 10,
        "block_time": 2
    },
    
    324: {
        "name": "zksync",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_ZKSYNC"),
        "wss": os.getenv("WSS_ZKSYNC"),
        "native": "ETH",
        "wrapped_native": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "syncswap_router": "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
        "explorer": "https://explorer.zksync.io",
        "gas_multiplier": 1.3,
        "max_gas_price_gwei": 5,
        "block_time": 2
    },
    
    81457: {
        "name": "blast",
        "symbol": "ETH",
        "rpc": os.getenv("RPC_BLAST"),
        "wss": os.getenv("WSS_BLAST"),
        "native": "ETH",
        "wrapped_native": "0x4300000000000000000000000000000000000004",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "thruster_router": "0x0000000000000000000000000000000000000000",
        "explorer": "https://blastscan.io",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 3,
        "block_time": 2
    },
    
    42220: {
        "name": "celo",
        "symbol": "CELO",
        "rpc": os.getenv("RPC_CELO"),
        "native": "CELO",
        "wrapped_native": "0x471EcE3750Da237f93B8E339c536989b8978a438",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "ubeswap_router": "0xE3D8bd6Aed4F159bc8000a9cD47CffDb95F96121",
        "explorer": "https://celoscan.io",
        "gas_multiplier": 1.2,
        "max_gas_price_gwei": 10,
        "block_time": 5
    },
    
    204: {
        "name": "opbnb",
        "symbol": "BNB",
        "rpc": os.getenv("RPC_OPBNB"),
        "wss": os.getenv("WSS_OPBNB"),
        "native": "BNB",
        "wrapped_native": "0x4200000000000000000000000000000000000006",
        "aave_pool": "0x0000000000000000000000000000000000000000",
        "pancakeswap_router": "0x0000000000000000000000000000000000000000",
        "explorer": "https://opbnbscan.com",
        "gas_multiplier": 1.1,
        "max_gas_price_gwei": 5,
        "block_time": 1
    }
}

# ==============================================================================
# DEX ROUTERS MASTER REGISTRY
# ==============================================================================
# Organized by protocol for easy cross-chain routing

DEX_ROUTERS = {
    # Uniswap Family
    "UNISWAP_V2": {
        1: "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
    },
    "UNISWAP_V3": {
        1: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        137: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        42161: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        10: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        8453: "0x2626664c2603336E57B271c5C0b26F421741e481",
        43114: "0xE592427A0AEce92De3Edee1F18E0157C05861564",
    },
    
    # SushiSwap
    "SUSHISWAP": {
        1: "0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F",
        137: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        42161: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        43114: "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506",
        42220: "0x1421bDe4B10e8dd459b3BCb598810B1337D56842",
    },
    
    # QuickSwap (Polygon)
    "QUICKSWAP": {
        137: os.getenv("QUICKSWAP_ROUTER", "0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff"),
    },
    "QUICKSWAP_V3": {
        137: "0xf5b509bB0909a69B1c207E495f687a596C168E12",
    },
    
    # PancakeSwap
    "PANCAKESWAP_V2": {
        56: "0x10ED43C718714eb63d5aA57B78B54704E256024E",
    },
    "PANCAKESWAP_V3": {
        56: "0x13f4EA83D0bd40E75C8222255bc855a974568Dd4",
        204: "0x0000000000000000000000000000000000000000",
    },
    
    # Curve Finance
    "CURVE": {
        1: "0x90E00ACe148ca3b23Ac1bC8C240C2a7Dd9c2d7f5",
        137: "0x094d12e5b541784701FD8d65F11fc0598FBC6332",
        42161: "0x445FE580eF8d70FF569aB36e80c647af338db351",
        10: "0x0000000022D53366457F9d5E68Ec105046FC4383",
        43114: "0x8474DdbE98F5aA3179B3B3F5942D724aFcdec9f6",
        250: "0x0f854EA9F38ceA4B1c2FC79047E9D0134419D5d6",
    },
    
    # Balancer
    "BALANCER_V2": {
        1: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        137: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        42161: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        10: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
        8453: "0xBA12222222228d8Ba445958a75a0704d566BF2C8",
    },
    
    # Aggregators
    "ONEINCH": {
        1: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        137: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        42161: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        10: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        56: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        8453: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        43114: "0x1111111254EEB25477B68fb85Ed929f73A960582",
        250: "0x1111111254EEB25477B68fb85Ed929f73A960582",
    },
    "PARASWAP": {
        1: "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57",
        137: os.getenv("PARASWAP_ROUTER", "0xDEF171Fe48CF0115B1d80b88dc8eAB59176FEe57"),
    },
    "ZEROX": {
        1: os.getenv("ZRX_EXCHANGE_PROXY", "0xDef1C0ded9bec7F1a1670819833240f027b25EfF"),
        137: "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
        42161: "0xDef1C0ded9bec7F1a1670819833240f027b25EfF",
    },
    
    # Polygon-Specific DEXs
    "APESWAP": {
        56: os.getenv("APE_SWAP_ROUTER", "0xcF0feBd3f17CEf5b47b0cD257aCf6025c5BFf3b7"),
        137: "0xC0788A3aD43d79aa53B09c2EaCc313A787d1d607",
    },
    "DFYN": {
        137: os.getenv("DFYN_ROUTER", "0xA102072A4C07F06EC3B4900FDC4C7B80FbbdC5C7"),
    },
    "JETSWAP": {
        137: os.getenv("JET_SWAP_ROUTER", "0x313C53BCA1df6AA2a80C1aD4781d6A46E0D8f221"),
    },
    "POLYCAT": {
        137: os.getenv("POLYCAT_ROUTER", "0x94930a328162957FF1dd48900aF67B5439336cBD"),
    },
    "WAULTSWAP": {
        137: os.getenv("WAULT_SWAP_ROUTER", "0x9A17f09C9F7F04428eF5A6B59f2eCf902B9Ff8e4"),
    },
    "KYBER_DMM": {
        137: os.getenv("KYBERDMM_ROUTER", "0x546C79662E028B661dFB4767664d0273184E4Dd1"),
    },
    "DODO": {
        137: os.getenv("DODO_ROUTER", "0xa356867fDCEa8e71AEaF87805808803806231FdC"),
    },
    "FIREBIRD": {
        137: os.getenv("FIREBIRD_ROUTER", "0xFf7B995e8cA26De1Bd6C768E8d3b96946F72693E"),
    },
    
    # Arbitrum-Specific
    "CAMELOT": {
        42161: os.getenv("CAMELOT_ROUTER", "0x1aB1E8E7A97790345e94b807b6E6cb57D6E89E3C"),
    },
    
    # Optimism-Specific
    "VELODROME": {
        10: "0xa062aE8A9c5e11aaA026fc2670B0D65cCc8B2858",
    },
    
    # Base-Specific
    "AERODROME": {
        8453: "0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43",
    },
    
    # BSC-Specific
    "BISWAP": {
        56: "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
    },
    "BABYSWAP": {
        56: "0x325E343f1dE602396E256B67eFd1F61C3A6B38Bd",
    },
    
    # Avalanche-Specific
    "TRADERJOE": {
        43114: "0x60aE616a2155Ee3d9A68541Ba4544862310933d4",
    },
    "PANGOLIN": {
        43114: "0xE54Ca86531e17Ef3616d22Ca28b0D458b6C89106",
    },
    
    # Fantom-Specific
    "SPOOKYSWAP": {
        250: "0xF491e7B69E4244ad4002BC14e878a34207E38c29",
    },
    "SPIRITSWAP": {
        250: "0x16327E3FbDaCA3bcF7E38F5Af2599D2DDc33aE52",
    },
    
    # Layer 2 Specific
    "SYNCSWAP": {
        59144: "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
        534352: "0x80e38291e06339d10AAB483C65695D004dBD5C69",
        324: "0x2da10A1e27bF85cEdD8FFb1AbBe97e53391C0295",
    },
    "HORIZONDEX": {
        59144: "0x272E156Df8DA513C69cB41cC7A99185D53F926Bb",
    },
    "SPACEFI": {
        534352: "0x18b71386418A9FCa5Ae7165E31c385a5130011b6",
        324: "0xbE7D1FD1f6748bbDefC4fbaCafBb11C6Fc506d1d",
    },
    "FUSIONX": {
        5000: "0xAA30eF758139ae4a7f798112902Bf6d65612045f",
    },
    "AGNI": {
        5000: "0x319B69888b0d11cEC22caA5034e25FfFBDc88421",
    },
    "THRUSTER": {
        81457: "0x98994a9A7a2570367554589189dC9772241650f6",
    },
    "UBESWAP": {
        42220: "0xE3D8bd6Aed4F159bc8000a9cD47CffDb95F96121",
    },
    "PANCAKESWAP_V3_L2": {
        59144: "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
        324: "0xf8b59f3c3Ab33200ec80a8A58b2aA5F5D2a8944C",
        204: "0x1b81D678ffb9C0263b24A97847620C99d213eB14",
    },
    "LINEHUB": {
        59144: "0xB3b0d5BC9e3e1e8e3F0c4e3e2b5bF3b3e0f3e0f3",
    },
    "SKYDROME": {
        534352: "0xAA111C62cDEEf205f70E6722D1E22274274ec12F",
    },
    "MERCHANT_MOE": {
        5000: "0xeaEE7EE68874218c3558b40063c42B82D3E7232a",
    },
    "MUTE": {
        324: "0x8B791913eB07C32779a16750e3868aA8495F5964",
    },
    "VELOCORE": {
        324: "0xd999E16e68476bC749A28FC14a0c3b6d7073F50c",
    },
    "THRUSTER_V3": {
        81457: "0x337827814155ECBf24D20231fCA4444F530C0555",
    },
    "BLADESWAP": {
        81457: "0x8e0B2e8E60c63c4eF12e55d9d03B7D7C2c08c85B",
    },
    "MONOBOMB": {
        81457: "0x9a5c8e4F0C2F5e3bBf0b95B5a9d5e6B8c4A6e3f9",
    },
    "CURVE_CELO": {
        42220: "0x0A3f7E8749c09C5c46B00A9D7e37c8b00f3A0e1d",
    },
    "BISWAP": {
        204: "0x3a6d8cA21D1CF76F653A67577FA0D27453350dD8",
    },
}

# ==============================================================================
# PROTOCOL IDS (For Smart Contract Encoding)
# ==============================================================================

PROTOCOL_IDS = {
    "UNISWAP_V2": 0,
    "UNISWAP_V3": 1,
    "CURVE": 2,
    "BALANCER_V2": 3,
    "PARASWAP": 4,
    "SUSHISWAP": 5,
    "QUICKSWAP": 6,
    "PANCAKESWAP": 7,
    "ONEINCH": 8,
    "ZEROX": 9,
}

# ==============================================================================
# GAS & TRADE LIMITS
# ==============================================================================

MIN_TRADE_USD = 10000  # $10k minimum
MAX_TVL_SHARE = 0.20   # Max 20% of pool liquidity
GAS_SAFETY_MULTIPLIER = 1.2

GAS_LIMITS = {
    "SIMPLE_SWAP": 150000,
    "FLASH_LOAN": 500000,
    "MULTI_HOP": 800000,
    "CROSS_CHAIN": 1200000,
}

# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================

def get_router(protocol_name: str, chain_id: int) -> str:
    """Get DEX router address for a protocol on a specific chain."""
    routers = DEX_ROUTERS.get(protocol_name, {})
    return routers.get(chain_id, "0x0000000000000000000000000000000000000000")

def get_chain_config(chain_id: int) -> dict:
    """Get complete chain configuration."""
    return CHAINS.get(chain_id, {})

def get_all_chain_ids() -> list:
    """Get list of all supported chain IDs."""
    return list(CHAINS.keys())

def get_rpc_url(chain_id: int, use_backup: bool = False) -> str:
    """Get RPC URL for a chain with optional fallback to backup."""
    config = CHAINS.get(chain_id, {})
    if use_backup and config.get("rpc_backup"):
        return config.get("rpc_backup")
    return config.get("rpc", "")

def get_wss_url(chain_id: int, use_backup: bool = False) -> str:
    """Get WebSocket URL for a chain with optional fallback."""
    config = CHAINS.get(chain_id, {})
    if use_backup and config.get("wss_backup"):
        return config.get("wss_backup")
    return config.get("wss", "")

def get_flash_loan_providers(chain_id: int) -> dict:
    """Get all flash loan provider addresses for a chain."""
    config = CHAINS.get(chain_id, {})
    return {
        "aave": config.get("aave_pool"),
        "balancer": BALANCER_V3_VAULT,
    }

def get_native_token(chain_id: int) -> str:
    """Get native token symbol for a chain."""
    config = CHAINS.get(chain_id, {})
    return config.get("native", "ETH")

def get_wrapped_native(chain_id: int) -> str:
    """Get wrapped native token address for a chain."""
    config = CHAINS.get(chain_id, {})
    return config.get("wrapped_native", "0x0000000000000000000000000000000000000000")

def validate_config() -> bool:
    """Validate critical configurations are present."""
    errors = []
    warnings = []
    
    for chain_id, config in CHAINS.items():
        chain_name = config.get("name", "unknown")
        
        # Critical checks
        if not config.get("rpc"):
            errors.append(f"Chain {chain_id} ({chain_name}): Missing RPC endpoint")
        
        if not config.get("wrapped_native"):
            errors.append(f"Chain {chain_id} ({chain_name}): Missing wrapped native token")
        
        # Warning checks
        if not config.get("wss"):
            warnings.append(f"Chain {chain_id} ({chain_name}): No WebSocket endpoint (real-time monitoring disabled)")
        
        if not config.get("rpc_backup"):
            warnings.append(f"Chain {chain_id} ({chain_name}): No backup RPC (no redundancy)")
        
        if config.get("aave_pool") == "0x0000000000000000000000000000000000000000":
            warnings.append(f"Chain {chain_id} ({chain_name}): No Aave pool (flash loans limited to Balancer)")
    
    # Print results
    if errors:
        print("❌ CRITICAL Configuration Errors:")
        for error in errors:
            print(f"   {error}")
        return False
    
    if warnings:
        print("⚠️  Configuration Warnings:")
        for warning in warnings:
            print(f"   {warning}")
    
    print(f"✅ Configuration validated: {len(CHAINS)} chains, {len(DEX_ROUTERS)} DEX protocols")
    return True

# ==============================================================================
# RUN VALIDATION
# ==============================================================================

if __name__ == "__main__":
    validate_config()
    print(f"\n📊 Summary:")
    print(f"   Default Chain: {DEFAULT_CHAIN_NAME.upper()} (Chain ID: {DEFAULT_CHAIN_ID})")
    print(f"   Chains: {len(CHAINS)}")
    print(f"   DEX Protocols: {len(DEX_ROUTERS)}")
    print(f"   Flash Loan Providers: Balancer V3 (Universal) + Aave V3 (Select chains)")