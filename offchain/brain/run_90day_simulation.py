#!/usr/bin/env python3
"""
Titan 90-Day Historical Simulation Runner
==========================================

Complete simulation runner that:
1. Fetches historical blockchain data (or loads from cache)
2. Runs 90-day simulation with Titan system logic
3. Compares full system wiring and features
4. Generates comprehensive reports

Usage:
    python run_90day_simulation.py [--fetch-data] [--chain-id CHAIN_ID]
    
Examples:
    # Run simulation with cached data
    python run_90day_simulation.py
    
    # Fetch fresh historical data and run simulation
    python run_90day_simulation.py --fetch-data --chain-id 137
    
    # Quick test (7 days instead of 90)
    python run_90day_simulation.py --quick-test
"""

import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from simulation.historical_data_fetcher import fetch_90_day_data, HistoricalDataFetcher
from simulation.simulation_engine import TitanSimulationEngine
from simulation.system_comparison import TitanSystemAnalyzer

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [Main] %(message)s'
)
logger = logging.getLogger("Main")


def setup_example_data(days: int = 90) -> pd.DataFrame:
    """
    Create example historical data for quick testing when RPC is unavailable.
    
    Args:
        days: Number of days to generate
        
    Returns:
        DataFrame with synthetic historical data
    """
    logger.info("📊 Generating example historical data for testing...")
    
    data = []
    start_date = datetime.now() - timedelta(days=days)
    
    for day in range(days):
        current_date = start_date + timedelta(days=day)
        
        # Generate realistic-looking data
        base_gas = 30 + (day % 20)  # Varies between 30-50 gwei
        
        data.append({
            'date': current_date.strftime('%Y-%m-%d'),
            'timestamp': int(current_date.timestamp()),
            'block_number': 50000000 + (day * 43200),  # ~43200 blocks per day on Polygon
            'chain_id': 137,
            'gas_price_gwei': base_gas,
            'pair_prices': {
                '0x6e7a5FAFcec6BB1e78bAE2A1F0B612012BF14827': {
                    'token0_price': 0.0003 + (day * 0.000001),
                    'token1_price': 3333.33
                }
            },
            'liquidity': {
                '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174': 50000000000000  # 50M USDC
            }
        })
    
    df = pd.DataFrame(data)
    
    # Save to data directory
    os.makedirs('data', exist_ok=True)
    output_file = 'data/example_historical_data.csv'
    df.to_csv(output_file, index=False)
    
    logger.info(f"✅ Generated {len(df)} days of example data")
    logger.info(f"   Saved to: {output_file}")
    
    return df


def fetch_historical_data(
    chain_id: int,
    days: int = 90,
    use_example: bool = False
) -> pd.DataFrame:
    """
    Fetch or load historical blockchain data.
    
    Args:
        chain_id: Chain ID to fetch data from
        days: Number of days to fetch
        use_example: Use example data instead of real blockchain data
        
    Returns:
        DataFrame with historical data
    """
    cache_file = f'data/historical_{chain_id}_{days}day.csv'
    
    # Check if cached data exists
    if os.path.exists(cache_file):
        logger.info(f"📂 Loading cached data from {cache_file}")
        df = pd.read_csv(cache_file)
        logger.info(f"✅ Loaded {len(df)} days of cached data")
        return df
    
    if use_example:
        return setup_example_data(days)
    
    # Fetch fresh data
    logger.info(f"🌐 Fetching {days} days of historical data from chain {chain_id}...")
    
    # Get RPC URL
    rpc_env_map = {
        1: 'RPC_ETHEREUM',
        137: 'RPC_POLYGON',
        42161: 'RPC_ARBITRUM',
        10: 'RPC_OPTIMISM',
        56: 'RPC_BSC',
        43114: 'RPC_AVALANCHE'
    }
    
    rpc_env = rpc_env_map.get(chain_id, 'RPC_POLYGON')
    rpc_url = os.getenv(rpc_env)
    
    if not rpc_url:
        logger.warning(f"⚠️  No RPC URL found for chain {chain_id}")
        logger.info("Using example data instead")
        return setup_example_data(days)
    
    # Define pairs and pools to track
    # These are examples - real implementation would track many more
    pairs = [
        {
            'address': '0x6e7a5FAFcec6BB1e78bAE2A1F0B612012BF14827',
            'token0_decimals': 6,
            'token1_decimals': 18
        }
    ]
    
    liquidity_pools = [
        {
            'token': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # USDC
            'pool_address': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'  # Balancer Vault
        }
    ]
    
    start_date = datetime.now() - timedelta(days=days)
    
    try:
        df = fetch_90_day_data(
            chain_id=chain_id,
            rpc_url=rpc_url,
            start_date=start_date,
            pairs=pairs,
            liquidity_pools=liquidity_pools,
            output_file=cache_file
        )
        return df
    except (ConnectionError, TimeoutError, ValueError) as e:
        logger.error(f"❌ Error fetching data: {e}")
        logger.info("Falling back to example data")
        return setup_example_data(days)
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")
        raise


