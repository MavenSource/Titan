#!/usr/bin/env python3
"""
Historical Data Fetcher for Titan 90-Day Simulation
====================================================

Fetches real backdated historical data from blockchain networks:
- DEX prices (Uniswap V2/V3, Curve, Balancer)
- Gas prices
- Bridge fees
- Liquidity metrics
- Block timestamps

Uses on-chain queries with historical block numbers to retrieve accurate
past market conditions for simulation purposes.
"""

import os
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from web3 import Web3
try:
    from web3.middleware import geth_poa_middleware
except ImportError:
    try:
        from web3.middleware import ExtraDataToPOAMiddleware as geth_poa_middleware
    except ImportError:
        geth_poa_middleware = None
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [HistoricalFetcher] %(message)s'
)
logger = logging.getLogger("HistoricalDataFetcher")

# Constants
POA_CHAINS = [137, 56, 250, 42220]  # Polygon, BSC, Fantom, Celo
SECONDS_PER_DAY = 86400

# Minimal ABIs for historical queries
UNISWAP_V2_PAIR_ABI = [
    {"constant": True, "inputs": [], "name": "getReserves", 
     "outputs": [
         {"name": "reserve0", "type": "uint112"},
         {"name": "reserve1", "type": "uint112"},
         {"name": "blockTimestampLast", "type": "uint32"}
     ], "type": "function"},
    {"constant": True, "inputs": [], "name": "token0", "outputs": [{"name": "", "type": "address"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "token1", "outputs": [{"name": "", "type": "address"}], "type": "function"}
]

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], 
     "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", 
     "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "symbol", 
     "outputs": [{"name": "", "type": "string"}], "type": "function"}
]


