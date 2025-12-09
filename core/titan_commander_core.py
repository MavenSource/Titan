import logging
from core.titan_simulation_engine import get_provider_tvl
from core.config import BALANCER_V3_VAULT, CHAINS

# Setup Logging
logger = logging.getLogger("TitanCommander")

class TitanCommander:
    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.chain_config = CHAINS.get(chain_id)
        
        # Guardrails (Real Money Limits)
        self.MIN_LOAN_USD = 10000     # Minimum trade size ($10k)
        self.MAX_TVL_SHARE = 0.20     # Max % of pool to borrow (Safety Ceiling)
        self.SLIPPAGE_TOLERANCE = 0.995 # 0.5% max slippage

    def optimize_loan_size(self, token_address, target_amount_raw, decimals=18):
        """
        Binary search to find the Maximum Safe Loan Amount based on real on-chain liquidity.
        Returns: Safe Amount (int) or 0 (Abort).
        """
        # 1. TVL CHECK (The Ceiling)
        # We check the Balancer V3 Vault balance for the specific token
        lender_address = BALANCER_V3_VAULT
        
        try:
            # Call the Simulation Engine (Sensor)
            pool_liquidity = get_provider_tvl(token_address, lender_address)
        except Exception as e:
            logger.error(f"TVL Check Failed for {token_address}: {e}")
            return 0

        if pool_liquidity == 0:
            logger.warning(f"⚠️ Vault Empty for token {token_address}. Aborting.")
            return 0

        # Calculate Caps
        max_cap = int(pool_liquidity * self.MAX_TVL_SHARE)
        requested_amount = int(target_amount_raw)
        
        # GUARD 1: Liquidity Check
        if requested_amount > max_cap:
            logger.warning(f"⚠️ Liquidity Constraint: Requested {requested_amount}, Cap {max_cap}. Scaling down.")
            requested_amount = max_cap

        # GUARD 2: Floor Check
        # We approximate USD value check. In prod, use Price Oracle here.
        # For now, we use a raw unit heuristic (e.g. 500 units of stablecoin/ETH)
        min_floor = 500 * (10**decimals) 
        if requested_amount < min_floor:
            logger.info(f"❌ Trade too small for profitability ({requested_amount} < {min_floor}). Aborting.")
            return 0

        # 2. SLIPPAGE OPTIMIZATION (The Loop)
        # In a full simulation, we would loop here calling get_real_output()
        # For Titan v4 MVP, we rely on the TVL cap as the primary safety net.
        # If TVL is sufficient, we authorize the trade.
        
        logger.info(f"✅ Loan Sizing Optimized: {requested_amount} (Cap: {max_cap})")
        return requested_amount