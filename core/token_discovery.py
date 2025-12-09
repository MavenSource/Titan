"""
Token Discovery - Multi-chain token inventory system
Discovers and tracks tokens across all supported chains
"""
from web3 import Web3
from typing import Dict, List
import logging

logger = logging.getLogger("TokenDiscovery")

class TokenDiscovery:
    """
    Discovers and manages token inventories across multiple chains
    """
    
    # Common stablecoins and wrapped tokens across chains
    COMMON_TOKENS = {
        "USDC": {
            1: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",      # Ethereum
            137: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",    # Polygon (bridged)
            42161: "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8",  # Arbitrum
            10: "0x7F5c764cBc14f9669B88837ca1490cCa17c31607",     # Optimism
            8453: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",   # Base
            56: "0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d",     # BSC
            43114: "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E"  # Avalanche
        },
        "USDT": {
            1: "0xdAC17F958D2ee523a2206206994597C13D831ec7",      # Ethereum
            137: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",    # Polygon
            42161: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",  # Arbitrum
            10: "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",     # Optimism
            56: "0x55d398326f99059fF775485246999027B3197955",     # BSC
            43114: "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7"  # Avalanche
        },
        "DAI": {
            1: "0x6B175474E89094C44Da98b954EedeAC495271d0F",      # Ethereum
            137: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",    # Polygon
            42161: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",  # Arbitrum
            10: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",     # Optimism
            8453: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb"    # Base
        },
        "WETH": {
            1: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",      # Ethereum
            137: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",    # Polygon
            42161: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",  # Arbitrum
            10: "0x4200000000000000000000000000000000000006",     # Optimism
            8453: "0x4200000000000000000000000000000000000006",   # Base
            56: "0x2170Ed0880ac9A755fd29B2688956BD959F933F8",     # BSC (ETH)
            43114: "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB"  # Avalanche
        },
        "WBTC": {
            1: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",      # Ethereum
            137: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",    # Polygon
            42161: "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",  # Arbitrum
            10: "0x68f180fcCe6836688e9084f035309E29Bf0A2095",     # Optimism
            43114: "0x50b7545627a5162F82A992c33b87aDc75187B218"  # Avalanche
        }
    }
    
    @staticmethod
    def fetch_all_chains(chain_ids: List[int]) -> Dict[int, Dict[str, str]]:
        """
        Fetch token inventory for all specified chains
        
        Args:
            chain_ids: List of chain IDs to discover tokens on
            
        Returns:
            Dict mapping chain_id -> {symbol: address}
        """
        inventory = {}
        
        for chain_id in chain_ids:
            inventory[chain_id] = TokenDiscovery.get_tokens_for_chain(chain_id)
            logger.info(f"Discovered {len(inventory[chain_id])} tokens on chain {chain_id}")
        
        return inventory
    
    @staticmethod
    def get_tokens_for_chain(chain_id: int) -> Dict[str, str]:
        """
        Get token addresses for a specific chain
        
        Args:
            chain_id: Chain ID
            
        Returns:
            Dict mapping symbol -> address
        """
        tokens = {}
        
        for symbol, addresses in TokenDiscovery.COMMON_TOKENS.items():
            if chain_id in addresses:
                tokens[symbol] = addresses[chain_id]
        
        return tokens
    
    @staticmethod
    def is_bridge_compatible(token_symbol: str, chain_ids: List[int]) -> bool:
        """
        Check if a token exists on multiple chains (bridge-compatible)
        
        Args:
            token_symbol: Token symbol (e.g., "USDC")
            chain_ids: List of chain IDs to check
            
        Returns:
            bool: True if token exists on all specified chains
        """
        if token_symbol not in TokenDiscovery.COMMON_TOKENS:
            return False
        
        token_chains = TokenDiscovery.COMMON_TOKENS[token_symbol]
        return all(chain_id in token_chains for chain_id in chain_ids)
    
    @staticmethod
    def get_bridge_tokens() -> List[str]:
        """
        Get list of tokens that can be bridged (exist on multiple chains)
        
        Returns:
            List of token symbols
        """
        bridge_tokens = []
        for symbol, addresses in TokenDiscovery.COMMON_TOKENS.items():
            if len(addresses) >= 2:  # Exists on at least 2 chains
                bridge_tokens.append(symbol)
        return bridge_tokens
    
    @staticmethod
    def get_token_address(chain_id: int, symbol: str) -> str:
        """
        Get token address for a specific chain and symbol
        
        Args:
            chain_id: Chain ID
            symbol: Token symbol
            
        Returns:
            Token address or None if not found
        """
        if symbol in TokenDiscovery.COMMON_TOKENS:
            return TokenDiscovery.COMMON_TOKENS[symbol].get(chain_id)
        return None
