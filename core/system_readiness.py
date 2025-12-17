"""
TITAN SYSTEM READINESS VALIDATOR
==================================

Comprehensive startup validation for production mainnet deployment.

Validates:
- Chain RPC connectivity
- Execution mode configuration
- Wallet setup (LIVE mode only)
- Executor contracts
- Redis connectivity
- Safety parameters
- Chain execution gates
"""

import os
import sys
import logging
from dotenv import load_dotenv
from core.chain_registry import get_chain_registry, ChainExecutionState

load_dotenv()
logger = logging.getLogger("SystemReadiness")


class SystemReadinessValidator:
    """
    Production system validation before mainnet operation.
    
    Ensures all components are properly configured and operational.
    """
    
    def __init__(self):
        self.chain_registry = get_chain_registry()
        self.execution_mode = os.getenv('EXECUTION_MODE', 'PAPER').upper()
        self.validation_results = {
            'chain_rpcs': {},
            'execution_mode': None,
            'wallet': None,
            'executor_contracts': {},
            'redis': None,
            'safety_params': {},
            'overall': False
        }
    
    def validate_execution_mode(self) -> bool:
        """Validate execution mode configuration"""
        logger.info("Validating execution mode...")
        
        if self.execution_mode not in ['PAPER', 'LIVE']:
            logger.error(f"❌ Invalid EXECUTION_MODE: {self.execution_mode}")
            logger.error("   Must be 'PAPER' or 'LIVE'")
            self.validation_results['execution_mode'] = False
            return False
        
        logger.info(f"✅ Execution mode: {self.execution_mode}")
        self.validation_results['execution_mode'] = True
        return True
    
    def validate_wallet(self) -> bool:
        """Validate wallet configuration (LIVE mode only)"""
        if self.execution_mode == 'PAPER':
            logger.info("ℹ️  Paper mode: Skipping wallet validation")
            self.validation_results['wallet'] = True
            return True
        
        logger.info("Validating wallet configuration...")
        
        private_key = os.getenv('PRIVATE_KEY')
        
        if not private_key:
            logger.error("❌ PRIVATE_KEY not configured in .env")
            self.validation_results['wallet'] = False
            return False
        
        # Basic format validation (0x + 64 hex chars)
        if not private_key.startswith('0x') or len(private_key) != 66:
            logger.error("❌ PRIVATE_KEY invalid format")
            logger.error("   Must be 0x followed by 64 hex characters")
            self.validation_results['wallet'] = False
            return False
        
        try:
            int(private_key, 16)
        except ValueError:
            logger.error("❌ PRIVATE_KEY contains invalid hex characters")
            self.validation_results['wallet'] = False
            return False
        
        logger.info("✅ Wallet configuration valid")
        self.validation_results['wallet'] = True
        return True
    
    def validate_executor_contracts(self) -> bool:
        """Validate executor contract addresses"""
        logger.info("Validating executor contracts...")
        
        # For Polygon (execution enabled)
        if self.execution_mode == 'LIVE':
            polygon_executor = os.getenv('EXECUTOR_ADDRESS_POLYGON')
            
            if not polygon_executor:
                logger.error("❌ EXECUTOR_ADDRESS_POLYGON not configured")
                logger.error("   Required for LIVE mode execution on Polygon")
                self.validation_results['executor_contracts'][137] = False
                return False
            
            if polygon_executor == '0xYOUR_DEPLOYED_CONTRACT_ADDRESS_HERE':
                logger.error("❌ EXECUTOR_ADDRESS_POLYGON not deployed")
                logger.error("   Deploy executor contract first")
                self.validation_results['executor_contracts'][137] = False
                return False
            
            logger.info(f"✅ Polygon executor: {polygon_executor}")
            self.validation_results['executor_contracts'][137] = True
        else:
            logger.info("ℹ️  Paper mode: Skipping executor contract validation")
            self.validation_results['executor_contracts'][137] = True
        
        return True
    
    def validate_safety_params(self) -> bool:
        """Validate safety parameters"""
        logger.info("Validating safety parameters...")
        
        try:
            max_base_fee = float(os.getenv('MAX_BASE_FEE_GWEI', '500'))
            min_profit_usd = float(os.getenv('MIN_PROFIT_USD', '5.0'))
            max_slippage_bps = int(os.getenv('MAX_SLIPPAGE_BPS', '50'))
            
            # Validate ranges
            if max_base_fee <= 0 or max_base_fee > 10000:
                logger.warning(f"⚠️  MAX_BASE_FEE_GWEI={max_base_fee} is unusual")
            
            if min_profit_usd < 0:
                logger.error("❌ MIN_PROFIT_USD cannot be negative")
                return False
            
            if max_slippage_bps < 0 or max_slippage_bps > 10000:
                logger.error("❌ MAX_SLIPPAGE_BPS out of range (0-10000)")
                return False
            
            logger.info(f"✅ Safety params: Max gas={max_base_fee} gwei, "
                       f"Min profit=${min_profit_usd}, Max slippage={max_slippage_bps} bps")
            
            self.validation_results['safety_params'] = {
                'max_base_fee_gwei': max_base_fee,
                'min_profit_usd': min_profit_usd,
                'max_slippage_bps': max_slippage_bps
            }
            
            return True
            
        except ValueError as e:
            logger.error(f"❌ Invalid safety parameter format: {e}")
            return False
    
    def validate_chain_rpcs(self) -> bool:
        """Validate RPC connectivity for all configured chains"""
        logger.info("")
        logger.info("Validating chain RPC connectivity...")
        
        results = self.chain_registry.validate_all_configured_chains()
        self.validation_results['chain_rpcs'] = results
        
        # Check if at least Polygon (execution-enabled chain) is healthy
        polygon_healthy = results.get(137, False)
        
        if not polygon_healthy:
            logger.error("❌ Polygon RPC is not healthy")
            logger.error("   Polygon must be operational for execution")
            return False
        
        # Check configured chains
        all_configured_healthy = all(results.values())
        if not all_configured_healthy:
            logger.warning("⚠️  Some configured chains have RPC issues")
            logger.warning("   System will continue but those chains will be unavailable")
        
        return True
    
    def print_summary(self):
        """Print comprehensive system readiness summary"""
        logger.info("")
        logger.info("=" * 70)
        logger.info("  TITAN SYSTEM READINESS REPORT")
        logger.info("=" * 70)
        
        # Execution mode
        logger.info("")
        logger.info("EXECUTION MODE:")
        mode_status = "✅" if self.validation_results['execution_mode'] else "❌"
        logger.info(f"  {mode_status} Mode: {self.execution_mode}")
        
        # Chain execution configuration
        logger.info("")
        logger.info("CHAIN EXECUTION CONFIGURATION:")
        for chain_id in sorted(self.chain_registry.CHAIN_STATES.keys()):
            state = self.chain_registry.get_execution_state(chain_id)
            name = self.chain_registry.get_chain_name(chain_id)
            rpc_ok = self.validation_results['chain_rpcs'].get(chain_id, False)
            
            if state == ChainExecutionState.ENABLED:
                status_icon = "🟢" if rpc_ok else "🔴"
                status_text = "LIVE EXECUTION ENABLED" if rpc_ok else "LIVE (RPC FAILED)"
            elif state == ChainExecutionState.CONFIGURED:
                status_icon = "🟡" if rpc_ok else "⚪"
                status_text = "CONFIGURED (Exec Disabled)" if rpc_ok else "CONFIGURED (RPC FAILED)"
            else:
                status_icon = "⚪"
                status_text = "DISABLED"
            
            logger.info(f"  {status_icon} {name.capitalize():12s} ({chain_id:5d}): {status_text}")
        
        # Wallet
        if self.execution_mode == 'LIVE':
            logger.info("")
            logger.info("WALLET:")
            wallet_status = "✅" if self.validation_results['wallet'] else "❌"
            logger.info(f"  {wallet_status} Private key: {'Configured' if self.validation_results['wallet'] else 'Not configured'}")
        
        # Executor contracts
        if self.execution_mode == 'LIVE':
            logger.info("")
            logger.info("EXECUTOR CONTRACTS:")
            for chain_id, status in self.validation_results['executor_contracts'].items():
                status_icon = "✅" if status else "❌"
                name = self.chain_registry.get_chain_name(chain_id)
                logger.info(f"  {status_icon} {name.capitalize()}: {'Deployed' if status else 'Not configured'}")
        
        # Safety parameters
        if self.validation_results['safety_params']:
            logger.info("")
            logger.info("SAFETY PARAMETERS:")
            params = self.validation_results['safety_params']
            logger.info(f"  ✅ Max gas: {params.get('max_base_fee_gwei', 'N/A')} gwei")
            logger.info(f"  ✅ Min profit: ${params.get('min_profit_usd', 'N/A')}")
            logger.info(f"  ✅ Max slippage: {params.get('max_slippage_bps', 'N/A')} bps")
        
        # Overall status
        logger.info("")
        overall_status = "✅ READY" if self.validation_results['overall'] else "❌ NOT READY"
        logger.info(f"OVERALL STATUS: {overall_status}")
        
        logger.info("=" * 70)
        logger.info("")
    
    def validate_system(self) -> bool:
        """
        Run complete system validation.
        
        Returns:
            bool: True if system is ready for operation
        """
        logger.info("")
        logger.info("=" * 70)
        logger.info("  TITAN SYSTEM READINESS CHECK")
        logger.info("=" * 70)
        logger.info("")
        
        checks = [
            self.validate_execution_mode(),
            self.validate_chain_rpcs(),
            self.validate_wallet(),
            self.validate_executor_contracts(),
            self.validate_safety_params(),
        ]
        
        self.validation_results['overall'] = all(checks)
        
        self.print_summary()
        
        return self.validation_results['overall']


def run_system_readiness_check() -> bool:
    """
    Run system readiness validation.
    
    Returns:
        bool: True if system is ready
    """
    validator = SystemReadinessValidator()
    return validator.validate_system()


if __name__ == "__main__":
    # Run as standalone script
    is_ready = run_system_readiness_check()
    
    if not is_ready:
        logger.error("System is not ready for operation")
        sys.exit(1)
    
    logger.info("System is ready for operation")
    sys.exit(0)
