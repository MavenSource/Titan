"""
Token Discovery Module - Multi-chain token inventory and bridge-compatible asset detection
"""

class TokenDiscovery:
    """
    Manages token inventory across multiple chains and identifies bridge-compatible assets.
    """
    
    # Tokens that exist on multiple chains and can be bridged
    BRIDGE_ASSETS = [
        "USDC", "USDT", "DAI", "WETH", "WBTC", 
        "LINK", "UNI", "AAVE", "MATIC", "FRAX"
    ]
    
    # Token addresses by chain - Production ready configuration
    TOKEN_REGISTRY = {
        137: {  # Polygon
            "USDC": {
                "address": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC.e (bridged)
                "decimals": 6
            },
            "USDT": {
                "address": "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
                "decimals": 6
            },
            "DAI": {
                "address": "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
                "decimals": 18
            },
            "WETH": {
                "address": "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
                "decimals": 18
            },
            "WBTC": {
                "address": "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
                "decimals": 8
            },
            "MATIC": {
                "address": "0x0000000000000000000000000000000000001010",  # Native MATIC (not ERC20)
                "decimals": 18,
                "native": True
            },
            "WMATIC": {
                "address": "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",  # Wrapped MATIC (ERC20)
                "decimals": 18
            }
        },
        42161: {  # Arbitrum
            "USDC": {
                "address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # USDC.e (bridged)
                "decimals": 6
            },
            "USDT": {
                "address": "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
                "decimals": 6
            },
            "DAI": {
                "address": "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
                "decimals": 18
            },
            "WETH": {
                "address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
                "decimals": 18
            },
            "WBTC": {
                "address": "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
                "decimals": 8
            }
        },
        1: {  # Ethereum
            "USDC": {
                "address": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "decimals": 6
            },
            "USDT": {
                "address": "0xdAC17F958D2ee523a2206206994597C13D831ec7",
                "decimals": 6
            },
            "DAI": {
                "address": "0x6B175474E89094C44Da98b954EedeAC495271d0F",
                "decimals": 18
            },
            "WETH": {
                "address": "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
                "decimals": 18
            },
            "WBTC": {
                "address": "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
                "decimals": 8
            }
        }
    }
    
    @classmethod
    def fetch_all_chains(cls, chain_ids):
        """
        Fetches token inventory for specified chains.
        
        Args:
            chain_ids (list): List of chain IDs to fetch tokens for
            
        Returns:
            dict: Nested dictionary {chain_id: {symbol: {address, decimals}}}
        """
        inventory = {}
        
        for chain_id in chain_ids:
            if chain_id in cls.TOKEN_REGISTRY:
                inventory[chain_id] = cls.TOKEN_REGISTRY[chain_id]
            else:
                # Return empty dict for unconfigured chains
                inventory[chain_id] = {}
        
        return inventory
    
    @classmethod
    def get_token_address(cls, chain_id, symbol):
        """
        Get token address for a specific chain and symbol.
        
        Args:
            chain_id (int): Chain ID
            symbol (str): Token symbol (e.g., "USDC")
            
        Returns:
            str: Token address or None if not found
        """
        if chain_id in cls.TOKEN_REGISTRY:
            token_data = cls.TOKEN_REGISTRY[chain_id].get(symbol)
            if token_data:
                return token_data["address"]
        return None
    
    @classmethod
    def get_token_decimals(cls, chain_id, symbol):
        """
        Get token decimals for a specific chain and symbol.
        
        Args:
            chain_id (int): Chain ID
            symbol (str): Token symbol (e.g., "USDC")
            
        Returns:
            int: Token decimals or 18 (default) if not found
        """
        if chain_id in cls.TOKEN_REGISTRY:
            token_data = cls.TOKEN_REGISTRY[chain_id].get(symbol)
            if token_data:
                return token_data["decimals"]
        return 18  # Default to 18 decimals
