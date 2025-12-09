#!/usr/bin/env python3
"""
================================================================================
TITAN EXECUTION CLIENT - Python Interface to Node.js Execution Server
================================================================================
Direct HTTP/WebSocket communication between Python brain and Node.js execution
layer without Redis dependency.
================================================================================
"""

import os
import json
import asyncio
import logging
import aiohttp
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict

logger = logging.getLogger("ExecutionClient")

@dataclass
class TradeSignal:
    """Trade signal data structure"""
    chainId: int
    token: str
    amount: str
    flashSource: int  # 1=Balancer, 2=Aave
    protocols: List[int]
    routers: List[str]
    path: List[str]
    extras: List[bytes]
    expected_profit: float
    gas_estimate: int = 500000
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class ExecutionClient:
    """
    Client for communicating with Node.js execution server.
    Supports both HTTP requests and WebSocket streaming.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 8545,
        use_websocket: bool = False,
        timeout: int = 30
    ):
        self.base_url = f"http://{host}:{port}"
        self.ws_url = f"ws://{host}:{port}"
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.use_websocket = use_websocket
        self.ws_connection = None
        self.ws_task = None
        
        logger.info(f"ExecutionClient initialized: {self.base_url}")
    
    async def health_check(self) -> Dict:
        """Check if execution server is healthy"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/health") as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Server health: {data}")
                        return data
                    else:
                        logger.error(f"Health check failed: {resp.status}")
                        return {"status": "unhealthy", "error": f"HTTP {resp.status}"}
        except Exception as e:
            logger.error(f"Health check error: {e}")
            return {"status": "error", "error": str(e)}
    
    async def execute_signal(self, signal: TradeSignal) -> Dict:
        """
        Execute a single trade signal via HTTP.
        
        Args:
            signal: TradeSignal object
            
        Returns:
            Execution result dictionary
        """
        try:
            signal_dict = signal.to_dict()
            
            logger.info(f"Sending trade signal for chain {signal.chainId}")
            logger.debug(f"Signal data: {json.dumps(signal_dict, indent=2)}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/execute",
                    json=signal_dict,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    result = await resp.json()
                    
                    if result.get("success"):
                        logger.info(f"✅ Execution successful: {result.get('mode')}")
                        if result.get("txHash"):
                            logger.info(f"   TX Hash: {result['txHash']}")
                    else:
                        logger.error(f"❌ Execution failed: {result.get('error')}")
                    
                    return result
                    
        except asyncio.TimeoutError:
            logger.error(f"Execution timeout after {self.timeout.total}s")
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def execute_batch(self, signals: List[TradeSignal]) -> Dict:
        """
        Execute multiple trade signals in batch.
        
        Args:
            signals: List of TradeSignal objects
            
        Returns:
            Batch execution result
        """
        try:
            signals_data = [s.to_dict() for s in signals]
            
            logger.info(f"Sending batch of {len(signals)} trade signals")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/execute/batch",
                    json={"signals": signals_data},
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    result = await resp.json()
                    
                    logger.info(f"Batch result: {result.get('succeeded')}/{result.get('total')} succeeded")
                    return result
                    
        except Exception as e:
            logger.error(f"Batch execution error: {e}")
            return {"success": False, "error": str(e)}
    
    async def simulate_signal(self, signal: TradeSignal) -> Dict:
        """
        Simulate trade without execution.
        
        Args:
            signal: TradeSignal object
            
        Returns:
            Simulation result
        """
        try:
            signal_dict = signal.to_dict()
            
            logger.info(f"Simulating trade for chain {signal.chainId}")
            
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.post(
                    f"{self.base_url}/simulate",
                    json=signal_dict,
                    headers={"Content-Type": "application/json"}
                ) as resp:
                    result = await resp.json()
                    
                    if result.get("success"):
                        logger.info("✅ Simulation successful")
                    else:
                        logger.error(f"❌ Simulation failed: {result.get('error')}")
                    
                    return result
                    
        except Exception as e:
            logger.error(f"Simulation error: {e}")
            return {"success": False, "error": str(e)}
    
    async def get_stats(self) -> Dict:
        """Get execution statistics from server"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(f"{self.base_url}/stats") as resp:
                    stats = await resp.json()
                    logger.debug(f"Server stats: {stats}")
                    return stats
        except Exception as e:
            logger.error(f"Stats error: {e}")
            return {}
    
    async def connect_websocket(self, callback=None):
        """
        Establish WebSocket connection for real-time updates.
        
        Args:
            callback: Function to call when messages are received
        """
        try:
            logger.info(f"Connecting to WebSocket: {self.ws_url}")
            
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(self.ws_url) as ws:
                    self.ws_connection = ws
                    logger.info("✅ WebSocket connected")
                    
                    async for msg in ws:
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            logger.debug(f"WS message: {data.get('type')}")
                            
                            if callback:
                                await callback(data)
                        elif msg.type == aiohttp.WSMsgType.ERROR:
                            logger.error(f"WS error: {ws.exception()}")
                            break
                        elif msg.type == aiohttp.WSMsgType.CLOSED:
                            logger.info("WebSocket closed")
                            break
                            
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            self.ws_connection = None
    
    async def send_via_websocket(self, signal: TradeSignal) -> bool:
        """Send trade signal via WebSocket"""
        if not self.ws_connection:
            logger.error("WebSocket not connected")
            return False
        
        try:
            message = {
                "type": "execute",
                "signal": signal.to_dict()
            }
            await self.ws_connection.send_json(message)
            logger.info(f"Sent signal via WebSocket for chain {signal.chainId}")
            return True
        except Exception as e:
            logger.error(f"WebSocket send error: {e}")
            return False
    
    async def close(self):
        """Close connections"""
        if self.ws_connection:
            await self.ws_connection.close()
        logger.info("ExecutionClient closed")


class ExecutionManager:
    """
    High-level manager for Python brain to submit trades to Node.js execution layer.
    Handles connection pooling, retries, and mode detection.
    """
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        mode: str = None,
        max_retries: int = 3
    ):
        # Get config from environment or defaults
        self.host = host or os.getenv("EXECUTION_HOST", "localhost")
        self.port = port or int(os.getenv("EXECUTION_PORT", "8545"))
        self.mode = mode or os.getenv("EXECUTION_MODE", "PAPER")
        self.max_retries = max_retries
        
        self.client = ExecutionClient(self.host, self.port)
        self.stats = {
            "sent": 0,
            "succeeded": 0,
            "failed": 0,
            "retried": 0
        }
        
        logger.info(f"ExecutionManager initialized: {self.mode} mode @ {self.host}:{self.port}")
    
    async def initialize(self) -> bool:
        """Initialize and verify connection to execution server"""
        try:
            health = await self.client.health_check()
            
            if health.get("status") == "healthy":
                server_mode = health.get("mode", "UNKNOWN")
                
                if server_mode != self.mode:
                    logger.warning(f"Mode mismatch: Python={self.mode}, Server={server_mode}")
                    logger.warning("Using server mode for consistency")
                    self.mode = server_mode
                
                logger.info(f"✅ Connected to execution server: {server_mode} mode")
                logger.info(f"   Chains available: {health.get('chains', 0)}")
                return True
            else:
                logger.error(f"Server unhealthy: {health}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to connect to execution server: {e}")
            logger.error(f"Make sure execution server is running: node execution/execution_server.js")
            return False
    
    async def submit_trade(
        self,
        chain_id: int,
        token: str,
        amount: str,
        flash_source: int,
        protocols: List[int],
        routers: List[str],
        path: List[str],
        extras: List[bytes],
        expected_profit: float
    ) -> Dict:
        """
        Submit trade signal to execution layer with retry logic.
        
        Args:
            chain_id: Blockchain network ID
            token: Token address to borrow
            amount: Amount to borrow (wei)
            flash_source: 1=Balancer V3, 2=Aave V3
            protocols: Protocol IDs for route
            routers: Router addresses
            path: Token swap path
            extras: Extra data for each swap
            expected_profit: Expected profit in USD
            
        Returns:
            Execution result dictionary
        """
        signal = TradeSignal(
            chainId=chain_id,
            token=token,
            amount=amount,
            flashSource=flash_source,
            protocols=protocols,
            routers=routers,
            path=path,
            extras=extras,
            expected_profit=expected_profit
        )
        
        self.stats["sent"] += 1
        
        # Retry logic
        for attempt in range(self.max_retries):
            try:
                result = await self.client.execute_signal(signal)
                
                if result.get("success"):
                    self.stats["succeeded"] += 1
                    return result
                else:
                    if attempt < self.max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1} failed, retrying...")
                        self.stats["retried"] += 1
                        await asyncio.sleep(1)
                    else:
                        self.stats["failed"] += 1
                        return result
                        
            except Exception as e:
                logger.error(f"Submit error (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    self.stats["retried"] += 1
                    await asyncio.sleep(1)
                else:
                    self.stats["failed"] += 1
                    return {"success": False, "error": str(e)}
        
        return {"success": False, "error": "Max retries exceeded"}
    
    async def submit_batch(self, signals_data: List[Dict]) -> Dict:
        """Submit multiple trade signals in batch"""
        signals = [TradeSignal(**data) for data in signals_data]
        self.stats["sent"] += len(signals)
        
        result = await self.client.execute_batch(signals)
        
        self.stats["succeeded"] += result.get("succeeded", 0)
        self.stats["failed"] += result.get("failed", 0)
        
        return result
    
    async def get_statistics(self) -> Dict:
        """Get combined statistics from client and server"""
        server_stats = await self.client.get_stats()
        
        return {
            "client": self.stats,
            "server": server_stats,
            "mode": self.mode
        }
    
    async def close(self):
        """Close execution manager"""
        await self.client.close()
        logger.info(f"ExecutionManager closed. Stats: {self.stats}")


# Convenience function for direct usage
async def execute_trade(
    chain_id: int,
    token: str,
    amount: str,
    flash_source: int,
    protocols: List[int],
    routers: List[str],
    path: List[str],
    extras: List[bytes],
    expected_profit: float,
    host: str = "localhost",
    port: int = 8545
) -> Dict:
    """
    Execute a single trade directly without manager.
    Useful for quick tests or one-off executions.
    """
    client = ExecutionClient(host, port)
    
    signal = TradeSignal(
        chainId=chain_id,
        token=token,
        amount=amount,
        flashSource=flash_source,
        protocols=protocols,
        routers=routers,
        path=path,
        extras=extras,
        expected_profit=expected_profit
    )
    
    result = await client.execute_signal(signal)
    await client.close()
    
    return result


# Example usage
if __name__ == "__main__":
    import sys
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    async def test_execution():
        """Test execution client"""
        print("\n" + "="*80)
        print("TITAN EXECUTION CLIENT - TEST")
        print("="*80 + "\n")
        
        # Initialize manager
        manager = ExecutionManager()
        
        # Check connection
        connected = await manager.initialize()
        if not connected:
            print("❌ Failed to connect to execution server")
            print("Start server with: node execution/execution_server.js")
            return
        
        print("\n✅ Connected to execution server\n")
        
        # Test signal
        result = await manager.submit_trade(
            chain_id=1,
            token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            amount="1000000000",  # 1000 USDC
            flash_source=1,  # Balancer V3
            protocols=[0, 1],  # Uniswap V2, V3
            routers=[
                "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
                "0xE592427A0AEce92De3Edee1F18E0157C05861564"
            ],
            path=[
                "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
                "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
            ],
            extras=[b'', b''],
            expected_profit=50.0
        )
        
        print(f"\n📊 Execution Result:")
        print(json.dumps(result, indent=2))
        
        # Get stats
        stats = await manager.get_statistics()
        print(f"\n📈 Statistics:")
        print(json.dumps(stats, indent=2))
        
        await manager.close()
        print("\n✅ Test complete\n")
    
    # Run test
    asyncio.run(test_execution())
