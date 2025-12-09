"""
TITAN METRICS PUBLISHER

Provides comprehensive system monitoring and metrics publishing
to the real-time monitoring dashboard via Redis.

Tracks:
- Chain connection status and block numbers
- Opportunity detection and execution metrics
- Performance timing (scan, simulation, execution)
- Profit tracking by chain and total
- Error logging and system health
"""

import redis
import json
import time
import os
from typing import Dict, Any, Optional
from datetime import datetime


class MetricsPublisher:
    """
    Publishes system metrics to Redis for real-time monitoring.
    All Titan components should instantiate this class to report metrics.
    """
    
    def __init__(self, component_name: str):
        """
        Initialize metrics publisher.
        
        Args:
            component_name: Name of the component (e.g., "brain", "executor", "pricer")
        """
        self.component = component_name
        self.redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        self.redis_client = None
        self._connect_redis()
        
        # Performance tracking
        self.scan_times = []
        self.simulation_times = []
        self.execution_times = []
        
        print(f"📊 [{self.component}] Metrics publisher initialized")
    
    def _connect_redis(self):
        """Connect to Redis server."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            self.redis_client.ping()
            print(f"✅ [{self.component}] Connected to Redis for metrics")
        except Exception as e:
            print(f"⚠️  [{self.component}] Redis connection failed: {e}")
            print(f"⚠️  [{self.component}] Metrics will be logged locally only")
            self.redis_client = None
    
    def _publish(self, channel: str, data: Dict[str, Any]):
        """
        Publish data to Redis channel.
        
        Args:
            channel: Redis channel name
            data: Data to publish
        """
        if not self.redis_client:
            return
        
        try:
            payload = json.dumps(data)
            self.redis_client.publish(channel, payload)
        except Exception as e:
            print(f"❌ [{self.component}] Failed to publish to {channel}: {e}")
    
    # ==================== CHAIN METRICS ====================
    
    def report_chain_connected(self, chain_id: int, block_number: int, gas_price: int, tokens_tracked: int = 0):
        """
        Report successful chain connection.
        
        Args:
            chain_id: Blockchain network ID
            block_number: Current block number
            gas_price: Current gas price in wei
            tokens_tracked: Number of tokens being tracked
        """
        data = {
            'chainId': chain_id,
            'connected': True,
            'blockNumber': block_number,
            'gasPrice': gas_price,
            'tokensTracked': tokens_tracked,
            'timestamp': int(time.time() * 1000)
        }
        
        self._publish('system_metrics', data)
        print(f"📡 [{self.component}] Chain {chain_id} connected | Block: {block_number}")
    
    def report_chain_disconnected(self, chain_id: int, reason: str = ""):
        """
        Report chain disconnection.
        
        Args:
            chain_id: Blockchain network ID
            reason: Reason for disconnection
        """
        data = {
            'chainId': chain_id,
            'connected': False,
            'reason': reason,
            'timestamp': int(time.time() * 1000)
        }
        
        self._publish('system_metrics', data)
        self.report_error('warning', f"Chain {chain_id} disconnected: {reason}", chain_id=chain_id)
    
    def report_chain_update(self, chain_id: int, block_number: int = None, gas_price: int = None):
        """
        Report chain status update.
        
        Args:
            chain_id: Blockchain network ID
            block_number: Updated block number
            gas_price: Updated gas price in wei
        """
        data = {
            'chainId': chain_id,
            'timestamp': int(time.time() * 1000)
        }
        
        if block_number is not None:
            data['blockNumber'] = block_number
        
        if gas_price is not None:
            data['gasPrice'] = gas_price
        
        self._publish('system_metrics', data)
    
    # ==================== OPPORTUNITY METRICS ====================
    
    def report_opportunity_detected(
        self,
        chain_id: int,
        token: str,
        expected_profit: float,
        loan_amount: float,
        route: str = "",
        details: Dict[str, Any] = None
    ):
        """
        Report arbitrage opportunity detection.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
            expected_profit: Expected profit in USD
            loan_amount: Flash loan amount
            route: Execution route description
            details: Additional opportunity details
        """
        data = {
            'chainId': chain_id,
            'token': token,
            'profit': expected_profit,
            'loanAmount': loan_amount,
            'route': route,
            'timestamp': int(time.time() * 1000)
        }
        
        if details:
            data.update(details)
        
        self._publish('trade_signals', data)
        print(f"💰 [{self.component}] Opportunity detected | Chain: {chain_id} | Profit: ${expected_profit:.2f}")
    
    # ==================== EXECUTION METRICS ====================
    
    def report_simulation_start(self, chain_id: int, token: str):
        """
        Report simulation start.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
        """
        self._sim_start_time = time.time()
        print(f"🧪 [{self.component}] Simulating trade | Chain: {chain_id}")
    
    def report_simulation_success(
        self,
        chain_id: int,
        token: str,
        estimated_gas: int,
        estimated_profit: float
    ):
        """
        Report successful simulation.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
            estimated_gas: Estimated gas units
            estimated_profit: Estimated profit in USD
        """
        sim_time = int((time.time() - getattr(self, '_sim_start_time', time.time())) * 1000)
        self.simulation_times.append(sim_time)
        
        data = {
            'status': 'simulated',
            'chainId': chain_id,
            'token': token,
            'estimatedGas': estimated_gas,
            'profit': estimated_profit,
            'simulationTime': sim_time,
            'timestamp': int(time.time() * 1000)
        }
        
        self._publish('execution_updates', data)
        self._publish('system_metrics', {
            'chainId': chain_id,
            'scanTime': sim_time
        })
        
        print(f"✅ [{self.component}] Simulation passed | Gas: {estimated_gas} | Time: {sim_time}ms")
    
    def report_simulation_failed(self, chain_id: int, token: str, reason: str):
        """
        Report failed simulation.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
            reason: Failure reason
        """
        data = {
            'status': 'rejected',
            'chainId': chain_id,
            'token': token,
            'error': reason,
            'timestamp': int(time.time() * 1000)
        }
        
        self._publish('execution_updates', data)
        print(f"🛑 [{self.component}] Simulation failed | Reason: {reason}")
    
    def report_execution_start(self, chain_id: int, token: str, tx_hash: str = ""):
        """
        Report execution start.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
            tx_hash: Transaction hash
        """
        self._exec_start_time = time.time()
        print(f"🚀 [{self.component}] Executing trade | Chain: {chain_id} | TX: {tx_hash[:16]}...")
    
    def report_execution_success(
        self,
        chain_id: int,
        token: str,
        tx_hash: str,
        profit: float,
        gas_used: int,
        gas_price: int
    ):
        """
        Report successful execution.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
            tx_hash: Transaction hash
            profit: Actual profit in USD
            gas_used: Gas units consumed
            gas_price: Gas price in wei
        """
        exec_time = int((time.time() - getattr(self, '_exec_start_time', time.time())) * 1000)
        self.execution_times.append(exec_time)
        
        gas_cost_eth = (gas_used * gas_price) / 1e18
        gas_cost_usd = gas_cost_eth * 2000  # Approximate ETH price
        
        data = {
            'status': 'executed',
            'chainId': chain_id,
            'token': token,
            'txHash': tx_hash,
            'profit': profit,
            'gasUsed': gas_used,
            'gasPrice': gas_price,
            'gasCost': gas_cost_usd,
            'executionTime': exec_time,
            'timestamp': int(time.time() * 1000)
        }
        
        self._publish('execution_updates', data)
        self._publish('system_metrics', {
            'chainId': chain_id,
            'scanTime': exec_time
        })
        
        print(f"✅ [{self.component}] Trade executed | Profit: ${profit:.2f} | Gas: {gas_used}")
        print(f"🔗 TX: {tx_hash}")
    
    def report_execution_failed(
        self,
        chain_id: int,
        token: str,
        tx_hash: str,
        reason: str,
        gas_used: int = 0
    ):
        """
        Report failed execution.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address
            tx_hash: Transaction hash
            reason: Failure reason
            gas_used: Gas units consumed (for reverted transactions)
        """
        data = {
            'status': 'failed',
            'chainId': chain_id,
            'token': token,
            'txHash': tx_hash,
            'error': reason,
            'gasUsed': gas_used,
            'timestamp': int(time.time() * 1000)
        }
        
        self._publish('execution_updates', data)
        self.report_error('error', f"Execution failed: {reason}", chain_id=chain_id, details={'txHash': tx_hash})
        
        print(f"❌ [{self.component}] Trade failed | Reason: {reason}")
    
    # ==================== PERFORMANCE METRICS ====================
    
    def report_scan_performance(self, scan_time_ms: float, opportunities_found: int = 0):
        """
        Report scan performance.
        
        Args:
            scan_time_ms: Scan duration in milliseconds
            opportunities_found: Number of opportunities found
        """
        self.scan_times.append(scan_time_ms)
        
        # Keep only last 100 measurements
        if len(self.scan_times) > 100:
            self.scan_times.pop(0)
        
        avg_scan_time = sum(self.scan_times) / len(self.scan_times)
        
        data = {
            'scanTime': scan_time_ms,
            'avgScanTime': avg_scan_time,
            'opportunitiesFound': opportunities_found
        }
        
        self._publish('system_metrics', data)
    
    def get_performance_stats(self) -> Dict[str, float]:
        """
        Get current performance statistics.
        
        Returns:
            Dictionary with average timing metrics
        """
        stats = {}
        
        if self.scan_times:
            stats['avgScanTime'] = sum(self.scan_times) / len(self.scan_times)
        
        if self.simulation_times:
            stats['avgSimulationTime'] = sum(self.simulation_times) / len(self.simulation_times)
        
        if self.execution_times:
            stats['avgExecutionTime'] = sum(self.execution_times) / len(self.execution_times)
        
        return stats
    
    # ==================== ERROR REPORTING ====================
    
    def report_error(
        self,
        level: str,
        message: str,
        chain_id: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        """
        Report error or warning.
        
        Args:
            level: Error level ('error', 'warning', 'critical')
            message: Error message
            chain_id: Related chain ID (optional)
            details: Additional error details
        """
        data = {
            'level': level,
            'component': self.component,
            'message': message,
            'timestamp': int(time.time() * 1000)
        }
        
        if chain_id is not None:
            data['chainId'] = chain_id
        
        if details:
            data['details'] = details
        
        self._publish('error_reports', data)
        
        emoji = '⚠️' if level == 'warning' else '❌'
        print(f"{emoji} [{self.component}] {level.upper()}: {message}")
    
    # ==================== HEALTH STATUS ====================
    
    def report_health(self, status: str, details: Dict[str, Any] = None):
        """
        Report component health status.
        
        Args:
            status: Health status ('healthy', 'degraded', 'critical')
            details: Additional health details
        """
        data = {
            'component': self.component,
            'status': status,
            'timestamp': int(time.time() * 1000)
        }
        
        if details:
            data.update(details)
        
        self._publish('system_metrics', data)
        
        emoji = '✅' if status == 'healthy' else '⚠️' if status == 'degraded' else '❌'
        print(f"{emoji} [{self.component}] Health: {status.upper()}")
    
    # ==================== CLEANUP ====================
    
    def close(self):
        """Close Redis connection."""
        if self.redis_client:
            try:
                self.redis_client.close()
                print(f"👋 [{self.component}] Metrics publisher closed")
            except:
                pass


# Singleton instance for convenience
_global_publisher = None

def get_metrics_publisher(component_name: str = "titan") -> MetricsPublisher:
    """
    Get or create global metrics publisher instance.
    
    Args:
        component_name: Name of the component
    
    Returns:
        MetricsPublisher instance
    """
    global _global_publisher
    
    if _global_publisher is None:
        _global_publisher = MetricsPublisher(component_name)
    
    return _global_publisher


# Example usage
if __name__ == "__main__":
    # Example integration
    metrics = MetricsPublisher("test")
    
    # Report chain connection
    metrics.report_chain_connected(
        chain_id=137,
        block_number=52847291,
        gas_price=30_000_000_000,
        tokens_tracked=103
    )
    
    # Report opportunity
    metrics.report_opportunity_detected(
        chain_id=137,
        token="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        expected_profit=7.23,
        loan_amount=50000,
        route="Uniswap V3 → Curve"
    )
    
    # Report simulation
    metrics.report_simulation_start(137, "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174")
    time.sleep(0.5)  # Simulate work
    metrics.report_simulation_success(
        chain_id=137,
        token="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        estimated_gas=285000,
        estimated_profit=7.23
    )
    
    # Report execution
    metrics.report_execution_start(137, "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "0xabc123...")
    time.sleep(1.0)  # Simulate work
    metrics.report_execution_success(
        chain_id=137,
        token="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",
        tx_hash="0xabc123def456...",
        profit=7.23,
        gas_used=285000,
        gas_price=30_000_000_000
    )
    
    # Report performance
    print("\n📊 Performance Stats:")
    print(metrics.get_performance_stats())
    
    metrics.close()
