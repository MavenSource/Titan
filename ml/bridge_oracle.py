"""
Bridge Oracle - Cross-chain price oracle and fee estimation
Provides bridge fee data and route optimization for cross-chain arbitrage
"""
import requests
import os
from typing import Dict, Optional
import logging

logger = logging.getLogger("BridgeOracle")

class BridgeOracle:
    """
    Provides cross-chain bridge fee estimates and route optimization
    """
    
    def __init__(self):
        self.lifi_api_key = os.getenv("LIFI_API_KEY")
        self.base_url = "https://li.quest/v1"
        
    def estimate_bridge_fee(self, from_chain: int, to_chain: int, 
                          token: str, amount: int) -> Optional[Dict]:
        """
        Estimate bridge fee for a cross-chain transfer
        
        Args:
            from_chain: Source chain ID
            to_chain: Destination chain ID
            token: Token address
            amount: Amount to bridge (in wei)
            
        Returns:
            Dict with fee_usd, time_minutes, bridge_name
        """
        try:
            params = {
                "fromChain": from_chain,
                "toChain": to_chain,
                "fromToken": token,
                "toToken": token,
                "fromAmount": str(amount)
            }
            
            headers = {"x-lifi-api-key": self.lifi_api_key} if self.lifi_api_key else {}
            
            response = requests.get(
                f"{self.base_url}/quote",
                params=params,
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract fee information
                fee_costs = data.get('estimate', {}).get('feeCosts', [])
                total_fee_usd = sum(float(cost.get('amountUSD', 0)) for cost in fee_costs)
                
                # Estimate time
                time_estimate = data.get('estimate', {}).get('executionDuration', 300)
                time_minutes = time_estimate / 60
                
                # Bridge protocol
                bridge_name = data.get('tool', 'Unknown')
                
                return {
                    'fee_usd': total_fee_usd,
                    'time_minutes': time_minutes,
                    'bridge_name': bridge_name,
                    'estimated_output': data.get('estimate', {}).get('toAmount', 0)
                }
            else:
                logger.warning(f"Bridge fee estimation failed: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"Error estimating bridge fee: {e}")
            return None
    
    def get_cheapest_bridge(self, from_chain: int, to_chain: int,
                           token: str, amount: int) -> Optional[str]:
        """
        Find the cheapest bridge for a given route
        
        Args:
            from_chain: Source chain ID
            to_chain: Destination chain ID
            token: Token address
            amount: Amount to bridge
            
        Returns:
            Bridge name with lowest fees
        """
        estimate = self.estimate_bridge_fee(from_chain, to_chain, token, amount)
        if estimate:
            return estimate['bridge_name']
        return None
    
    def is_bridge_profitable(self, from_chain: int, to_chain: int,
                            token: str, amount: int, 
                            expected_price_diff: float) -> bool:
        """
        Determine if bridging would be profitable given expected price difference
        
        Args:
            from_chain: Source chain ID
            to_chain: Destination chain ID
            token: Token address
            amount: Amount to bridge
            expected_price_diff: Expected profit in USD
            
        Returns:
            bool: True if profitable after bridge fees
        """
        estimate = self.estimate_bridge_fee(from_chain, to_chain, token, amount)
        
        if not estimate:
            return False
        
        # Profit must exceed bridge fees
        return expected_price_diff > estimate['fee_usd']
    
    def get_bridge_time_estimate(self, from_chain: int, to_chain: int) -> float:
        """
        Get estimated bridge time in minutes
        
        Args:
            from_chain: Source chain ID
            to_chain: Destination chain ID
            
        Returns:
            float: Estimated time in minutes
        """
        # Common bridge time estimates (in minutes)
        bridge_times = {
            (1, 137): 7,    # ETH -> Polygon
            (1, 42161): 10, # ETH -> Arbitrum
            (1, 10): 7,     # ETH -> Optimism
            (137, 42161): 15, # Polygon -> Arbitrum
            (137, 10): 15,  # Polygon -> Optimism
        }
        
        # Return known time or default to 20 minutes
        return bridge_times.get((from_chain, to_chain), 20)
