"""
Test Suite for Li.Fi Integration - Intent-Based Bridging

Tests the Python wrapper for Li.Fi SDK and bridge oracle functionality.
"""

import unittest
from decimal import Decimal
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from routing.lifi_wrapper import LiFiWrapper
from ml.bridge_oracle import BridgeOracle


class TestLiFiWrapper(unittest.TestCase):
    """Test Li.Fi Python wrapper functionality"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.wrapper = LiFiWrapper()
    
    def test_estimate_bridge_time_intent_based(self):
        """Test timing estimates for intent-based bridges"""
        # Across should be fastest (30 seconds)
        self.assertEqual(self.wrapper.estimate_bridge_time('across'), 30)
        
        # Stargate should be 60 seconds
        self.assertEqual(self.wrapper.estimate_bridge_time('stargate'), 60)
        
        # Hop should be 120 seconds
        self.assertEqual(self.wrapper.estimate_bridge_time('hop'), 120)
    
    def test_estimate_bridge_time_traditional(self):
        """Test timing estimates for traditional bridges"""
        # Synapse should be 900 seconds (15 minutes)
        self.assertEqual(self.wrapper.estimate_bridge_time('synapse'), 900)
        
        # Cbridge should be 1200 seconds (20 minutes)
        self.assertEqual(self.wrapper.estimate_bridge_time('cbridge'), 1200)
        
        # Unknown bridge should default to 600 seconds
        self.assertEqual(self.wrapper.estimate_bridge_time('unknown_bridge'), 600)
    
    def test_is_intent_based_bridge(self):
        """Test intent-based bridge detection"""
        # Intent-based bridges should return True
        self.assertTrue(self.wrapper.is_intent_based_bridge('across'))
        self.assertTrue(self.wrapper.is_intent_based_bridge('stargate'))
        self.assertTrue(self.wrapper.is_intent_based_bridge('hop'))
        
        # Traditional bridges should return False
        self.assertFalse(self.wrapper.is_intent_based_bridge('synapse'))
        self.assertFalse(self.wrapper.is_intent_based_bridge('cbridge'))
        self.assertFalse(self.wrapper.is_intent_based_bridge('multichain'))
    
    def test_calculate_total_cost(self):
        """Test total cost calculation"""
        bridge_fee = Decimal('0.50')
        src_gas = Decimal('0.20')
        dst_gas = Decimal('0.15')
        
        total = self.wrapper.calculate_total_cost(bridge_fee, src_gas, dst_gas)
        
        self.assertEqual(total, Decimal('0.85'))
    
    def test_is_arbitrage_profitable_positive(self):
        """Test profitability check with positive scenario"""
        src_price = Decimal('0.998')  # USDC on Polygon
        dst_price = Decimal('1.002')  # USDC on Arbitrum
        amount_usd = Decimal('10000')
        bridge_cost = {'gas_cost_usd': 0.50}
        min_profit = Decimal('5.0')
        
        is_profitable, net_profit = self.wrapper.is_arbitrage_profitable(
            src_price, dst_price, amount_usd, bridge_cost, min_profit
        )
        
        # Price spread: (1.002 - 0.998) / 0.998 = 0.004 = 0.4%
        # Gross profit: 0.004 * 10000 = $40
        # Net profit: 40 - 0.50 = $39.50
        self.assertTrue(is_profitable)
        self.assertGreater(net_profit, min_profit)
    
    def test_is_arbitrage_profitable_negative(self):
        """Test profitability check with negative scenario"""
        src_price = Decimal('1.000')
        dst_price = Decimal('1.001')  # Only 0.1% spread
        amount_usd = Decimal('1000')
        bridge_cost = {'gas_cost_usd': 2.00}  # High bridge cost
        min_profit = Decimal('5.0')
        
        is_profitable, net_profit = self.wrapper.is_arbitrage_profitable(
            src_price, dst_price, amount_usd, bridge_cost, min_profit
        )
        
        # Gross profit: 0.001 * 1000 = $1
        # Net profit: 1 - 2 = -$1 (loss)
        self.assertFalse(is_profitable)
        self.assertLess(net_profit, min_profit)
    
    def test_is_arbitrage_profitable_zero_src_price(self):
        """Test profitability check with zero source price (edge case)"""
        src_price = Decimal('0')
        dst_price = Decimal('1.000')
        amount_usd = Decimal('10000')
        bridge_cost = {'gas_cost_usd': 0.50}
        min_profit = Decimal('5.0')
        
        is_profitable, net_profit = self.wrapper.is_arbitrage_profitable(
            src_price, dst_price, amount_usd, bridge_cost, min_profit
        )
        
        # Should handle zero/negative price gracefully
        self.assertFalse(is_profitable)
        self.assertEqual(net_profit, Decimal('0'))
    
    def test_is_arbitrage_profitable_negative_price(self):
        """Test profitability check with negative price (edge case)"""
        src_price = Decimal('-1.000')
        dst_price = Decimal('1.000')
        amount_usd = Decimal('10000')
        bridge_cost = {'gas_cost_usd': 0.50}
        min_profit = Decimal('5.0')
        
        is_profitable, net_profit = self.wrapper.is_arbitrage_profitable(
            src_price, dst_price, amount_usd, bridge_cost, min_profit
        )
        
        # Should handle negative price gracefully
        self.assertFalse(is_profitable)
        self.assertEqual(net_profit, Decimal('0'))


class TestBridgeOracle(unittest.TestCase):
    """Test Bridge Oracle with Li.Fi integration"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.oracle = BridgeOracle(min_profit_threshold_usd=5.0)
    
    def test_estimate_bridge_time_uses_lifi(self):
        """Test that bridge oracle uses Li.Fi wrapper for timing"""
        time_across = self.oracle._estimate_bridge_time('across')
        self.assertEqual(time_across, 30)
        
        # Test traditional bridge
        time_synapse = self.oracle._estimate_bridge_time('synapse')
        self.assertEqual(time_synapse, 900)
    
    def test_is_intent_based(self):
        """Test intent-based detection in bridge oracle"""
        self.assertTrue(self.oracle.is_intent_based('across'))
        self.assertTrue(self.oracle.is_intent_based('stargate'))
        self.assertFalse(self.oracle.is_intent_based('synapse'))


