"""
Bridge Manager - Unified interface for cross-chain routing
Wraps BridgeAggregator (Li.Fi) with additional logic for Titan system
"""
from routing.bridge_aggregator import BridgeAggregator

class BridgeManager:
    """
    Manages cross-chain bridge routing using Li.Fi aggregation.
    Provides a unified interface for the Brain to query optimal bridge routes.
    """
    
    def __init__(self):
        self.aggregator = BridgeAggregator()
    
    def get_route(self, src_chain, dst_chain, token_address, amount_str, user_address):
        """
        Find the best bridge route between chains.
        
        Args:
            src_chain (int): Source chain ID
            dst_chain (int): Destination chain ID
            token_address (str): Token contract address on source chain
            amount_str (str): Amount to bridge (in wei/raw units as string)
            user_address (str): User wallet address for route calculation
            
        Returns:
            dict: Route information including:
                - bridge: Name of bridge protocol
                - est_output: Expected output amount
                - fee_usd: Bridge fee in USD
                - tx_data: Transaction data for execution
            None: If no route found or error occurred
        """
        return self.aggregator.get_best_route(
            src_chain=src_chain,
            dst_chain=dst_chain,
            token=token_address,
            amount=amount_str,
            user=user_address
        )
