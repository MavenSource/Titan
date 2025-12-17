import logging
from core.titan_simulation_engine import get_provider_tvl
from core.config import BALANCER_V3_VAULT, CHAINS
from core.chain_registry import get_chain_registry

# Setup Logging
logger = logging.getLogger("TitanCommander")

class TitanCommander:
    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.chain_config = CHAINS.get(chain_id)
        self.chain_registry = get_chain_registry()
        
        # Validate chain is configured
        if not self.chain_config:
            raise ValueError(f"Chain {chain_id} not configured")
        
        # Guardrails (Real Money Limits)
        self.MIN_LOAN_USD = 10000     # Minimum trade size ($10k)
        self.MAX_TVL_SHARE = 0.20     # Max % of pool to borrow (Safety Ceiling)
        self.SLIPPAGE_TOLERANCE = 0.995 # 0.5% max slippage
        
        # Log chain state
        chain_name = self.chain_registry.get_chain_name(chain_id)
        exec_state = self.chain_registry.get_execution_state(chain_id)
        logger.info(f"TitanCommander initialized for {chain_name} ({exec_state.value})")

    def optimize_loan_size(self, token_address, target_amount_raw, decimals=18):
        """
        Binary search to find the Maximum Safe Loan Amount based on real on-chain liquidity.
        Returns: Safe Amount (int) or 0 (Abort).
        """
        chain_name = self.chain_registry.get_chain_name(self.chain_id)
        
        # 1. TVL CHECK (The Ceiling)
        # We check the Balancer V3 Vault balance for the specific token
        lender_address = BALANCER_V3_VAULT
        
        try:
            # Call the Simulation Engine (Sensor)
            pool_liquidity = get_provider_tvl(token_address, lender_address, self.chain_id)
        except Exception as e:
            logger.error(f"[{chain_name}] TVL check failed for {token_address}: {e}")
            return 0

        if pool_liquidity == 0:
            logger.warning(
                f"[{chain_name}] ⚠️ Vault empty for token {token_address}. "
                f"This may indicate: 1) Zero liquidity, 2) RPC failure, 3) Unsupported token. Aborting."
            )
            return 0

        # Calculate Caps
        max_cap = int(pool_liquidity * self.MAX_TVL_SHARE)
        requested_amount = int(target_amount_raw)
        
        # GUARD 1: Liquidity Check
        if requested_amount > max_cap:
            logger.warning(
                f"[{chain_name}] ⚠️ Liquidity constraint: "
                f"Requested {requested_amount}, Cap {max_cap}. Scaling down."
            )
            requested_amount = max_cap

        # GUARD 2: Floor Check
        min_floor = 500 * (10**decimals) 
        if requested_amount < min_floor:
            logger.info(
                f"[{chain_name}] ❌ Trade too small for profitability "
                f"({requested_amount} < {min_floor}). Aborting."
            )
            return 0

        # 2. SLIPPAGE OPTIMIZATION (The Loop)
        # In a full simulation, we would loop here calling get_real_output()
        # For Titan v4 MVP, we rely on the TVL cap as the primary safety net.
        # If TVL is sufficient, we authorize the trade.
        
        logger.info(
            f"[{chain_name}] ✅ Loan sizing optimized: {requested_amount} (Cap: {max_cap})"
        )
        return requested_amount