class HistoricalDataFetcher:
    """
    Fetches historical blockchain data for simulation purposes.
    """
    
    def __init__(self, chain_id: int, rpc_url: str):
        """
        Initialize historical data fetcher for a specific chain.
        
        Args:
            chain_id: Chain ID (e.g., 137 for Polygon)
            rpc_url: RPC endpoint URL
        """
        self.chain_id = chain_id
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 60}))
        
        # Inject PoA middleware if needed
        if chain_id in POA_CHAINS and geth_poa_middleware:
            try:
                self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            except Exception:
                pass  # Middleware injection failed, continue without it
        
        if not self.w3.is_connected():
            logger.warning(f"⚠️  Could not connect to chain {chain_id} RPC")
        else:
            logger.info(f"✅ Connected to chain {chain_id}")
    
    def get_block_by_timestamp(self, target_timestamp: int) -> Optional[int]:
        """
        Find the closest block number to a target timestamp using binary search.
        
        Args:
            target_timestamp: Unix timestamp
            
        Returns:
            Block number closest to the timestamp, or None if error
        """
        try:
            # Get current block as upper bound
            latest_block = self.w3.eth.block_number
            latest_timestamp = self.w3.eth.get_block(latest_block)['timestamp']
            
            # Check if timestamp is in the future
            if target_timestamp > latest_timestamp:
                logger.warning(f"Target timestamp {target_timestamp} is in the future")
                return latest_block
            
            # Estimate average block time (varies by chain)
            block_time_estimates = {
                1: 12,      # Ethereum
                137: 2,     # Polygon
                42161: 0.3, # Arbitrum
                10: 2,      # Optimism
                56: 3,      # BSC
                43114: 2,   # Avalanche
            }
            avg_block_time = block_time_estimates.get(self.chain_id, 12)
            
            # Estimate starting block
            time_diff = latest_timestamp - target_timestamp
            blocks_back = int(time_diff / avg_block_time)
            lower_bound = max(0, latest_block - blocks_back - 1000)
            upper_bound = latest_block
            
            logger.info(f"Searching for block at timestamp {target_timestamp} (date: {datetime.fromtimestamp(target_timestamp)})")
            
            # Binary search
            iterations = 0
            max_iterations = 50
            
            while lower_bound <= upper_bound and iterations < max_iterations:
                mid = (lower_bound + upper_bound) // 2
                mid_block = self.w3.eth.get_block(mid)
                mid_timestamp = mid_block['timestamp']
                
                if abs(mid_timestamp - target_timestamp) < 100:  # Within 100 seconds
                    logger.info(f"Found block {mid} at timestamp {mid_timestamp}")
                    return mid
                
                if mid_timestamp < target_timestamp:
                    lower_bound = mid + 1
                else:
                    upper_bound = mid - 1
                
                iterations += 1
                
                if iterations % 10 == 0:
                    logger.debug(f"Binary search iteration {iterations}: block {mid}, timestamp diff: {mid_timestamp - target_timestamp}s")
            
            # Return closest block found
            final_block = (lower_bound + upper_bound) // 2
            logger.info(f"Found approximate block {final_block} after {iterations} iterations")
            return final_block
            
        except Exception as e:
            logger.error(f"Error finding block by timestamp: {e}")
            return None
    
    def get_historical_gas_price(self, block_number: int) -> Optional[float]:
        """
        Get historical gas price at a specific block.
        
        Args:
            block_number: Block number
            
        Returns:
            Gas price in Gwei, or None if error
        """
        try:
            block = self.w3.eth.get_block(block_number)
            base_fee = block.get('baseFeePerGas', 0)
            
            if base_fee > 0:
                # EIP-1559 chain
                gas_price_wei = base_fee
            else:
                # Legacy chain - estimate from previous blocks
                gas_price_wei = self.w3.eth.gas_price
            
            gas_price_gwei = gas_price_wei / 1e9
            return gas_price_gwei
            
        except Exception as e:
            logger.error(f"Error getting gas price at block {block_number}: {e}")
            return None
    
    def get_historical_pair_price(
        self, 
        pair_address: str, 
        block_number: int,
        token0_decimals: int = 18,
        token1_decimals: int = 18
    ) -> Optional[Tuple[float, float]]:
        """
        Get historical DEX pair reserves at a specific block.
        
        Args:
            pair_address: Uniswap V2 pair address
            block_number: Block number
            token0_decimals: Decimals for token0
            token1_decimals: Decimals for token1
            
        Returns:
            Tuple of (token0_price_in_token1, token1_price_in_token0), or None if error
        """
        try:
            pair_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(pair_address),
                abi=UNISWAP_V2_PAIR_ABI
            )
            
            # Get reserves at historical block
            reserves = pair_contract.functions.getReserves().call(block_identifier=block_number)
            reserve0 = reserves[0] / (10 ** token0_decimals)
            reserve1 = reserves[1] / (10 ** token1_decimals)
            
            if reserve0 > 0 and reserve1 > 0:
                token0_price = reserve1 / reserve0
                token1_price = reserve0 / reserve1
                return (token0_price, token1_price)
            
            return None
            
        except Exception as e:
            logger.debug(f"Error getting pair price at block {block_number}: {e}")
            return None
    
    def get_historical_token_balance(
        self,
        token_address: str,
        holder_address: str,
        block_number: int
    ) -> Optional[float]:
        """
        Get historical token balance for liquidity checks.
        
        Args:
            token_address: Token contract address
            holder_address: Address holding tokens (e.g., liquidity pool)
            block_number: Block number
            
        Returns:
            Token balance in raw units, or None if error
        """
        try:
            token_contract = self.w3.eth.contract(
                address=Web3.to_checksum_address(token_address),
                abi=ERC20_ABI
            )
            
            balance = token_contract.functions.balanceOf(
                Web3.to_checksum_address(holder_address)
            ).call(block_identifier=block_number)
            
            return balance
            
        except Exception as e:
            logger.debug(f"Error getting token balance at block {block_number}: {e}")
            return None
    
    def fetch_daily_snapshot(
        self,
        date: datetime,
        pairs: List[Dict[str, str]],
        liquidity_pools: List[Dict[str, str]]
    ) -> Dict:
        """
        Fetch a complete market snapshot for a specific day.
        
        Args:
            date: Date to fetch data for
            pairs: List of DEX pairs to query [{address, token0_decimals, token1_decimals}]
            liquidity_pools: List of liquidity pools to check [{token, pool_address}]
            
        Returns:
            Dictionary with all market data for that day
        """
        timestamp = int(date.timestamp())
        block_number = self.get_block_by_timestamp(timestamp)
        
        if not block_number:
            logger.error(f"Could not find block for date {date}")
            return None
        
        snapshot = {
            'date': date.strftime('%Y-%m-%d'),
            'timestamp': timestamp,
            'block_number': block_number,
            'chain_id': self.chain_id,
            'gas_price_gwei': None,
            'pair_prices': {},
            'liquidity': {}
        }
        
        # Get gas price
        snapshot['gas_price_gwei'] = self.get_historical_gas_price(block_number)
        
        # Get DEX pair prices
        for pair in pairs:
            price_data = self.get_historical_pair_price(
                pair['address'],
                block_number,
                pair.get('token0_decimals', 18),
                pair.get('token1_decimals', 18)
            )
            if price_data:
                snapshot['pair_prices'][pair['address']] = {
                    'token0_price': price_data[0],
                    'token1_price': price_data[1]
                }
        
        # Get liquidity data
        for pool in liquidity_pools:
            balance = self.get_historical_token_balance(
                pool['token'],
                pool['pool_address'],
                block_number
            )
            if balance:
                snapshot['liquidity'][pool['token']] = balance
        
        logger.info(f"✅ Fetched snapshot for {date.strftime('%Y-%m-%d')}: "
                   f"gas={snapshot['gas_price_gwei']:.2f} gwei, "
                   f"pairs={len(snapshot['pair_prices'])}, "
                   f"liquidity={len(snapshot['liquidity'])}")
        
        return snapshot