def run_simulation(
    historical_data: pd.DataFrame,
    config: dict = None
) -> dict:
    """
    Run 90-day simulation with historical data.
    
    Args:
        historical_data: DataFrame with historical market data
        config: Optional simulation configuration
        
    Returns:
        Simulation results dictionary
    """
    logger.info("\n" + "=" * 70)
    logger.info("🚀 STARTING TITAN 90-DAY SIMULATION")
    logger.info("=" * 70)
    
    # Initialize simulation engine
    engine = TitanSimulationEngine(config)
    
    # Determine start date from data
    first_date_str = historical_data.iloc[0]['date']
    start_date = datetime.strptime(first_date_str, '%Y-%m-%d')
    
    # Run simulation
    results = engine.run_90_day_simulation(start_date, historical_data)
    
    # Export results
    engine.export_results()
    
    return results


def generate_comparison_report(simulation_results: dict):
    """
    Generate system comparison report.
    
    Args:
        simulation_results: Results from simulation
    """
    logger.info("\n" + "=" * 70)
    logger.info("📊 GENERATING COMPARISON REPORT")
    logger.info("=" * 70)
    
    analyzer = TitanSystemAnalyzer()
    analyzer.generate_comparison_report(simulation_results)


def main():
    """Main execution function"""
    parser = argparse.ArgumentParser(
        description='Run Titan 90-day historical simulation',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Quick test with example data
  %(prog)s --fetch-data --chain-id 137       # Fetch Polygon data and simulate
  %(prog)s --quick-test                       # 7-day test simulation
  %(prog)s --use-cache                        # Use cached historical data
        """
    )
    
    parser.add_argument(
        '--fetch-data',
        action='store_true',
        help='Fetch fresh historical data from blockchain'
    )
    
    parser.add_argument(
        '--chain-id',
        type=int,
        default=137,
        help='Chain ID to fetch data from (default: 137 for Polygon)'
    )
    
    parser.add_argument(
        '--quick-test',
        action='store_true',
        help='Run quick 7-day test instead of full 90 days'
    )
    
    parser.add_argument(
        '--use-cache',
        action='store_true',
        help='Use cached data if available'
    )
    
    parser.add_argument(
        '--example-data',
        action='store_true',
        help='Use generated example data instead of real blockchain data'
    )
    
    args = parser.parse_args()
    
    # Determine number of days
    days = 7 if args.quick_test else 90
    
    logger.info("=" * 70)
    logger.info("🎯 TITAN 90-DAY HISTORICAL SIMULATION")
    logger.info("=" * 70)
    logger.info(f"Mode: {'Quick Test' if args.quick_test else 'Full Simulation'}")
    logger.info(f"Days: {days}")
    logger.info(f"Chain ID: {args.chain_id}")
    logger.info(f"Fetch Fresh Data: {args.fetch_data}")
    logger.info("=" * 70)
    
    try:
        # Step 1: Get historical data
        if args.example_data or (not args.fetch_data and not args.use_cache):
            logger.info("\n📊 Using example historical data...")
            historical_data = setup_example_data(days)
        else:
            logger.info(f"\n📡 Fetching historical data for chain {args.chain_id}...")
            historical_data = fetch_historical_data(
                chain_id=args.chain_id,
                days=days,
                use_example=args.example_data
            )
        
        if historical_data is None or len(historical_data) == 0:
            logger.error("❌ No historical data available")
            return 1
        
        logger.info(f"✅ Historical data ready: {len(historical_data)} days")
        
        # Step 2: Run simulation
        simulation_config = {
            'min_profit_threshold_usd': 5.0,
            'max_gas_price_gwei': 500,
            'flash_loan_fee_rate': 0.0,
            'min_success_probability': 0.7,
            'slippage_tolerance': 0.01,
            'gas_buffer_multiplier': 1.2,
            'base_gas_units': 390000,
            'bridge_fee_avg_usd': 2.5,
            'execution_mode': 'PAPER'
        }
        
        results = run_simulation(historical_data, simulation_config)
        
        # Step 3: Generate comparison report
        generate_comparison_report(results)
        
        # Print final summary
        logger.info("\n" + "=" * 70)
        logger.info("✅ SIMULATION COMPLETE")
        logger.info("=" * 70)
        logger.info("\n📁 Output files generated:")
        logger.info("   data/simulation_results/daily_metrics.csv")
        logger.info("   data/simulation_results/opportunities.csv")
        logger.info("   data/simulation_results/summary.json")
        logger.info("   data/simulation_results/feature_matrix.csv")
        logger.info("   data/simulation_results/components.csv")
        logger.info("   data/simulation_results/system_wiring.json")
        logger.info("   data/simulation_results/system_comparison.json")
        logger.info("   data/simulation_results/COMPARISON_SUMMARY.md")
        logger.info("\n" + "=" * 70)
        logger.info("📊 View COMPARISON_SUMMARY.md for complete analysis")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"\n❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
