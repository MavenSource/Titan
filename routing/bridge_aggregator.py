"""
Bridge Aggregator - Li.Fi API Integration

Direct REST API interface to Li.Fi for bridge route discovery.
Supports intent-based bridging via Across, Stargate, Hop, and 15+ protocols.

For full Python integration, see lifi_wrapper.py which provides additional
functionality like solver verification and timing estimates.
"""
import requests
import os
import logging

# Configure logging
logger = logging.getLogger(__name__)


class BridgeAggregator:
    """
    Direct REST API interface to Li.Fi bridge aggregation service.
    Li.Fi aggregates 15+ bridge protocols including intent-based options.
    """
    
    # Li.Fi REST API endpoints
    QUOTE_URL = "https://li.quest/v1/quote"
    ROUTES_URL = "https://li.quest/v1/advanced/routes"
    STATUS_URL = "https://li.quest/v1/status"

    def __init__(self):
        self.api_key = os.getenv("LIFI_API_KEY")
        if not self.api_key:
            logger.warning("LIFI_API_KEY not set in .env - API calls may be rate limited")

    def get_best_route(self, src_chain, dst_chain, token, amount, user, prefer_intent_based=True):
        """
        Finds the absolute best bridge route (Stargate, Across, Hop, etc.)
        
        Args:
            src_chain (int): Source chain ID (e.g., 137 for Polygon)
            dst_chain (int): Destination chain ID (e.g., 42161 for Arbitrum)
            token (str): Token address (same on both chains for arbitrage)
            amount (str): Amount in smallest unit (e.g., "1000000" for 1 USDC)
            user (str): User wallet address
            prefer_intent_based (bool): Prioritize intent-based bridges for speed
            
        Returns:
            dict: {
                'bridge': str,           # Bridge protocol name
                'est_output': str,       # Expected output amount
                'fee_usd': float,        # Total fees in USD
                'gas_cost_usd': float,   # Gas costs in USD
                'estimated_time': int,   # Estimated completion time in seconds
                'is_intent_based': bool, # Whether bridge uses solvers
                'tx_data': dict          # Raw transaction data to sign
            } or None if no route found
        """
        params = {
            "fromChain": src_chain,
            "toChain": dst_chain,
            "fromToken": token,
            "toToken": token,
            "fromAmount": amount,
            "fromAddress": user,
            "order": "FASTEST" if prefer_intent_based else "CHEAPEST"
        }
        
        # Add API key to headers if available
        headers = {}
        if self.api_key:
            headers["x-lifi-api-key"] = self.api_key
        
        try:
            res = requests.get(self.QUOTE_URL, params=params, headers=headers, timeout=30)
            
            if res.status_code == 200:
                data = res.json()
                
                # Parse response
                bridge_name = data.get('tool', 'unknown')
                estimate = data.get('estimate', {})
                
                # Calculate fees
                fee_costs = estimate.get('feeCosts', [])
                total_fee_usd = sum(float(cost.get('amountUSD', 0)) for cost in fee_costs)
                
                # Get gas costs
                gas_costs = estimate.get('gasCosts', [])
                total_gas_usd = sum(float(cost.get('amountUSD', 0)) for cost in gas_costs)
                
                # Determine if intent-based (import from config to avoid duplication)
                try:
                    from core.config import INTENT_BASED_BRIDGES
                    intent_based_bridges = list(INTENT_BASED_BRIDGES.keys())
                except ImportError:
                    # Fallback if config not available
                    intent_based_bridges = ['across', 'stargate', 'hop']
                is_intent_based = any(bridge in bridge_name.lower() for bridge in intent_based_bridges)
                
                # Estimate completion time
                if is_intent_based:
                    estimated_time = 60  # 1 minute for intent-based
                else:
                    estimated_time = 600  # 10 minutes for traditional
                
                return {
                    "bridge": bridge_name,
                    "est_output": estimate.get('toAmount', '0'),
                    "fee_usd": total_fee_usd,
                    "gas_cost_usd": total_gas_usd,
                    "estimated_time": estimated_time,
                    "is_intent_based": is_intent_based,
                    "tx_data": data.get('transactionRequest', {})
                }
            elif res.status_code == 404:
                logger.warning(f"No route found from chain {src_chain} to {dst_chain}")
                return None
            else:
                logger.error(f"Li.Fi API error: {res.status_code} - {res.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Li.Fi API timeout for route {src_chain} -> {dst_chain}")
            return None
        except Exception as e:
            logger.error(f"Bridge aggregator error: {e}")
            return None
    
    def get_route_status(self, tx_hash, from_chain, to_chain):
        """
        Check the status of a bridge transaction.
        
        Args:
            tx_hash (str): Transaction hash on source chain
            from_chain (int): Source chain ID
            to_chain (int): Destination chain ID
            
        Returns:
            dict: {
                'status': str,  # 'PENDING', 'DONE', 'FAILED'
                'substatus': str,
                'sending': dict,
                'receiving': dict
            } or None if check failed
        """
        params = {
            "txHash": tx_hash,
            "fromChain": from_chain,
            "toChain": to_chain
        }
        
        headers = {}
        if self.api_key:
            headers["x-lifi-api-key"] = self.api_key
        
        try:
            res = requests.get(self.STATUS_URL, params=params, headers=headers, timeout=15)
            if res.status_code == 200:
                return res.json()
            else:
                logger.error(f"Status check failed: {res.status_code}")
                return None
        except Exception as e:
            logger.error(f"Status check error: {e}")
            return None