#!/usr/bin/env python3
"""
APEX-OMEGA TITAN: MAINNET HEALTH MONITOR
========================================

Real-time health monitoring and diagnostics for mainnet operations.
Monitors:
1. System component status (Brain, Bot, ML)
2. RPC connectivity and latency
3. Signal processing throughput
4. Gas price conditions
5. Wallet balances (live mode)
6. Error rates and circuit breakers
"""

import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("HealthMonitor")

class MainnetHealthMonitor:
    """Comprehensive health monitoring for Titan mainnet system"""
    
    def __init__(self):
        self.mode = os.getenv('EXECUTION_MODE', 'PAPER').upper()
        self.signals_dir = Path('signals/outgoing')
        self.processed_dir = Path('signals/processed')
        self.start_time = datetime.now()
        
        # RPC endpoints to check
        self.rpc_endpoints = {
            'Ethereum': os.getenv('RPC_ETHEREUM'),
            'Polygon': os.getenv('RPC_POLYGON'),
            'Arbitrum': os.getenv('RPC_ARBITRUM'),
            'Optimism': os.getenv('RPC_OPTIMISM'),
            'Base': os.getenv('RPC_BASE'),
        }
        
        # Metrics storage
        self.metrics = {
            'last_signal_time': None,
            'total_signals': 0,
            'signals_last_hour': 0,
            'rpc_status': {},
            'gas_prices': {},
            'wallet_balances': {},
            'errors': []
        }
    
    def check_rpc_connectivity(self):
        """Check RPC endpoints connectivity and response time"""
        logger.info("🔍 Checking RPC connectivity...")
        
        for chain_name, rpc_url in self.rpc_endpoints.items():
            if not rpc_url or 'YOUR_' in rpc_url:
                self.metrics['rpc_status'][chain_name] = {
                    'status': 'NOT_CONFIGURED',
                    'latency_ms': None
                }
                continue
            
            try:
                start = time.time()
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                block = w3.eth.block_number
                latency = (time.time() - start) * 1000
                
                self.metrics['rpc_status'][chain_name] = {
                    'status': 'HEALTHY',
                    'latency_ms': round(latency, 2),
                    'block_number': block
                }
                logger.info(f"   ✅ {chain_name}: {latency:.2f}ms (block {block})")
                
                # Check gas price for major chains
                if chain_name in ['Ethereum', 'Polygon', 'Arbitrum']:
                    gas_price_wei = w3.eth.gas_price
                    gas_price_gwei = gas_price_wei / 1e9
                    self.metrics['gas_prices'][chain_name] = round(gas_price_gwei, 2)
                    
            except Exception as e:
                self.metrics['rpc_status'][chain_name] = {
                    'status': 'ERROR',
                    'latency_ms': None,
                    'error': str(e)
                }
                logger.error(f"   ❌ {chain_name}: {str(e)[:50]}")
    
    def check_signal_processing(self):
        """Check signal file processing metrics"""
        logger.info("📊 Checking signal processing...")
        
        # Count signals in outgoing directory
        if self.signals_dir.exists():
            signal_files = list(self.signals_dir.glob('*.json'))
            self.metrics['total_signals'] = len(signal_files)
            
            # Check last signal time
            if signal_files:
                latest_signal = max(signal_files, key=lambda p: p.stat().st_mtime)
                last_mod = datetime.fromtimestamp(latest_signal.stat().st_mtime)
                self.metrics['last_signal_time'] = last_mod
                
                time_since = datetime.now() - last_mod
                if time_since.total_seconds() < 300:  # Less than 5 minutes
                    logger.info(f"   ✅ Latest signal: {time_since.seconds}s ago")
                else:
                    logger.warning(f"   ⚠️  Latest signal: {time_since.seconds}s ago (system may be idle)")
            else:
                logger.info("   ℹ️  No signals in queue (normal if just started)")
        
        # Count processed signals
        if self.processed_dir.exists():
            processed_count = len(list(self.processed_dir.glob('*.json')))
            logger.info(f"   📝 Processed signals: {processed_count}")
    
    def check_gas_conditions(self):
        """Check if gas conditions are favorable"""
        logger.info("⛽ Checking gas conditions...")
        
        max_gas_limit = float(os.getenv('MAX_BASE_FEE_GWEI', '500'))
        
        for chain_name, gas_gwei in self.metrics['gas_prices'].items():
            if gas_gwei:
                status = "✅ GOOD" if gas_gwei < max_gas_limit else "❌ HIGH"
                logger.info(f"   {status}: {chain_name} = {gas_gwei} gwei")
    
    def check_wallet_status(self):
        """Check wallet configuration and balance (live mode only)"""
        if self.mode == 'PAPER':
            logger.info("💳 Wallet: PAPER mode (wallet checks skipped)")
            return
        
        logger.info("💳 Checking wallet status...")
        
        executor_addr = os.getenv('EXECUTOR_ADDRESS')
        private_key = os.getenv('PRIVATE_KEY')
        
        # Validate configuration
        if not executor_addr or 'YOUR_' in executor_addr:
            logger.error("   ❌ EXECUTOR_ADDRESS not configured!")
            return
        
        if not private_key or 'YOUR_' in private_key:
            logger.error("   ❌ PRIVATE_KEY not configured!")
            return
        
        logger.info(f"   📍 Address: {executor_addr}")
        
        # Check balances on major chains
        for chain_name, rpc_url in self.rpc_endpoints.items():
            if not rpc_url or 'YOUR_' in rpc_url:
                continue
            
            try:
                w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={'timeout': 10}))
                balance_wei = w3.eth.get_balance(executor_addr)
                balance_eth = balance_wei / 1e18
                
                self.metrics['wallet_balances'][chain_name] = round(balance_eth, 6)
                
                if balance_eth > 0.001:
                    logger.info(f"   ✅ {chain_name}: {balance_eth:.6f} (sufficient)")
                else:
                    logger.warning(f"   ⚠️  {chain_name}: {balance_eth:.6f} (low balance!)")
                    
            except Exception as e:
                logger.error(f"   ❌ {chain_name} balance check failed: {str(e)[:50]}")
    
    def check_system_components(self):
        """Check if system components are running"""
        logger.info("🔧 Checking system components...")
        
        # Check if brain module can be imported
        try:
            from ml.brain import OmniBrain
            logger.info("   ✅ Brain module: OK")
        except ImportError as e:
            logger.error(f"   ❌ Brain module: {e}")
        
        # Check if bot execution module exists
        bot_path = Path('execution/bot.js')
        if bot_path.exists():
            logger.info("   ✅ Bot module: OK")
        else:
            logger.error("   ❌ Bot module: NOT FOUND")
        
        # Check signal directories
        if self.signals_dir.exists():
            logger.info("   ✅ Signal directories: OK")
        else:
            logger.warning("   ⚠️  Signal directories: Creating...")
            self.signals_dir.mkdir(parents=True, exist_ok=True)
            self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def print_summary(self):
        """Print comprehensive health summary"""
        runtime = datetime.now() - self.start_time
        
        print("\n" + "="*70)
        print("  📊 TITAN MAINNET HEALTH REPORT")
        print("="*70)
        print(f"  Execution Mode: {self.mode}")
        print(f"  Monitor Runtime: {runtime.seconds}s")
        print("")
        
        # RPC Status Summary
        print("  🌐 RPC CONNECTIVITY")
        print("  " + "-"*66)
        healthy = sum(1 for s in self.metrics['rpc_status'].values() if s['status'] == 'HEALTHY')
        total = len(self.metrics['rpc_status'])
        print(f"  Status: {healthy}/{total} endpoints healthy")
        print("")
        
        # Gas Prices Summary
        if self.metrics['gas_prices']:
            print("  ⛽ GAS PRICES")
            print("  " + "-"*66)
            for chain, price in self.metrics['gas_prices'].items():
                print(f"  {chain}: {price} gwei")
            print("")
        
        # Signal Processing Summary
        print("  📡 SIGNAL PROCESSING")
        print("  " + "-"*66)
        print(f"  Pending Signals: {self.metrics['total_signals']}")
        if self.metrics['last_signal_time']:
            time_ago = datetime.now() - self.metrics['last_signal_time']
            print(f"  Last Signal: {time_ago.seconds}s ago")
        print("")
        
        # Wallet Status (live mode only)
        if self.mode == 'LIVE' and self.metrics['wallet_balances']:
            print("  💳 WALLET BALANCES")
            print("  " + "-"*66)
            for chain, balance in self.metrics['wallet_balances'].items():
                print(f"  {chain}: {balance} (native token)")
            print("")
        
        print("="*70)
        print("")
    
    def run_continuous_monitoring(self, interval_seconds=60):
        """Run continuous health monitoring"""
        logger.info(f"🔄 Starting continuous monitoring (interval: {interval_seconds}s)")
        logger.info("Press Ctrl+C to stop\n")
        
        try:
            while True:
                self.check_system_components()
                self.check_rpc_connectivity()
                self.check_signal_processing()
                self.check_gas_conditions()
                self.check_wallet_status()
                self.print_summary()
                
                time.sleep(interval_seconds)
                
        except KeyboardInterrupt:
            logger.info("\n🛑 Monitoring stopped by user")
    
    def run_single_check(self):
        """Run a single health check"""
        self.check_system_components()
        self.check_rpc_connectivity()
        self.check_signal_processing()
        self.check_gas_conditions()
        self.check_wallet_status()
        self.print_summary()

def main():
    """Main entry point"""
    monitor = MainnetHealthMonitor()
    
    # Check if continuous monitoring requested
    if len(sys.argv) > 1 and sys.argv[1] == '--continuous':
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 60
        monitor.run_continuous_monitoring(interval)
    else:
        monitor.run_single_check()

if __name__ == "__main__":
    main()
