"""
Enum Matrix - Chain ID enumeration and provider management utilities
"""
from enum import IntEnum
from web3 import Web3
from core.config import CHAINS
import os

class ChainID(IntEnum):
    """
    Enumeration of supported blockchain networks by their EIP-155 Chain ID
    """
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

class ProviderManager:
    """
    Manages Web3 provider connections for multiple chains
    """
    
    @staticmethod
    def get_provider(chain_id):
        """
        Get Web3 provider for a specific chain
        
        Args:
            chain_id (int): Chain ID
            
        Returns:
            Web3: Connected Web3 instance or None if not configured
        """
        chain_config = CHAINS.get(chain_id)
        if not chain_config or not chain_config.get('rpc'):
            return None
        
        rpc_url = chain_config['rpc']
        if not rpc_url:
            return None
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            if w3.is_connected():
                return w3
        except Exception as e:
            print(f"⚠️ Failed to connect to chain {chain_id}: {e}")
        
        return None
    
    @staticmethod
    def get_all_providers():
        """
        Get Web3 providers for all configured chains
        
        Returns:
            dict: {chain_id: Web3 instance}
        """
        providers = {}
        for chain_id in CHAINS.keys():
            provider = ProviderManager.get_provider(chain_id)
            if provider:
                providers[chain_id] = provider
        
        return providers
    
    @staticmethod
    def test_connection(chain_id):
        """
        Test connection to a specific chain
        
        Args:
            chain_id (int): Chain ID to test
            
        Returns:
            bool: True if connected, False otherwise
        """
        provider = ProviderManager.get_provider(chain_id)
        if not provider:
            return False
        
        try:
            block_number = provider.eth.block_number
            print(f"✅ Chain {chain_id}: Connected | Block: {block_number}")
            return True
        except Exception as e:
            print(f"❌ Chain {chain_id}: Connection failed | Error: {e}")
            return False
