#!/usr/bin/env python3
"""
Titan 90-Day Historical Simulation Engine
==========================================

Replays Titan system logic using historical blockchain data to validate
performance and compare system features over a 90-day period.

Features simulated:
- Opportunity detection across chains
- Profit calculations with real fees
- Liquidity validation
- Gas cost estimation
- ML-based optimization
- Cross-chain bridge routing
- Transaction success probability
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from decimal import Decimal, getcontext
import pandas as pd
import numpy as np
from dataclasses import dataclass, asdict

# Set precision for financial calculations
getcontext().prec = 28

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [SimEngine] %(message)s'
)
logger = logging.getLogger("SimulationEngine")


@dataclass
class OpportunityResult:
    """Result of a simulated arbitrage opportunity"""
    date: str
    chain_id: int
    token_pair: str
    loan_amount_usd: float
    gross_revenue_usd: float
    gas_cost_usd: float
    bridge_fee_usd: float
    flash_loan_fee_usd: float
    net_profit_usd: float
    is_profitable: bool
    success_probability: float
    executed: bool
    ml_optimized: bool


@dataclass
class DailyMetrics:
    """Daily performance metrics"""
    date: str
    opportunities_found: int
    opportunities_executed: int
    successful_trades: int
    failed_trades: int
    total_profit_usd: float
    total_gas_cost_usd: float
    average_profit_per_trade: float
    success_rate: float
    avg_gas_price_gwei: float


class TitanSimulationEngine:
    """
    Simulates Titan system behavior using historical data.
    """
    
    def __init__(self, config: Dict = None):
        """
        Initialize simulation engine.
        
        Args:
            config: Configuration dictionary with simulation parameters
        """
        self.config = config or self._default_config()
        self.results: List[OpportunityResult] = []
        self.daily_metrics: List[DailyMetrics] = []
        
        # System feature flags (matching real Titan capabilities)
        self.features = {
            'ml_gas_prediction': True,
            'ml_profit_optimization': True,
            'cross_chain_bridges': True,
            'multi_dex_routing': True,
            'flash_loans': True,
            'liquidity_validation': True,
            'transaction_simulation': True,
            'mev_protection': False,  # Optional
            'adaptive_slippage': True
        }
        
        # Opportunity simulation parameters (configurable)
        self.opportunity_params = {
            'base_spread_pct': self.config.get('base_spread_pct', 0.03),  # 3%
            'spread_random_min': self.config.get('spread_random_min', 0.8),
            'spread_random_max': self.config.get('spread_random_max', 2.0),
            'min_spread_pct': self.config.get('min_spread_pct', 0.015)  # 1.5%
        }
        
        logger.info("🔧 Simulation Engine Initialized")
        logger.info(f"   Features enabled: {sum(self.features.values())}/{len(self.features)}")
    
    def _default_config(self) -> Dict:
        """Default simulation configuration"""
        return {
            'min_profit_threshold_usd': 5.0,
            'max_gas_price_gwei': 500,
            'flash_loan_fee_rate': 0.0,  # Balancer V3 = 0%
            'min_success_probability': 0.7,
            'slippage_tolerance': 0.01,  # 1%
            'gas_buffer_multiplier': 1.2,
            'base_gas_units': 390000,
            'bridge_fee_avg_usd': 2.5,
            'execution_mode': 'PAPER'
        }
    
    def simulate_opportunity_detection(
        self,
        snapshot: Dict,
        pair_data: Dict
    ) -> List[Dict]:
        """
        Simulate Titan's opportunity detection logic.
        
        Args:
            snapshot: Historical market snapshot
            pair_data: DEX pair price data
            
        Returns:
            List of detected opportunities
        """
        opportunities = []
        
        # Simulate price differential detection (simplified)
        # In real Titan, this scans multiple DEXs and chains
        if not pair_data or 'token0_price' not in pair_data:
            return opportunities
        
        token0_price = pair_data['token0_price']
        gas_price = snapshot.get('gas_price_gwei', 50)
        
        # Simulate price spread (historical data shows spreads)
        # Use random variation to simulate arbitrage opportunities
        base_spread = self.opportunity_params['base_spread_pct']
        random_factor = np.random.uniform(
            self.opportunity_params['spread_random_min'],
            self.opportunity_params['spread_random_max']
        )
        simulated_spread = base_spread * random_factor
        
        if simulated_spread > self.opportunity_params['min_spread_pct']:
            opportunity = {
                'token_pair': 'USDC/WETH',
                'price_a': token0_price,
                'price_b': token0_price * (1 + simulated_spread),
                'spread_pct': simulated_spread * 100,
                'gas_price_gwei': gas_price,
                'chain_id': snapshot['chain_id']
            }
            opportunities.append(opportunity)
        
        return opportunities
    
    def calculate_optimal_loan_size(
        self,
        spread_pct: float,
        liquidity: float,
        gas_price_gwei: float
    ) -> float:
        """
        Calculate optimal flash loan size using ML-based optimization.
        Simulates the RL agent's decision-making.
        
        Args:
            spread_pct: Price spread percentage
            liquidity: Available liquidity
            gas_price_gwei: Current gas price
            
        Returns:
            Optimal loan size in USD
        """
        # Base calculation
        base_loan = 10000  # Start with $10k
        
        # Adjust for spread (higher spread = larger loan)
        spread_factor = min(spread_pct / 2, 2.0)  # Cap at 2x
        
        # Adjust for liquidity (don't exceed 10% of pool)
        liquidity_usd = liquidity / 1e6  # Approximate conversion
        max_loan = liquidity_usd * 0.1
        
        # Adjust for gas (lower loan if gas is high)
        gas_factor = max(0.5, 1 - (gas_price_gwei / 1000))
        
        optimal_loan = base_loan * spread_factor * gas_factor
        optimal_loan = min(optimal_loan, max_loan)
        optimal_loan = max(optimal_loan, 1000)  # Minimum $1k
        
        return optimal_loan
    
    def simulate_profit_calculation(
        self,
        opportunity: Dict,
        loan_amount: float,
        liquidity: float
    ) -> Tuple[float, Dict]:
        """
        Simulate Titan's profit calculation engine.
        
        Args:
            opportunity: Opportunity data
            loan_amount: Flash loan amount in USD
            liquidity: Available liquidity
            
        Returns:
            Tuple of (net_profit, fee_breakdown)
        """
        spread = opportunity['spread_pct'] / 100
        gas_price = opportunity['gas_price_gwei']
        
        # 1. Calculate gross revenue
        gross_revenue = loan_amount * (1 + spread)
        
        # 2. Calculate costs
        # Gas cost (varies by chain)
        chain_gas_cost_map = {
            1: 0.0005,    # Ethereum (expensive)
            137: 0.00003, # Polygon (cheap)
            42161: 0.0001,# Arbitrum
            10: 0.00005,  # Optimism
        }
        gas_cost_per_unit = chain_gas_cost_map.get(
            opportunity['chain_id'], 0.0001
        )
        gas_cost_usd = (
            self.config['base_gas_units'] * 
            gas_price * 
            gas_cost_per_unit * 
            self.config['gas_buffer_multiplier']
        )
        
        # Flash loan fee
        flash_loan_fee = loan_amount * self.config['flash_loan_fee_rate']
        
        # Bridge fee (if cross-chain)
        bridge_fee = self.config['bridge_fee_avg_usd'] if spread > 0.03 else 0
        
        # Slippage impact
        slippage_cost = loan_amount * self.config['slippage_tolerance']
        
        # 3. Net profit
        total_costs = gas_cost_usd + flash_loan_fee + bridge_fee + slippage_cost
        net_profit = gross_revenue - loan_amount - total_costs
        
        fee_breakdown = {
            'gross_revenue': gross_revenue,
            'gas_cost': gas_cost_usd,
            'flash_loan_fee': flash_loan_fee,
            'bridge_fee': bridge_fee,
            'slippage_cost': slippage_cost,
            'total_costs': total_costs
        }
        
        return net_profit, fee_breakdown
    
    def estimate_success_probability(
        self,
        net_profit: float,
        gas_price_gwei: float,
        liquidity_ratio: float
    ) -> float:
        """
        Estimate probability of successful execution.
        Simulates ML model prediction.
        
        Args:
            net_profit: Calculated net profit
            gas_price_gwei: Current gas price
            liquidity_ratio: Used liquidity / available liquidity
            
        Returns:
            Success probability (0.0 to 1.0)
        """
        base_probability = 0.85  # Base success rate
        
        # Adjust for profit margin (higher profit = more cushion)
        profit_factor = min(net_profit / 100, 0.1)  # Up to +10%
        
        # Adjust for gas price (higher gas = more risk)
        gas_penalty = min(gas_price_gwei / 500, 0.15)  # Up to -15%
        
        # Adjust for liquidity (higher usage = more slippage risk)
        liquidity_penalty = liquidity_ratio * 0.2  # Up to -20%
        
        probability = base_probability + profit_factor - gas_penalty - liquidity_penalty
        probability = max(0.5, min(0.99, probability))
        
        return probability
    
    def simulate_execution_decision(
        self,
        net_profit: float,
        success_probability: float,
        gas_price_gwei: float
    ) -> bool:
        """
        Decide whether to execute based on Titan's logic.
        
        Args:
            net_profit: Expected net profit
            success_probability: Probability of success
            gas_price_gwei: Current gas price
            
        Returns:
            True if should execute, False otherwise
        """
        # Check minimum profit threshold
        if net_profit < self.config['min_profit_threshold_usd']:
            return False
        
        # Check gas price limit
        if gas_price_gwei > self.config['max_gas_price_gwei']:
            return False
        
        # Check success probability
        if success_probability < self.config['min_success_probability']:
            return False
        
        # Expected value check
        expected_value = net_profit * success_probability
        if expected_value < self.config['min_profit_threshold_usd'] * 0.8:
            return False
        
        return True
    
    def simulate_execution_outcome(
        self,
        success_probability: float
    ) -> bool:
        """
        Simulate whether execution succeeds or fails.
        
        Args:
            success_probability: Probability of success
            
        Returns:
            True if successful, False if failed
        """
        return np.random.random() < success_probability
    
    def simulate_day(
        self,
        date: datetime,
        historical_data: Dict
    ) -> DailyMetrics:
        """
        Simulate one day of Titan operations.
        
        Args:
            date: Date to simulate
            historical_data: Historical market data for that day
            
        Returns:
            Daily performance metrics
        """
        logger.info(f"\n📅 Simulating day: {date.strftime('%Y-%m-%d')}")
        
        opportunities_found = 0
        opportunities_executed = 0
        successful_trades = 0
        failed_trades = 0
        total_profit = 0.0
        total_gas_cost = 0.0
        
        # Extract data from historical snapshot
        gas_price = historical_data.get('gas_price_gwei', 50)
        pair_prices = historical_data.get('pair_prices', {})
        liquidity = historical_data.get('liquidity', {})
        
        # Get first pair (simplified - real Titan scans all pairs)
        if not pair_prices:
            logger.warning("No pair price data available")
            return self._empty_daily_metrics(date)
        
        first_pair_key = list(pair_prices.keys())[0]
        pair_data = pair_prices[first_pair_key]
        
        # Get liquidity (use first available)
        liquidity_value = list(liquidity.values())[0] if liquidity else 1e9
        
        # Simulate multiple scanning intervals per day
        # Default: scan every 15 minutes (96 scans per day)
        scan_interval_minutes = self.config.get('scan_interval_minutes', 15)
        scans_per_day = (24 * 60) // scan_interval_minutes
        
        for scan in range(scans_per_day):
            # Detect opportunities
            opportunities = self.simulate_opportunity_detection(
                historical_data,
                pair_data
            )
            
            opportunities_found += len(opportunities)
            
            for opp in opportunities:
                # Calculate optimal loan size
                loan_amount = self.calculate_optimal_loan_size(
                    opp['spread_pct'],
                    liquidity_value,
                    gas_price
                )
                
                # Calculate profit
                net_profit, fees = self.simulate_profit_calculation(
                    opp,
                    loan_amount,
                    liquidity_value
                )
                
                # Estimate success probability
                liquidity_ratio = loan_amount / (liquidity_value / 1e6)
                success_prob = self.estimate_success_probability(
                    net_profit,
                    gas_price,
                    liquidity_ratio
                )
                
                # Decide whether to execute
                should_execute = self.simulate_execution_decision(
                    net_profit,
                    success_prob,
                    gas_price
                )
                
                if should_execute:
                    opportunities_executed += 1
                    
                    # Simulate execution outcome
                    execution_success = self.simulate_execution_outcome(success_prob)
                    
                    if execution_success:
                        successful_trades += 1
                        total_profit += net_profit
                        total_gas_cost += fees['gas_cost']
                    else:
                        failed_trades += 1
                        total_gas_cost += fees['gas_cost']  # Still pay gas on failure
                    
                    # Record result
                    result = OpportunityResult(
                        date=date.strftime('%Y-%m-%d'),
                        chain_id=opp['chain_id'],
                        token_pair=opp['token_pair'],
                        loan_amount_usd=loan_amount,
                        gross_revenue_usd=fees['gross_revenue'],
                        gas_cost_usd=fees['gas_cost'],
                        bridge_fee_usd=fees['bridge_fee'],
                        flash_loan_fee_usd=fees['flash_loan_fee'],
                        net_profit_usd=net_profit if execution_success else -fees['gas_cost'],
                        is_profitable=execution_success,
                        success_probability=success_prob,
                        executed=True,
                        ml_optimized=self.features['ml_profit_optimization']
                    )
                    self.results.append(result)
        
        # Calculate daily metrics
        success_rate = (
            successful_trades / opportunities_executed 
            if opportunities_executed > 0 else 0
        )
        avg_profit = (
            total_profit / successful_trades 
            if successful_trades > 0 else 0
        )
        
        metrics = DailyMetrics(
            date=date.strftime('%Y-%m-%d'),
            opportunities_found=opportunities_found,
            opportunities_executed=opportunities_executed,
            successful_trades=successful_trades,
            failed_trades=failed_trades,
            total_profit_usd=total_profit,
            total_gas_cost_usd=total_gas_cost,
            average_profit_per_trade=avg_profit,
            success_rate=success_rate,
            avg_gas_price_gwei=gas_price
        )
        
        logger.info(f"   Opportunities: {opportunities_found} found, {opportunities_executed} executed")
        logger.info(f"   Success: {successful_trades}/{opportunities_executed} ({success_rate*100:.1f}%)")
        logger.info(f"   Profit: ${total_profit:.2f}")
        
        return metrics
    
    def _empty_daily_metrics(self, date: datetime) -> DailyMetrics:
        """Return empty metrics for days with no data"""
        return DailyMetrics(
            date=date.strftime('%Y-%m-%d'),
            opportunities_found=0,
            opportunities_executed=0,
            successful_trades=0,
            failed_trades=0,
            total_profit_usd=0.0,
            total_gas_cost_usd=0.0,
            average_profit_per_trade=0.0,
            success_rate=0.0,
            avg_gas_price_gwei=0.0
        )
    
    def run_90_day_simulation(
        self,
        start_date: datetime,
        historical_data: pd.DataFrame
    ) -> Dict:
        """
        Run complete 90-day simulation.
        
        Args:
            start_date: Starting date
            historical_data: DataFrame with historical market data
            
        Returns:
            Complete simulation results
        """
        logger.info("=" * 70)
        logger.info("🚀 STARTING 90-DAY TITAN SIMULATION")
        logger.info("=" * 70)
        logger.info(f"Start Date: {start_date.strftime('%Y-%m-%d')}")
        logger.info(f"Features Enabled: {json.dumps(self.features, indent=2)}")
        logger.info("=" * 70)
        
        self.results = []
        self.daily_metrics = []
        
        # Convert historical data to dict for easier access
        historical_dict = {}
        for _, row in historical_data.iterrows():
            date_str = row['date']
            historical_dict[date_str] = row.to_dict()
        
        # Simulate each day
        for day in range(90):
            current_date = start_date + timedelta(days=day)
            date_str = current_date.strftime('%Y-%m-%d')
            
            if date_str in historical_dict:
                daily_data = historical_dict[date_str]
                metrics = self.simulate_day(current_date, daily_data)
            else:
                logger.warning(f"No historical data for {date_str}, skipping")
                metrics = self._empty_daily_metrics(current_date)
            
            self.daily_metrics.append(metrics)
        
        # Generate summary
        summary = self.generate_summary()
        
        logger.info("\n" + "=" * 70)
        logger.info("✅ 90-DAY SIMULATION COMPLETE")
        logger.info("=" * 70)
        
        return summary
    
    def generate_summary(self) -> Dict:
        """Generate comprehensive simulation summary"""
        total_profit = sum(m.total_profit_usd for m in self.daily_metrics)
        total_gas = sum(m.total_gas_cost_usd for m in self.daily_metrics)
        total_opportunities = sum(m.opportunities_found for m in self.daily_metrics)
        total_executed = sum(m.opportunities_executed for m in self.daily_metrics)
        total_successful = sum(m.successful_trades for m in self.daily_metrics)
        total_failed = sum(m.failed_trades for m in self.daily_metrics)
        
        overall_success_rate = (
            total_successful / total_executed if total_executed > 0 else 0
        )
        
        summary = {
            'simulation_period': '90 days',
            'total_opportunities_found': total_opportunities,
            'total_opportunities_executed': total_executed,
            'total_successful_trades': total_successful,
            'total_failed_trades': total_failed,
            'overall_success_rate': overall_success_rate,
            'total_profit_usd': total_profit,
            'total_gas_cost_usd': total_gas,
            'net_profit_usd': total_profit - total_gas,
            'average_daily_profit': total_profit / 90,
            'average_profit_per_trade': total_profit / total_successful if total_successful > 0 else 0,
            'features_enabled': self.features,
            'config': self.config
        }
        
        logger.info(f"\n📊 SIMULATION SUMMARY:")
        logger.info(f"   Total Opportunities Found: {total_opportunities:,}")
        logger.info(f"   Total Executed: {total_executed:,}")
        logger.info(f"   Successful Trades: {total_successful:,}")
        logger.info(f"   Overall Success Rate: {overall_success_rate*100:.1f}%")
        logger.info(f"   Total Profit: ${total_profit:,.2f}")
        logger.info(f"   Total Gas Cost: ${total_gas:,.2f}")
        logger.info(f"   Net Profit: ${total_profit - total_gas:,.2f}")
        logger.info(f"   Average Daily Profit: ${total_profit/90:,.2f}")
        
        return summary
    
    def export_results(self, output_dir: str = "data/simulation_results"):
        """Export simulation results to files"""
        os.makedirs(output_dir, exist_ok=True)
        
        # Export daily metrics
        metrics_df = pd.DataFrame([asdict(m) for m in self.daily_metrics])
        metrics_file = f"{output_dir}/daily_metrics.csv"
        metrics_df.to_csv(metrics_file, index=False)
        logger.info(f"✅ Exported daily metrics to {metrics_file}")
        
        # Export individual opportunities
        if self.results:
            results_df = pd.DataFrame([asdict(r) for r in self.results])
            results_file = f"{output_dir}/opportunities.csv"
            results_df.to_csv(results_file, index=False)
            logger.info(f"✅ Exported {len(self.results)} opportunities to {results_file}")
        
        # Export summary
        summary = self.generate_summary()
        summary_file = f"{output_dir}/summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)
        logger.info(f"✅ Exported summary to {summary_file}")


if __name__ == "__main__":
    # Example usage
    logger.info("Simulation Engine module loaded")
