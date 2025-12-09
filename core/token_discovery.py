"""
================================================================================
APEX-OMEGA TITAN: TOKEN DISCOVERY & REGISTRY MODULE
================================================================================
Comprehensive token address registry for all supported chains with bridge-
compatible assets and automated chain scanning capabilities.

Last Updated: December 9, 2025
Version: 4.2.0
================================================================================
"""

import logging
from typing import Dict, List
from core.config import CHAINS

logger = logging.getLogger("TokenDiscovery")

# ==============================================================================
# BRIDGE-COMPATIBLE ASSETS
# ==============================================================================
# These tokens exist on multiple chains and can be bridged via Li.Fi

BRIDGE_ASSETS = [
    "USDC", "USDT", "DAI", "WETH", "WBTC",
    "USDC.e", "LINK", "UNI", "AAVE", "CRV"
]

# ==============================================================================
# TOKEN REGISTRY BY CHAIN
# ==============================================================================
# Complete address registry for major tokens on each supported chain

TOKEN_REGISTRY = {
    # ==========================================================================
    # ETHEREUM MAINNET (Chain ID: 1)
    # ==========================================================================
    1: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
            "decimals": 8
        },
        "LINK": {
            "symbol": "LINK",
            "name": "Chainlink",
            "address": "0x514910771AF9Ca656af840dff83E8264EcF986CA",
            "decimals": 18
        },
        "UNI": {
            "symbol": "UNI",
            "name": "Uniswap",
            "address": "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
            "decimals": 18
        },
        "AAVE": {
            "symbol": "AAVE",
            "name": "Aave Token",
            "address": "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
            "decimals": 18
        },
        "CRV": {
            "symbol": "CRV",
            "name": "Curve DAO Token",
            "address": "0xD533a949740bb3306d119CC777fa900bA034cd52",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # POLYGON (Chain ID: 137)
    # ==========================================================================
    137: {
        "MATIC": {
            "symbol": "MATIC",
            "name": "Polygon",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WMATIC": {
            "symbol": "WMATIC",
            "name": "Wrapped Matic",
            "address": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
            "decimals": 18
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDC.e": {
            "symbol": "USDC.e",
            "name": "USD Coin (Bridged)",
            "address": "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
            "decimals": 8
        },
        "LINK": {
            "symbol": "LINK",
            "name": "Chainlink",
            "address": "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
            "decimals": 18
        },
        "UNI": {
            "symbol": "UNI",
            "name": "Uniswap",
            "address": "0xb33EaAd8d922B1083446DC23f610c2567fB5180f",
            "decimals": 18
        },
        "AAVE": {
            "symbol": "AAVE",
            "name": "Aave Token",
            "address": "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
            "decimals": 18
        },
        "CRV": {
            "symbol": "CRV",
            "name": "Curve DAO Token",
            "address": "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # ARBITRUM (Chain ID: 42161)
    # ==========================================================================
    42161: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDC.e": {
            "symbol": "USDC.e",
            "name": "USD Coin (Bridged)",
            "address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
            "decimals": 8
        },
        "LINK": {
            "symbol": "LINK",
            "name": "Chainlink",
            "address": "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
            "decimals": 18
        },
        "UNI": {
            "symbol": "UNI",
            "name": "Uniswap",
            "address": "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0",
            "decimals": 18
        },
        "ARB": {
            "symbol": "ARB",
            "name": "Arbitrum",
            "address": "0x912CE59144191C1204E64559FE8253a0e49E6548",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # OPTIMISM (Chain ID: 10)
    # ==========================================================================
    10: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x4200000000000000000000000000000000000006",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDC.e": {
            "symbol": "USDC.e",
            "name": "USD Coin (Bridged)",
            "address": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x68f180fcCe6836688e9084f035309E29Bf0A2095",
            "decimals": 8
        },
        "OP": {
            "symbol": "OP",
            "name": "Optimism",
            "address": "0x4200000000000000000000000000000000000042",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # BASE (Chain ID: 8453)
    # ==========================================================================
    8453: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x4200000000000000000000000000000000000006",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
            "decimals": 18,
            "is_stablecoin": True
        },
    },
    
    # ==========================================================================
    # BSC (Chain ID: 56)
    # ==========================================================================
    56: {
        "BNB": {
            "symbol": "BNB",
            "name": "BNB",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WBNB": {
            "symbol": "WBNB",
            "name": "Wrapped BNB",
            "address": "0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",
            "decimals": 18,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x55d398326f99059fF775485246999027B3197955",
            "decimals": 18,
            "is_stablecoin": True
        },
        "BUSD": {
            "symbol": "BUSD",
            "name": "Binance USD",
            "address": "0xe9e7CEA3DedcA5984780Bafc599bD69ADd087D56",
            "decimals": 18,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",
            "decimals": 18
        },
        "BTCB": {
            "symbol": "BTCB",
            "name": "Bitcoin BEP2",
            "address": "0x7130d2A12B9BCbFAe4f2634d864A1Ee1Ce3Ead9c",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # AVALANCHE (Chain ID: 43114)
    # ==========================================================================
    43114: {
        "AVAX": {
            "symbol": "AVAX",
            "name": "Avalanche",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WAVAX": {
            "symbol": "WAVAX",
            "name": "Wrapped AVAX",
            "address": "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WETH.e": {
            "symbol": "WETH.e",
            "name": "Wrapped Ether",
            "address": "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",
            "decimals": 18
        },
        "WBTC.e": {
            "symbol": "WBTC.e",
            "name": "Wrapped BTC",
            "address": "0x50b7545627a5162F82A992c33b87aDc75187B218",
            "decimals": 8
        },
    },
    
    # ==========================================================================
    # FANTOM (Chain ID: 250)
    # ==========================================================================
    250: {
        "FTM": {
            "symbol": "FTM",
            "name": "Fantom",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WFTM": {
            "symbol": "WFTM",
            "name": "Wrapped Fantom",
            "address": "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x8D11eC38a3EB5E956B052f67Da8Bdc9bef8Abf3E",
            "decimals": 18,
            "is_stablecoin": True
        },
    },
    
    # ==========================================================================
    # LINEA (Chain ID: 59144)
    # ==========================================================================
    59144: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x176211869cA2b568f2A7D4EE941E073a821EE1ff",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0xA219439258ca9da29E9Cc4cE5596924745e12B93",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x4AF15ec2A0BD43Db75dd04E62FAA3B8EF36b00d5",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x3aAB2285ddcDdaD8edf438C1bAB47e1a9D05a9b4",
            "decimals": 8
        },
    },
    
    # ==========================================================================
    # SCROLL (Chain ID: 534352)
    # ==========================================================================
    534352: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x5300000000000000000000000000000000000004",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x06eFdBFf2a14a7c8E15944D1F4A48F9F95F663A4",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0xf55BEC9cafDbE8730f096Aa55dad6D22d44099Df",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0xcA77eB3fEFe3725Dc33bccB54eDEFc3D9f764f97",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0x3C1BCa5a656e69edCD0D4E36BEbb3FcDAcA60Cf1",
            "decimals": 8
        },
    },
    
    # ==========================================================================
    # MANTLE (Chain ID: 5000)
    # ==========================================================================
    5000: {
        "MNT": {
            "symbol": "MNT",
            "name": "Mantle",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WMNT": {
            "symbol": "WMNT",
            "name": "Wrapped Mantle",
            "address": "0x78c1b0C915c4FAA5FffA6CAbf0219DA63d7f4cb8",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x09Bc4E0D864854c6aFB6eB9A9cdF58aC190D0dF9",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x201EBa5CC46D216Ce6DC03F6a759e8E766e956aE",
            "decimals": 6,
            "is_stablecoin": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0xdEAddEaDdeadDEadDEADDEAddEADDEAddead1111",
            "decimals": 18
        },
        "mETH": {
            "symbol": "mETH",
            "name": "Mantle Staked Ether",
            "address": "0xcDA86A272531e8640cD7F1a92c01839911B90bb0",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # ZKSYNC ERA (Chain ID: 324)
    # ==========================================================================
    324: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x5AEa5775959fBC2557Cc8789bC1bf90A239D9a91",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0x3355df6D4c9C3035724Fd0e3914dE96A5a83aaf4",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDC.e": {
            "symbol": "USDC.e",
            "name": "USD Coin (Bridged)",
            "address": "0x1d17CBcF0D6D143135aE902365D2E5e2A16538D4",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x493257fD37EDB34451f62EDf8D2a0C418852bA4C",
            "decimals": 6,
            "is_stablecoin": True
        },
        "DAI": {
            "symbol": "DAI",
            "name": "Dai Stablecoin",
            "address": "0x4B9eb6c0b6ea15176BBF62841C6B2A8a398cb656",
            "decimals": 18,
            "is_stablecoin": True
        },
        "WBTC": {
            "symbol": "WBTC",
            "name": "Wrapped BTC",
            "address": "0xBBeB516fb02a01611cBBE0453Fe3c580D7281011",
            "decimals": 8
        },
    },
    
    # ==========================================================================
    # BLAST (Chain ID: 81457)
    # ==========================================================================
    81457: {
        "ETH": {
            "symbol": "ETH",
            "name": "Ether",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WETH": {
            "symbol": "WETH",
            "name": "Wrapped Ether",
            "address": "0x4300000000000000000000000000000000000004",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDB": {
            "symbol": "USDB",
            "name": "Blast USD",
            "address": "0x4300000000000000000000000000000000000003",
            "decimals": 18,
            "is_stablecoin": True
        },
        "BLAST": {
            "symbol": "BLAST",
            "name": "Blast Token",
            "address": "0xb1a5700fA2358173Fe465e6eA4Ff52E36e88E2ad",
            "decimals": 18
        },
    },
    
    # ==========================================================================
    # CELO (Chain ID: 42220)
    # ==========================================================================
    42220: {
        "CELO": {
            "symbol": "CELO",
            "name": "Celo Native",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WCELO": {
            "symbol": "WCELO",
            "name": "Wrapped Celo",
            "address": "0x471EcE3750Da237f93B8E339c536989b8978a438",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "cUSD": {
            "symbol": "cUSD",
            "name": "Celo Dollar",
            "address": "0x765DE816845861e75A25fCA122bb6898B8B1282a",
            "decimals": 18,
            "is_stablecoin": True
        },
        "cEUR": {
            "symbol": "cEUR",
            "name": "Celo Euro",
            "address": "0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73",
            "decimals": 18,
            "is_stablecoin": True
        },
        "cREAL": {
            "symbol": "cREAL",
            "name": "Celo Real",
            "address": "0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787",
            "decimals": 18,
            "is_stablecoin": True
        },
        "USDC": {
            "symbol": "USDC",
            "name": "USD Coin",
            "address": "0xcebA9300f2b948710d2653dD7B07f33A8B32118C",
            "decimals": 6,
            "is_stablecoin": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x48065fbBE25f71C9282ddf5e1cD6D6A887483D5e",
            "decimals": 6,
            "is_stablecoin": True
        },
    },
    
    # ==========================================================================
    # OPBNB (Chain ID: 204)
    # ==========================================================================
    204: {
        "BNB": {
            "symbol": "BNB",
            "name": "BNB",
            "address": "0x0000000000000000000000000000000000000000",  # Native
            "decimals": 18,
            "is_native": True
        },
        "WBNB": {
            "symbol": "WBNB",
            "name": "Wrapped BNB",
            "address": "0x4200000000000000000000000000000000000006",
            "decimals": 18,
            "is_wrapped_native": True
        },
        "USDT": {
            "symbol": "USDT",
            "name": "Tether USD",
            "address": "0x9e5AAC1Ba1a2e6aEd6b32689DFcF62A509Ca96f3",
            "decimals": 18,
            "is_stablecoin": True
        },
        "FDUSD": {
            "symbol": "FDUSD",
            "name": "First Digital USD",
            "address": "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
            "decimals": 18,
            "is_stablecoin": True
        },
    },
}

# ==============================================================================
# TOKEN DISCOVERY CLASS
# ==============================================================================

class TokenDiscovery:
    """
    Handles token discovery and registry management across all chains.
    """
    
    # Bridge-compatible assets (class attribute)
    BRIDGE_ASSETS = BRIDGE_ASSETS
    
    @staticmethod
    def fetch_all_chains(chain_ids: List[int]) -> Dict[int, Dict[str, dict]]:
        """
        Fetch token inventories for multiple chains.
        
        Args:
            chain_ids: List of chain IDs to fetch tokens for
            
        Returns:
            Dictionary mapping chain_id -> token_symbol -> token_data
        """
        logger.info(f"🔍 Fetching token inventories for {len(chain_ids)} chains...")
        
        inventory = {}
        for chain_id in chain_ids:
            if chain_id in TOKEN_REGISTRY:
                inventory[chain_id] = TOKEN_REGISTRY[chain_id]
                logger.debug(f"✅ Loaded {len(TOKEN_REGISTRY[chain_id])} tokens for chain {chain_id}")
            else:
                logger.warning(f"⚠️  Chain {chain_id} not found in registry")
                inventory[chain_id] = {}
        
        return inventory
    
    @staticmethod
    def get_token_address(chain_id: int, symbol: str) -> str:
        """
        Get token address for a specific symbol on a specific chain.
        
        Args:
            chain_id: Chain ID
            symbol: Token symbol (e.g., "USDC")
            
        Returns:
            Token address or None if not found
        """
        chain_tokens = TOKEN_REGISTRY.get(chain_id, {})
        token_data = chain_tokens.get(symbol, {})
        return token_data.get("address")
    
    @staticmethod
    def get_token_decimals(chain_id: int, symbol: str) -> int:
        """
        Get token decimals for a specific symbol on a specific chain.
        
        Args:
            chain_id: Chain ID
            symbol: Token symbol
            
        Returns:
            Decimal places (default: 18)
        """
        chain_tokens = TOKEN_REGISTRY.get(chain_id, {})
        token_data = chain_tokens.get(symbol, {})
        return token_data.get("decimals", 18)
    
    @staticmethod
    def is_stablecoin(chain_id: int, symbol: str) -> bool:
        """
        Check if a token is a stablecoin.
        
        Args:
            chain_id: Chain ID
            symbol: Token symbol
            
        Returns:
            True if stablecoin, False otherwise
        """
        chain_tokens = TOKEN_REGISTRY.get(chain_id, {})
        token_data = chain_tokens.get(symbol, {})
        return token_data.get("is_stablecoin", False)
    
    @staticmethod
    def get_wrapped_native(chain_id: int) -> dict:
        """
        Get the wrapped native token for a chain.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            Token data for wrapped native token
        """
        chain_tokens = TOKEN_REGISTRY.get(chain_id, {})
        for symbol, data in chain_tokens.items():
            if data.get("is_wrapped_native"):
                return data
        return None
    
    @staticmethod
    def get_stablecoins(chain_id: int) -> List[dict]:
        """
        Get all stablecoins for a specific chain.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            List of stablecoin token data
        """
        chain_tokens = TOKEN_REGISTRY.get(chain_id, {})
        return [
            data for symbol, data in chain_tokens.items()
            if data.get("is_stablecoin")
        ]
    
    @staticmethod
    def get_bridge_compatible_tokens() -> List[str]:
        """
        Get list of tokens that exist on multiple chains and can be bridged.
        
        Returns:
            List of token symbols
        """
        return BRIDGE_ASSETS.copy()
    
    @staticmethod
    def validate_token_exists(chain_id: int, address: str) -> bool:
        """
        Check if a token address exists in the registry for a chain.
        
        Args:
            chain_id: Chain ID
            address: Token address
            
        Returns:
            True if exists, False otherwise
        """
        chain_tokens = TOKEN_REGISTRY.get(chain_id, {})
        for symbol, data in chain_tokens.items():
            if data.get("address", "").lower() == address.lower():
                return True
        return False

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "TokenDiscovery",
    "TOKEN_REGISTRY",
    "BRIDGE_ASSETS"
]
