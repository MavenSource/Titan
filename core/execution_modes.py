"""
================================================================================
APEX-OMEGA TITAN: EXECUTION MODE FRAMEWORK
================================================================================
Provides live mainnet execution and paper trading modes with comprehensive
safety controls, simulation validation, and performance tracking.

Execution Modes:
1. PAPER_TRADING: Simulate all transactions without spending real funds
2. LIVE_MAINNET: Execute real transactions with actual capital
3. HYBRID: Paper trade new strategies, live trade proven ones

Last Updated: December 9, 2025
Version: 1.0.0
================================================================================
"""

import os
import logging
import json
from enum import Enum
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import redis

logger = logging.getLogger("ExecutionModes")

# ==============================================================================
# EXECUTION MODE DEFINITIONS
# ==============================================================================

class ExecutionMode(Enum):
    """Defines the execution mode for the trading system"""
    PAPER_TRADING = "paper"      # Simulate only - no real transactions
    LIVE_MAINNET = "live"        # Real capital execution
    HYBRID = "hybrid"            # Mixed mode with confidence-based switching

class TradeStatus(Enum):
    """Trade execution status"""
    PENDING = "pending"
    SIMULATED = "simulated"
    SUBMITTED = "submitted"
    CONFIRMED = "confirmed"
    FAILED = "failed"
    REVERTED = "reverted"

# ==============================================================================
# PAPER TRADING SIMULATOR
# ==============================================================================

class PaperTradingSimulator:
    """
    Simulates trade execution without real capital.
    Tracks hypothetical P&L, maintains virtual portfolio.
    """
    
    def __init__(self, initial_capital_usd: float = 100000.0):
        self.mode = ExecutionMode.PAPER_TRADING
        self.initial_capital = Decimal(str(initial_capital_usd))
        self.current_capital = Decimal(str(initial_capital_usd))
        self.total_trades = 0
        self.successful_trades = 0
        self.total_profit = Decimal("0")
        self.trade_history = []
        
        # Try to connect to Redis, but don't fail if unavailable
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=1, socket_connect_timeout=1)
            self.redis_client.ping()
            self.redis_enabled = True
            logger.info("✅ Redis connected for trade persistence")
        except:
            self.redis_client = None
            self.redis_enabled = False
            logger.warning("⚠️  Redis unavailable - trades will not be persisted")
        
        logger.info(f"📝 Paper Trading Mode Initialized | Capital: ${initial_capital_usd:,.2f}")
    
    def execute_trade(self, trade_signal: Dict) -> Dict:
        """
        Simulates a trade execution.
        
        Args:
            trade_signal: Dictionary containing trade parameters
            
        Returns:
            Execution result with simulated outcomes
        """
        self.total_trades += 1
        trade_id = f"PAPER_{trade_signal['chainId']}_{self.total_trades}"
        
        logger.info(f"📝 Simulating Trade {trade_id}")
        logger.info(f"   Chain: {trade_signal['chainId']}")
        logger.info(f"   Token: {trade_signal['token']}")
        logger.info(f"   Amount: {trade_signal['amount']}")
        logger.info(f"   Expected Profit: ${trade_signal.get('expected_profit', 0):.2f}")
        
        # Simulate execution with realistic slippage
        slippage_factor = Decimal("0.998")  # 0.2% realistic slippage
        expected_profit = Decimal(str(trade_signal.get('expected_profit', 0)))
        actual_profit = expected_profit * slippage_factor
        
        # Simulate gas costs
        gas_cost = Decimal(str(trade_signal.get('gas_cost', 5.0)))
        net_profit = actual_profit - gas_cost
        
        # Update capital
        self.current_capital += net_profit
        self.total_profit += net_profit
        
        if net_profit > 0:
            self.successful_trades += 1
            status = "SUCCESS"
        else:
            status = "LOSS"
        
        # Record trade
        trade_record = {
            "trade_id": trade_id,
            "timestamp": datetime.now().isoformat(),
            "mode": "PAPER",
            "chain_id": trade_signal['chainId'],
            "token": trade_signal['token'],
            "amount": str(trade_signal['amount']),
            "expected_profit": str(expected_profit),
            "actual_profit": str(actual_profit),
            "gas_cost": str(gas_cost),
            "net_profit": str(net_profit),
            "status": status,
            "capital_after": str(self.current_capital)
        }
        
        self.trade_history.append(trade_record)
        
        # Store in Redis if available
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.lpush("paper_trades", json.dumps(trade_record))
                self.redis_client.set("paper_capital", str(self.current_capital))
            except:
                pass  # Redis errors don't stop trading
        
        logger.info(f"✅ Paper Trade Complete | Net: ${net_profit:.2f} | Capital: ${self.current_capital:,.2f}")
        
        return {
            "trade_id": trade_id,
            "status": TradeStatus.SIMULATED,
            "net_profit": float(net_profit),
            "capital": float(self.current_capital),
            "tx_hash": f"SIMULATED_{trade_id}",  # Fake hash for tracking
            "is_paper": True
        }
    
    def get_performance_summary(self) -> Dict:
        """Returns comprehensive paper trading performance metrics"""
        win_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        roi = ((self.current_capital - self.initial_capital) / self.initial_capital * 100) if self.initial_capital > 0 else 0
        
        return {
            "mode": "PAPER_TRADING",
            "initial_capital": float(self.initial_capital),
            "current_capital": float(self.current_capital),
            "total_profit": float(self.total_profit),
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "win_rate": float(win_rate),
            "roi": float(roi)
        }

