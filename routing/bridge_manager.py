"""
Bridge Manager - Wrapper for bridge functionality
Combines BridgeAggregator and BridgeOracle
"""
from routing.bridge_aggregator import BridgeAggregator
from ml.bridge_oracle import BridgeOracle

class BridgeManager:
    """
    Unified bridge management interface
    """
    
    def __init__(self):
        self.aggregator = BridgeAggregator()
        self.oracle = BridgeOracle()
    
    def get_best_route(self, src_chain, dst_chain, token, amount, user):
        """Get best bridge route"""
        return self.aggregator.get_best_route(src_chain, dst_chain, token, amount, user)
    
    def estimate_fee(self, from_chain, to_chain, token, amount):
        """Estimate bridge fee"""
        return self.oracle.estimate_bridge_fee(from_chain, to_chain, token, amount)
    
    def is_profitable(self, from_chain, to_chain, token, amount, expected_diff):
        """Check if bridge is profitable"""
        return self.oracle.is_bridge_profitable(from_chain, to_chain, token, amount, expected_diff)
