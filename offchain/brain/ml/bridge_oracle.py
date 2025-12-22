"""
Bridge Oracle - Cross-chain price oracle and fee estimation

Enhanced with Li.Fi integration for intent-based bridging support.
Provides accurate timing estimates for different bridge protocols including
solver-based (intent-based) bridges like Across, Stargate, and Hop.
"""
from routing.bridge_aggregator import BridgeAggregator
from routing.lifi_wrapper import LiFiWrapper
from decimal import Decimal

class BridgeOracle:
    """
    Provides cross-chain pricing data and bridge fee estimates.
    Acts as an oracle for cross-chain arbitrage opportunities.
    
    Enhanced with Li.Fi wrapper for:
    - Intent-based bridge detection (Across, Stargate, Hop)
    - Accurate timing estimates (30-60s for intent-based vs 10-30min for traditional)
    - Solver liquidity verification
    """
    
    def __init__(self, min_profit_threshold_usd=5.0):
        self.aggregator = BridgeAggregator()
        self.lifi = LiFiWrapper()
        self.min_profit_threshold_usd = Decimal(str(min_profit_threshold_usd))
    
    def get_bridge_cost(self, src_chain, dst_chain, token, amount):
        """
        Calculate total cost of bridging assets between chains.
        
        Args:
            src_chain (int): Source chain ID
            dst_chain (int): Destination chain ID
            token (str): Token address
            amount (str): Amount to bridge (in wei)
            
        Returns:
            dict: {
                'fee_usd': Decimal,
                'output_amount': str,
                'bridge_name': str,
                'estimated_time': int (seconds)
            } or None if route unavailable
        """
        
        try:
            route = self.aggregator.get_best_route(
                src_chain=src_chain,
                dst_chain=dst_chain,
                token=token,
                amount=amount,
                user="0x0000000000000000000000000000000000000000"  # Placeholder
            )
            
            if not route:
                return None
            
            fee_usd = Decimal(str(route.get('fee_usd', 0)))
            
            return {
                'fee_usd': fee_usd,
                'output_amount': route.get('est_output', '0'),
                'bridge_name': route.get('bridge', 'Unknown'),
                'estimated_time': self._estimate_bridge_time(route.get('bridge', 'Unknown'))
            }
            
        except Exception as e:
            print(f"⚠️ Bridge Oracle Error: {e}")
            return None
    
    def _estimate_bridge_time(self, bridge_name):
        """
        Estimate bridge completion time based on bridge type.
        
        Updated with accurate timing for intent-based bridges:
        - Intent-based (solver network): 30-120 seconds
        - Traditional (validator-based): 5-20 minutes
        
        Args:
            bridge_name (str): Name of the bridge protocol
            
        Returns:
            int: Estimated time in seconds
        """
        # Use LiFi wrapper for accurate estimates
        return self.lifi.estimate_bridge_time(bridge_name)
    
    def is_intent_based(self, bridge_name):
        """
        Check if a bridge uses intent-based architecture.
        
        Intent-based bridges (Across, Stargate, Hop) use market maker solvers
        who advance liquidity instantly, making them ideal for arbitrage.
        
        Args:
            bridge_name (str): Name of the bridge protocol
            
        Returns:
            bool: True if intent-based (fast), False if traditional (slow)
        """
        return self.lifi.is_intent_based_bridge(bridge_name)
    
    def is_bridge_profitable(self, src_price, dst_price, bridge_fee_usd, amount_usd):
        """
        Determine if cross-chain arbitrage is profitable after bridge fees.
        
        Args:
            src_price (Decimal): Token price on source chain
            dst_price (Decimal): Token price on destination chain
            bridge_fee_usd (Decimal): Bridge fee in USD
            amount_usd (Decimal): Trade size in USD
            
        Returns:
            tuple: (is_profitable: bool, expected_profit_usd: Decimal)
        """
        # Calculate price differential
        price_spread = dst_price - src_price
        
        # Calculate gross profit
        gross_profit = (price_spread / src_price) * amount_usd
        
        # Subtract bridge fees
        net_profit = gross_profit - bridge_fee_usd
        
        # Profitable if net profit exceeds configured threshold
        is_profitable = net_profit > self.min_profit_threshold_usd
        
        return is_profitable, net_profit