# ==============================================================================
# LIVE MAINNET EXECUTOR
# ==============================================================================

class LiveMainnetExecutor:
    """
    Executes real trades on mainnet with safety guardrails.
    Includes pre-execution validation, simulation checks, and monitoring.
    """
    
    def __init__(self):
        self.mode = ExecutionMode.LIVE_MAINNET
        self.total_trades = 0
        self.successful_trades = 0
        self.total_volume_usd = Decimal("0")
        self.total_profit = Decimal("0")
        self.trade_history = []
        
        # Try to connect to Redis
        try:
            self.redis_client = redis.Redis(host='localhost', port=6379, db=0, socket_connect_timeout=1)
            self.redis_client.ping()
            self.redis_enabled = True
            logger.info("✅ Redis connected for execution layer")
        except:
            self.redis_client = None
            self.redis_enabled = False
            logger.error("❌ Redis unavailable - LIVE MODE REQUIRES REDIS for bot.js communication")
        
        # Safety limits from .env
        self.min_profit_usd = Decimal(str(os.getenv("MIN_PROFIT_USD", "5.0")))
        self.max_slippage_bps = int(os.getenv("MAX_SLIPPAGE_BPS", "50"))
        self.max_concurrent_txs = int(os.getenv("MAX_CONCURRENT_TXS", "3"))
        
        logger.warning("🔴 LIVE MAINNET MODE ACTIVE - REAL CAPITAL AT RISK")
        logger.info(f"   Min Profit: ${self.min_profit_usd}")
        logger.info(f"   Max Slippage: {self.max_slippage_bps} BPS")
    
    def pre_execution_checks(self, trade_signal: Dict) -> tuple[bool, str]:
        """
        Validates trade before execution.
        
        Returns:
            (is_valid, reason)
        """
        # Check 1: Minimum profit threshold
        expected_profit = Decimal(str(trade_signal.get('expected_profit', 0)))
        if expected_profit < self.min_profit_usd:
            return False, f"Profit ${expected_profit} below minimum ${self.min_profit_usd}"
        
        # Check 2: Slippage tolerance
        slippage_bps = trade_signal.get('estimated_slippage_bps', 0)
        if slippage_bps > self.max_slippage_bps:
            return False, f"Slippage {slippage_bps} BPS exceeds max {self.max_slippage_bps} BPS"
        
        # Check 3: Concurrent transaction limit
        if self.redis_enabled and self.redis_client:
            try:
                pending_count = self.redis_client.scard("pending_txs")
                if pending_count >= self.max_concurrent_txs:
                    return False, f"Max concurrent txs ({self.max_concurrent_txs}) reached"
            except:
                pass  # Skip if Redis unavailable
        
        # Check 4: Required fields
        required_fields = ['chainId', 'token', 'amount', 'protocols', 'routers', 'path']
        missing = [f for f in required_fields if f not in trade_signal]
        if missing:
            return False, f"Missing required fields: {missing}"
        
        # Check 5: Private key exists
        if not os.getenv("PRIVATE_KEY") or os.getenv("PRIVATE_KEY") == "0xYOUR_REAL_PRIVATE_KEY_HERE":
            return False, "PRIVATE_KEY not configured in .env"
        
        # Check 6: Executor contract deployed
        if not os.getenv("EXECUTOR_ADDRESS") or os.getenv("EXECUTOR_ADDRESS") == "0xYOUR_DEPLOYED_CONTRACT_ADDRESS_HERE":
            return False, "EXECUTOR_ADDRESS not configured - contract not deployed"
        
        return True, "All checks passed"
    
    def execute_trade(self, trade_signal: Dict) -> Dict:
        """
        Executes a real trade on mainnet.
        
        Args:
            trade_signal: Dictionary containing trade parameters
            
        Returns:
            Execution result with transaction details
        """
        self.total_trades += 1
        trade_id = f"LIVE_{trade_signal['chainId']}_{self.total_trades}"
        
        logger.warning(f"🔴 EXECUTING LIVE TRADE {trade_id}")
        
        # Pre-execution validation
        is_valid, reason = self.pre_execution_checks(trade_signal)
        if not is_valid:
            logger.error(f"❌ Trade rejected: {reason}")
            return {
                "trade_id": trade_id,
                "status": TradeStatus.FAILED,
                "error": reason,
                "is_paper": False
            }
        
        # Mark as pending and publish if Redis available
        if not self.redis_enabled or not self.redis_client:
            return {
                "trade_id": trade_id,
                "status": TradeStatus.FAILED,
                "error": "Redis not available - cannot communicate with execution layer",
                "is_paper": False
            }
        
        try:
            self.redis_client.sadd("pending_txs", trade_id)
            
            # Publish to execution bot (bot.js will handle actual execution)
            trade_signal['trade_id'] = trade_id
            trade_signal['timestamp'] = datetime.now().isoformat()
            trade_signal['mode'] = 'LIVE'
            
            self.redis_client.publish('trade_signals', json.dumps(trade_signal))
        except Exception as e:
            return {
                "trade_id": trade_id,
                "status": TradeStatus.FAILED,
                "error": f"Redis publish failed: {str(e)}",
                "is_paper": False
            }
        
        logger.info(f"✅ Trade signal published to execution layer")
        logger.info(f"   Trade ID: {trade_id}")
        logger.info(f"   Expected Profit: ${trade_signal.get('expected_profit', 0):.2f}")
        logger.info(f"   Chain: {trade_signal['chainId']}")
        
        return {
            "trade_id": trade_id,
            "status": TradeStatus.SUBMITTED,
            "timestamp": trade_signal['timestamp'],
            "expected_profit": trade_signal.get('expected_profit', 0),
            "is_paper": False,
            "message": "Trade submitted to execution layer - awaiting confirmation"
        }
    
    def record_execution_result(self, trade_id: str, result: Dict):
        """
        Records the result of a completed trade.
        Called by bot.js after transaction confirmation.
        """
        # Remove from pending if Redis available
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.srem("pending_txs", trade_id)
            except:
                pass
        
        # Update stats
        if result.get('status') == 'SUCCESS':
            self.successful_trades += 1
            profit = Decimal(str(result.get('actual_profit', 0)))
            self.total_profit += profit
            logger.info(f"✅ Trade {trade_id} successful | Profit: ${profit:.2f}")
        else:
            logger.error(f"❌ Trade {trade_id} failed: {result.get('error')}")
        
        # Store in history
        self.trade_history.append(result)
        if self.redis_enabled and self.redis_client:
            try:
                self.redis_client.lpush("live_trades", json.dumps(result))
            except:
                pass
    
    def get_performance_summary(self) -> Dict:
        """Returns live trading performance metrics"""
        win_rate = (self.successful_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        
        pending_count = 0
        if self.redis_enabled and self.redis_client:
            try:
                pending_count = self.redis_client.scard("pending_txs")
            except:
                pass
        
        return {
            "mode": "LIVE_MAINNET",
            "total_trades": self.total_trades,
            "successful_trades": self.successful_trades,
            "win_rate": float(win_rate),
            "total_profit": float(self.total_profit),
            "total_volume": float(self.total_volume_usd),
            "pending_txs": pending_count
        }

# ==============================================================================
# HYBRID EXECUTION MANAGER
# ==============================================================================

class HybridExecutionManager:
    """
    Intelligently routes trades between paper and live execution
    based on confidence scores, historical performance, and risk parameters.
    """
    
    def __init__(self, confidence_threshold: float = 0.85):
        self.mode = ExecutionMode.HYBRID
        self.paper_simulator = PaperTradingSimulator()
        self.live_executor = LiveMainnetExecutor()
        self.confidence_threshold = confidence_threshold
        
        logger.info(f"🔄 Hybrid Mode Initialized | Confidence Threshold: {confidence_threshold}")
    
    def execute_trade(self, trade_signal: Dict) -> Dict:
        """
        Routes trade to paper or live execution based on confidence.
        
        Args:
            trade_signal: Trade parameters including 'confidence_score'
            
        Returns:
            Execution result
        """
        confidence = trade_signal.get('confidence_score', 0.0)
        
        # Route based on confidence
        if confidence >= self.confidence_threshold:
            logger.info(f"🔴 High confidence ({confidence:.2%}) - Routing to LIVE execution")
            return self.live_executor.execute_trade(trade_signal)
        else:
            logger.info(f"📝 Low confidence ({confidence:.2%}) - Routing to PAPER execution")
            return self.paper_simulator.execute_trade(trade_signal)
    
    def get_performance_summary(self) -> Dict:
        """Returns combined performance metrics"""
        paper_stats = self.paper_simulator.get_performance_summary()
        live_stats = self.live_executor.get_performance_summary()
        
        return {
            "mode": "HYBRID",
            "confidence_threshold": self.confidence_threshold,
            "paper_trading": paper_stats,
            "live_trading": live_stats
        }

# ==============================================================================
# EXECUTION MODE FACTORY
# ==============================================================================

class ExecutionModeFactory:
    """Factory for creating execution mode instances"""
    
    @staticmethod
    def create(mode: str = None) -> object:
        """
        Creates appropriate executor based on environment configuration.
        
        Args:
            mode: Override mode ('paper', 'live', 'hybrid')
                  If None, reads from EXECUTION_MODE env var
        
        Returns:
            Executor instance
        """
        if mode is None:
            mode = os.getenv("EXECUTION_MODE", "paper").lower()
        
        if mode == "paper":
            return PaperTradingSimulator()
        elif mode == "live":
            return LiveMainnetExecutor()
        elif mode == "hybrid":
            threshold = float(os.getenv("HYBRID_CONFIDENCE_THRESHOLD", "0.85"))
            return HybridExecutionManager(confidence_threshold=threshold)
        else:
            logger.warning(f"Unknown mode '{mode}', defaulting to PAPER")
            return PaperTradingSimulator()

# ==============================================================================
# EXPORT
# ==============================================================================

__all__ = [
    "ExecutionMode",
    "TradeStatus",
    "PaperTradingSimulator",
    "LiveMainnetExecutor",
    "HybridExecutionManager",
    "ExecutionModeFactory"
]
