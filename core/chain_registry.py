"""
TITAN CHAIN EXECUTION REGISTRY
================================
Production-grade chain configuration with execution gating.

CHAIN STATES:
- ENABLED: Full execution allowed (Polygon only)
- CONFIGURED: RPC validated, execution disabled (Ethereum, Arbitrum)
- DISABLED: No RPC, no execution

This is the single source of truth for chain execution permissions.
"""

import os
import logging
from enum import Enum
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger("ChainRegistry")


class ChainExecutionState(Enum):
    """Chain execution states"""
    ENABLED = "ENABLED"           # Live execution allowed
    CONFIGURED = "CONFIGURED"     # RPC validated, execution disabled
    DISABLED = "DISABLED"          # Not configured


class ChainRegistry:
    """
    Centralized chain configuration and execution gating.
    
    CRITICAL GUARANTEES:
    - Only Polygon (137) can execute transactions
    - Ethereum (1) and Arbitrum (42161) are configured but execution-blocked
    - All other chains are disabled
    - RPC URLs must be validated at startup
    - No fallback to localhost
    """
    
    # Chain execution states (PRODUCTION CONFIG)
    CHAIN_STATES = {
        137: ChainExecutionState.ENABLED,      # Polygon - LIVE
        1: ChainExecutionState.CONFIGURED,     # Ethereum - RPC only
        42161: ChainExecutionState.CONFIGURED, # Arbitrum - RPC only
    }
    
    # Chain metadata
    CHAIN_METADATA = {
        1: {
            "name": "ethereum",
            "native": "ETH",
            "rpc_env": "RPC_ETHEREUM",
            "wss_env": "WSS_ETHEREUM",
            "chain_id": 1,
        },
        137: {
            "name": "polygon",
            "native": "MATIC",
            "rpc_env": "RPC_POLYGON",
            "wss_env": "WSS_POLYGON",
            "chain_id": 137,
        },
        42161: {
            "name": "arbitrum",
            "native": "ETH",
            "rpc_env": "RPC_ARBITRUM",
            "wss_env": "WSS_ARBITRUM",
            "chain_id": 42161,
        },
    }
    
    def __init__(self):
        self.validated_rpcs = {}
        self.health_status = {}
    
    @classmethod
    def is_execution_enabled(cls, chain_id: int) -> bool:
        """
        Check if transaction execution is allowed on this chain.
        
        Returns:
            bool: True only if chain is ENABLED (Polygon mainnet only)
        """
        state = cls.CHAIN_STATES.get(chain_id)
        return state == ChainExecutionState.ENABLED
    
    @classmethod
    def is_configured(cls, chain_id: int) -> bool:
        """
        Check if chain has RPC configuration.
        
        Returns:
            bool: True if chain is ENABLED or CONFIGURED
        """
        state = cls.CHAIN_STATES.get(chain_id)
        return state in [ChainExecutionState.ENABLED, ChainExecutionState.CONFIGURED]
    
    @classmethod
    def get_chain_name(cls, chain_id: int) -> str:
        """Get human-readable chain name"""
        return cls.CHAIN_METADATA.get(chain_id, {}).get("name", f"chain-{chain_id}")
    
    @classmethod
    def get_execution_state(cls, chain_id: int) -> ChainExecutionState:
        """Get execution state for chain"""
        return cls.CHAIN_STATES.get(chain_id, ChainExecutionState.DISABLED)
    
    @classmethod
    def get_rpc_url(cls, chain_id: int) -> Optional[str]:
        """
        Get RPC URL for chain from environment.
        
        CRITICAL: Returns actual URL from .env, never defaults to localhost
        
        Args:
            chain_id: Chain ID
            
        Returns:
            str: RPC URL or None if not configured
        """
        metadata = cls.CHAIN_METADATA.get(chain_id)
        if not metadata:
            return None
        
        rpc_env_var = metadata.get("rpc_env")
        if not rpc_env_var:
            return None
        
        rpc_url = os.getenv(rpc_env_var)
        
        # SAFETY: Reject localhost/invalid URLs
        if rpc_url:
            if "localhost" in rpc_url.lower() or "127.0.0.1" in rpc_url:
                logger.warning(
                    f"[{cls.get_chain_name(chain_id)}] RPC URL contains localhost - rejected"
                )
                return None
            
            # Basic validation
            if not rpc_url.startswith(("http://", "https://")):
                logger.warning(
                    f"[{cls.get_chain_name(chain_id)}] Invalid RPC URL format: {rpc_url}"
                )
                return None
        
        return rpc_url
    
    @classmethod
    def get_enabled_chains(cls) -> list:
        """Get list of execution-enabled chain IDs"""
        return [
            chain_id
            for chain_id, state in cls.CHAIN_STATES.items()
            if state == ChainExecutionState.ENABLED
        ]
    
    @classmethod
    def get_configured_chains(cls) -> list:
        """Get list of configured chain IDs (enabled + configured)"""
        return [
            chain_id
            for chain_id, state in cls.CHAIN_STATES.items()
            if state in [ChainExecutionState.ENABLED, ChainExecutionState.CONFIGURED]
        ]
    
    @classmethod
    def get_executor_address(cls, chain_id: int) -> Optional[str]:
        """
        Get executor contract address for a chain.
        
        Args:
            chain_id: Chain ID
            
        Returns:
            str: Executor address or None
        """
        import os
        
        # Map chain IDs to environment variables
        executor_env_map = {
            1: 'EXECUTOR_ADDRESS_ETHEREUM',
            137: 'EXECUTOR_ADDRESS_POLYGON',
            42161: 'EXECUTOR_ADDRESS_ARBITRUM',
        }
        
        env_var = executor_env_map.get(chain_id)
        if not env_var:
            return None
        
        return os.getenv(env_var)
    
    def validate_rpc_health(self, chain_id: int) -> bool:
        """
        Validate RPC connectivity for a chain.
        
        Args:
            chain_id: Chain ID to validate
            
        Returns:
            bool: True if RPC is reachable, False otherwise
        """
        from web3 import Web3
        
        rpc_url = self.get_rpc_url(chain_id)
        if not rpc_url:
            logger.error(
                f"[{self.get_chain_name(chain_id)}] No RPC URL configured"
            )
            self.health_status[chain_id] = False
            return False
        
        try:
            w3 = Web3(Web3.HTTPProvider(rpc_url))
            is_connected = w3.is_connected()
            
            if is_connected:
                # Get block number as additional health check
                block_number = w3.eth.block_number
                logger.info(
                    f"[{self.get_chain_name(chain_id)}] RPC healthy - "
                    f"block #{block_number}"
                )
                self.validated_rpcs[chain_id] = rpc_url
                self.health_status[chain_id] = True
                return True
            else:
                logger.error(
                    f"[{self.get_chain_name(chain_id)}] RPC unreachable: {rpc_url}"
                )
                self.health_status[chain_id] = False
                return False
                
        except Exception as e:
            logger.error(
                f"[{self.get_chain_name(chain_id)}] RPC health check failed: {e}"
            )
            self.health_status[chain_id] = False
            return False
    
    def validate_all_configured_chains(self) -> Dict[int, bool]:
        """
        Validate RPC health for all configured chains.
        
        Returns:
            dict: {chain_id: health_status}
        """
        logger.info("=" * 70)
        logger.info("  VALIDATING CHAIN RPC HEALTH")
        logger.info("=" * 70)
        
        results = {}
        for chain_id in self.get_configured_chains():
            results[chain_id] = self.validate_rpc_health(chain_id)
        
        logger.info("=" * 70)
        return results
    
    @classmethod
    def print_execution_summary(cls):
        """Print chain execution configuration summary"""
        logger.info("=" * 70)
        logger.info("  CHAIN EXECUTION CONFIGURATION")
        logger.info("=" * 70)
        
        for chain_id in sorted(cls.CHAIN_STATES.keys()):
            state = cls.get_execution_state(chain_id)
            name = cls.get_chain_name(chain_id)
            
            if state == ChainExecutionState.ENABLED:
                status = "🟢 LIVE EXECUTION ENABLED"
            elif state == ChainExecutionState.CONFIGURED:
                status = "🟡 CONFIGURED (Execution Disabled)"
            else:
                status = "⚪ DISABLED"
            
            logger.info(f"  Chain {chain_id:6d} ({name:10s}): {status}")
        
        logger.info("=" * 70)


# Singleton instance
_registry = ChainRegistry()


def get_chain_registry() -> ChainRegistry:
    """Get global chain registry instance"""
    return _registry