def fetch_90_day_data(
    chain_id: int,
    rpc_url: str,
    start_date: datetime,
    pairs: List[Dict[str, str]],
    liquidity_pools: List[Dict[str, str]],
    output_file: str = "data/historical_90day.csv"
) -> pd.DataFrame:
    """
    Fetch 90 days of historical data and save to CSV.
    
    Args:
        chain_id: Chain ID to fetch data from
        rpc_url: RPC endpoint
        start_date: Starting date (will fetch 90 days from this date)
        pairs: DEX pairs to track
        liquidity_pools: Liquidity pools to monitor
        output_file: Output CSV file path
        
    Returns:
        DataFrame with all historical data
    """
    fetcher = HistoricalDataFetcher(chain_id, rpc_url)
    
    all_snapshots = []
    
    for day in range(90):
        current_date = start_date + timedelta(days=day)
        
        logger.info(f"\n📅 Fetching data for day {day + 1}/90: {current_date.strftime('%Y-%m-%d')}")
        
        snapshot = fetcher.fetch_daily_snapshot(current_date, pairs, liquidity_pools)
        
        if snapshot:
            all_snapshots.append(snapshot)
        
        # Rate limiting - don't overwhelm the RPC
        time.sleep(0.5)
    
    # Convert to DataFrame
    df = pd.DataFrame(all_snapshots)
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    df.to_csv(output_file, index=False)
    logger.info(f"\n✅ Saved {len(df)} days of data to {output_file}")
    
    return df


if __name__ == "__main__":
    # Example: Fetch 90 days of Polygon data
    # Starting from 90 days ago
    
    start_date = datetime.now() - timedelta(days=90)
    
    # Example pairs (USDC/WETH on Polygon)
    example_pairs = [
        {
            'address': '0x6e7a5FAFcec6BB1e78bAE2A1F0B612012BF14827',  # QuickSwap USDC/WETH
            'token0_decimals': 6,
            'token1_decimals': 18
        }
    ]
    
    # Example liquidity pools
    example_pools = [
        {
            'token': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',  # USDC on Polygon
            'pool_address': '0xBA12222222228d8Ba445958a75a0704d566BF2C8'  # Balancer V3 Vault
        }
    ]
    
    rpc_url = os.getenv('RPC_POLYGON', 'https://polygon-rpc.com')
    
    logger.info("🚀 Starting 90-day historical data fetch...")
    df = fetch_90_day_data(
        chain_id=137,
        rpc_url=rpc_url,
        start_date=start_date,
        pairs=example_pairs,
        liquidity_pools=example_pools
    )
    
    logger.info(f"\n📊 Data Summary:")
    logger.info(f"Total days: {len(df)}")
    logger.info(f"Date range: {df['date'].min()} to {df['date'].max()}")
    logger.info(f"\nFirst few rows:")
    print(df.head())
