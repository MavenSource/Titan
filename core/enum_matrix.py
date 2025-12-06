"""
Chain Manager - Provides connection details for all supported networks
"""
from core.config import CHAINS

class ChainManager:
    """
    Utility class to get network connection details across 15+ chains
    """
    
    @staticmethod
    def get_connection_details(chain_id: int) -> dict:
        """
        Returns RPC, WebSocket, and network details for a given chain ID
        
        Args:
            chain_id: The EVM chain ID
            
        Returns:
            dict with keys: name, rpc, wss, aave_pool, uniswap_router, native
        """
        if chain_id not in CHAINS:
            raise ValueError(f"Chain ID {chain_id} not configured in CHAINS")
        
        return CHAINS[chain_id]
    
    @staticmethod
    def get_all_chain_ids() -> list:
        """
        Returns list of all configured chain IDs
        """
        return list(CHAINS.keys())
    
    @staticmethod
    def is_chain_supported(chain_id: int) -> bool:
        """
        Check if a chain is supported
        """
        return chain_id in CHAINS
    
    @staticmethod
    def get_chain_name(chain_id: int) -> str:
        """
        Get human-readable chain name
        """
        return CHAINS.get(chain_id, {}).get("name", "Unknown")
