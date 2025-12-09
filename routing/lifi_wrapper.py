"""
LiFi Python Wrapper - Intent-Based Bridging for Cross-Chain Arbitrage

This module provides a Python interface to the Li.Fi SDK for cross-chain
asset bridging. It supports intent-based bridging via protocols like Across,
Stargate, and Hop, which enable near-instant cross-chain transfers through
market maker solver networks.

Key Features:
- Intent-based bridging with 30-120 second settlement times
- Automatic best route selection from 15+ bridge protocols
- Solver liquidity verification
- Route validation and cost estimation
- Integration with Titan AI brain for arbitrage decisions
"""

import subprocess
import json
import os
import logging
from decimal import Decimal
from typing import Dict, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)


class LiFiWrapper:
    """
    Python wrapper for Li.Fi JavaScript SDK.
    Calls Node.js scripts to interact with the Li.Fi API.
    """
    
    def __init__(self):
        self.node_script_dir = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'execution'
        )
    
    def get_quote(
        self, 
        from_chain: int, 
        to_chain: int, 
        from_token: str, 
        to_token: str, 
        amount: str,
        prefer_intent_based: bool = True
    ) -> Optional[Dict]:
        """
        Get a bridge quote without executing the transaction.
        
        Args:
            from_chain: Source chain ID (e.g., 137 for Polygon)
            to_chain: Destination chain ID (e.g., 42161 for Arbitrum)
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to bridge (in smallest unit, e.g., "1000000" for 1 USDC)
            prefer_intent_based: Prefer intent-based bridges for faster settlement
            
        Returns:
            dict: {
                'success': bool,
                'bridge_name': str,
                'from_amount': str,
                'to_amount': str,
                'to_amount_min': str,
                'gas_cost_usd': float,
                'estimated_time': int (seconds),
                'error': str (if failed)
            }
        """
        try:
            # Validate inputs to prevent code injection
            if not isinstance(from_chain, int) or not isinstance(to_chain, int):
                return None
            if not from_token.startswith('0x') or not to_token.startswith('0x'):
                return None
            if not amount.isdigit():
                return None
            
            # Build parameters as JSON for safe passing
            params = json.dumps({
                'from_chain': from_chain,
                'to_chain': to_chain,
                'from_token': from_token,
                'to_token': to_token,
                'amount': amount,
                'prefer_intent_based': prefer_intent_based
            })
            
            # Call Node.js script via subprocess with JSON parameter passing
            script = f"""
            const {{ LifiExecutionEngine }} = require('./lifi_manager');
            const params = {params};
            LifiExecutionEngine.getQuote(
                params.from_chain, 
                params.to_chain, 
                params.from_token, 
                params.to_token, 
                params.amount,
                {{ preferIntentBased: params.prefer_intent_based }}
            ).then(result => console.log(JSON.stringify(result)));
            """
            
            result = subprocess.run(
                ['node', '-e', script],
                cwd=self.node_script_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                logger.warning("LiFi quote error: %s", result.stderr)
                return None
            
            quote = json.loads(result.stdout.strip())
            return quote
            
        except subprocess.TimeoutExpired:
            logger.warning("LiFi quote request timed out")
            return None
        except Exception as e:
            logger.error("LiFi quote failed: %s", e)
            return None
    
    def verify_route(
        self, 
        from_chain: int, 
        to_chain: int, 
        token: str
    ) -> Tuple[bool, bool, int]:
        """
        Verify if a bridge route exists and check for intent-based options.
        
        Args:
            from_chain: Source chain ID
            to_chain: Destination chain ID
            token: Token address (same on both chains for arbitrage)
            
        Returns:
            tuple: (route_exists: bool, has_intent_based: bool, route_count: int)
        """
        try:
            script = f"""
            const {{ LifiDiscovery }} = require('./lifi_discovery');
            const discovery = new LifiDiscovery();
            discovery.verifyConnection({from_chain}, {to_chain}, '{token}')
                .then(result => console.log(JSON.stringify(result)));
            """
            
            result = subprocess.run(
                ['node', '-e', script],
                cwd=self.node_script_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return False, False, 0
            
            # Parse last line (actual JSON output, ignoring logs)
            lines = result.stdout.strip().split('\n')
            json_line = lines[-1]
            verification = json.loads(json_line)
            
            if verification.get('success'):
                return (
                    True,
                    verification.get('hasIntentBased', False),
                    verification.get('routeCount', 0)
                )
            else:
                return False, False, 0
                
        except Exception as e:
            logger.warning("Route verification failed: %s", e)
            return False, False, 0
    
    def estimate_bridge_time(self, bridge_name: str) -> int:
        """
        Estimate bridge completion time based on protocol type.
        
        Args:
            bridge_name: Name of the bridge protocol
            
        Returns:
            int: Estimated time in seconds
        """
        # Intent-based bridges (near-instant via solvers)
        intent_based = {
            'across': 30,        # 30 seconds (fastest)
            'stargate': 60,      # 1 minute
            'hop': 120,          # 2 minutes
        }
        
        # Traditional bridges (wait for validators)
        traditional = {
            'synapse': 900,      # 15 minutes
            'cbridge': 1200,     # 20 minutes
            'multichain': 600,   # 10 minutes
            'connext': 300,      # 5 minutes
            'anyswap': 600,      # 10 minutes
        }
        
        bridge_lower = bridge_name.lower()
        
        # Check intent-based first (priority)
        for key, time in intent_based.items():
            if key in bridge_lower:
                return time
        
        # Check traditional
        for key, time in traditional.items():
            if key in bridge_lower:
                return time
        
        # Default: assume 10 minutes for unknown bridges
        return 600
    
    def is_intent_based_bridge(self, bridge_name: str) -> bool:
        """
        Check if a bridge uses intent-based architecture (solvers).
        
        Args:
            bridge_name: Name of the bridge protocol
            
        Returns:
            bool: True if intent-based (fast), False if traditional (slow)
        """
        intent_based_bridges = ['across', 'stargate', 'hop']
        return any(bridge in bridge_name.lower() for bridge in intent_based_bridges)
    
    def calculate_total_cost(
        self,
        bridge_fee_usd: Decimal,
        src_gas_cost_usd: Decimal,
        dst_gas_cost_usd: Decimal,
        flash_loan_fee_bps: int = 0
    ) -> Decimal:
        """
        Calculate total cost of cross-chain arbitrage operation.
        
        Args:
            bridge_fee_usd: Bridge/solver fee in USD
            src_gas_cost_usd: Gas cost on source chain in USD
            dst_gas_cost_usd: Gas cost on destination chain in USD
            flash_loan_fee_bps: Flash loan fee in basis points (e.g., 5 = 0.05%)
            
        Returns:
            Decimal: Total cost in USD
        """
        total = bridge_fee_usd + src_gas_cost_usd + dst_gas_cost_usd
        return total
    
    def is_arbitrage_profitable(
        self,
        src_price: Decimal,
        dst_price: Decimal,
        amount_usd: Decimal,
        bridge_cost: Dict,
        min_profit_usd: Decimal = Decimal('5.0')
    ) -> Tuple[bool, Decimal]:
        """
        Determine if cross-chain arbitrage is profitable after all costs.
        
        Args:
            src_price: Token price on source chain (USD)
            dst_price: Token price on destination chain (USD)
            amount_usd: Trade size in USD
            bridge_cost: Dict with 'fee_usd' from get_quote()
            min_profit_usd: Minimum profit threshold in USD
            
        Returns:
            tuple: (is_profitable: bool, net_profit: Decimal)
        """
        # Validate prices are positive and non-zero
        if src_price <= 0 or dst_price <= 0:
            return False, Decimal('0')
        
        price_spread_pct = (dst_price - src_price) / src_price
        gross_profit = price_spread_pct * amount_usd
        
        # Subtract bridge and gas costs
        bridge_fee = Decimal(str(bridge_cost.get('gas_cost_usd', 0)))
        net_profit = gross_profit - bridge_fee
        
        # Check if exceeds minimum threshold
        is_profitable = net_profit > min_profit_usd
        
        return is_profitable, net_profit


# Singleton instance for easy import
lifi_wrapper = LiFiWrapper()


def get_cross_chain_quote(from_chain: int, to_chain: int, token: str, amount: str) -> Optional[Dict]:
    """
    Convenience function to get a cross-chain bridge quote.
    
    Usage:
        >>> from routing.lifi_wrapper import get_cross_chain_quote
        >>> quote = get_cross_chain_quote(137, 42161, '0x...', '1000000000')
        >>> if quote and quote['success']:
        >>>     print(f"Bridge fee: ${quote['gas_cost_usd']}")
    """
    return lifi_wrapper.get_quote(from_chain, to_chain, token, token, amount)


def verify_cross_chain_route(from_chain: int, to_chain: int, token: str) -> bool:
    """
    Convenience function to verify if a cross-chain route exists.
    
    Usage:
        >>> from routing.lifi_wrapper import verify_cross_chain_route
        >>> if verify_cross_chain_route(137, 42161, usdc_address):
        >>>     print("Route available!")
    """
    exists, has_intent, count = lifi_wrapper.verify_route(from_chain, to_chain, token)
    return exists