class TestLiFiConfiguration(unittest.TestCase):
    """Test Li.Fi configuration in core/config.py"""
    
    def test_config_imports(self):
        """Test that Li.Fi configuration can be imported"""
        try:
            from core.config import (
                LIFI_SUPPORTED_CHAINS,
                INTENT_BASED_BRIDGES,
                TRADITIONAL_BRIDGES,
                BRIDGE_PRIORITY_FOR_ARBITRAGE,
                MAX_INTENT_BASED_TRADE_SIZE
            )
            
            # Verify expected structures
            self.assertIsInstance(LIFI_SUPPORTED_CHAINS, list)
            self.assertIsInstance(INTENT_BASED_BRIDGES, dict)
            self.assertIsInstance(TRADITIONAL_BRIDGES, dict)
            self.assertIsInstance(BRIDGE_PRIORITY_FOR_ARBITRAGE, list)
            self.assertIsInstance(MAX_INTENT_BASED_TRADE_SIZE, dict)
            
            # Verify intent-based bridges are configured
            self.assertIn('across', INTENT_BASED_BRIDGES)
            self.assertIn('stargate', INTENT_BASED_BRIDGES)
            self.assertIn('hop', INTENT_BASED_BRIDGES)
            
            # Verify timing information exists
            self.assertIn('typical_time_seconds', INTENT_BASED_BRIDGES['across'])
            
            # Verify Across is fastest (30 seconds)
            across_time = INTENT_BASED_BRIDGES['across']['typical_time_seconds']
            self.assertEqual(across_time, 30)
            
        except (ImportError, ModuleNotFoundError) as e:
            # Skip this test if dependencies are not available
            self.skipTest(f"Skipping config test due to missing dependencies: {e}")


if __name__ == '__main__':
    unittest.main(verbosity=2)
