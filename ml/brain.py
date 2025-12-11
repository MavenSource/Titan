import time
import logging
import json
import redis
import rustworkx as rx
import pandas as pd
from web3 import Web3
from datetime import datetime
from eth_abi import encode
from decimal import Decimal, getcontext
from concurrent.futures import ThreadPoolExecutor, as_completed

# Core Infrastructure
from core.config import CHAINS, BALANCER_V3_VAULT, DEX_ROUTERS
from core.token_discovery import TokenDiscovery
from routing.bridge_manager import BridgeManager
from core.titan_commander_core import TitanCommander

# The Cortex (AI Layer)
from ml.cortex.forecaster import MarketForecaster
from ml.cortex.rl_optimizer import QLearningAgent
from ml.cortex.feature_store import FeatureStore
from ml.dex_pricer import DexPricer

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [BRAIN] %(message)s')
logger = logging.getLogger("TitanBrain")

# Precision for financial math
getcontext().prec = 28

# Constants
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"

def is_zero_address(address: str) -> bool:
    """
    Check if an address is the zero address (uninitialized/unavailable).
    
    Args:
        address: Ethereum address to check
        
    Returns:
        bool: True if address is zero address, False otherwise
    """
    if not address:
        return True
    return address.lower() == ZERO_ADDRESS.lower()

class ProfitEngine:
    """
    Implements the Titan Master Profit Equation.
    Π_net = V_loan × [(P_A × (1 - S_A)) - (P_B × (1 + S_B))] - F_flat - (V_loan × F_rate)
    """
    def __init__(self, default_flash_fee=Decimal("0.0")):
        self.flash_fee = default_flash_fee # Balancer V3 is 0%

    def calculate_enhanced_profit(self, amount, amount_out, bridge_fee_usd, gas_cost_usd):
        """
        Calculates Net Profit based on REAL simulated output.
        """
        # 1. Gross Revenue (What we actually get out)
        gross_revenue_usd = amount_out # Assuming normalized to USD for this calculation context

        # 2. Cost Basis (What we borrowed + fees)
        loan_cost_usd = amount
        flash_fee_cost = amount * self.flash_fee
        
        total_operational_costs = bridge_fee_usd + gas_cost_usd + flash_fee_cost

        # 3. Net Profit
        net_profit = gross_revenue_usd - loan_cost_usd - total_operational_costs
        
        return {
            "net_profit": net_profit,
            "gross_spread": gross_revenue_usd - loan_cost_usd,
            "total_fees": total_operational_costs,
            "is_profitable": net_profit > 0
        }

class OmniBrain:
    def __init__(self):
        # 1. Infrastructure
        self.graph = rx.PyDiGraph()
        self.bridge = BridgeManager()
        self.profit_engine = ProfitEngine()
        self.inventory = {} 
        self.web3_connections = {}
        
        # 2. AI Modules
        self.forecaster = MarketForecaster()
        self.optimizer = QLearningAgent()
        self.memory = FeatureStore()
        
        # 3. Communication with retry logic
        self.redis_client = None
        self._init_redis_connection()
        
        # 4. State
        self.node_indices = {} 
        self.executor = ThreadPoolExecutor(max_workers=20)
        
        # 5. Safety Limits
        self.MAX_GAS_PRICE_GWEI = Decimal("200.0")  # Maximum gas price ceiling
        self.MIN_PROFIT_THRESHOLD_USD = Decimal("5.0")  # Minimum profit to execute
        self.MAX_SLIPPAGE_BPS = 100  # Maximum 1% slippage allowed
        self.consecutive_failures = 0
        self.MAX_CONSECUTIVE_FAILURES = 10  # Circuit breaker threshold
        
    def _init_redis_connection(self):
        """Initialize Redis connection with retry logic"""
        max_retries = 5
        for attempt in range(max_retries):
            try:
                self.redis_client = redis.Redis(
                    host='localhost', 
                    port=6379, 
                    db=0,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                    health_check_interval=30
                )
                self.redis_client.ping()
                logger.info("✅ Redis connection established")
                return
            except Exception as e:
                logger.warning(f"Redis connection attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    # Exponential backoff capped at 10 seconds
                    time.sleep(min(2 ** attempt, 10))
        logger.error("❌ Failed to establish Redis connection. Operating in degraded mode.")
        self.redis_client = None

    def initialize(self):
        logger.info("🧠 Booting Apex-Omega Titan Brain...")
        
        # A. Load Assets (10 Chains)
        target_chains = list(CHAINS.keys())
        self.inventory = TokenDiscovery.fetch_all_chains(target_chains)
        
        # B. Initialize Web3 with timeout protection
        for cid, config in CHAINS.items():
            if config.get('rpc'):
                try:
                    # Add request timeout to prevent hanging
                    from web3.middleware import geth_poa_middleware
                    w3 = Web3(Web3.HTTPProvider(
                        config['rpc'],
                        request_kwargs={'timeout': 30}  # 30 second timeout for RPC calls
                    ))
                    # Add PoA middleware for chains that need it (Polygon, BSC, etc.)
                    if cid in [137, 56, 250, 42220]:  # PoA chains
                        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
                    self.web3_connections[cid] = w3
                    logger.debug(f"Web3 connection established for chain {cid}")
                except Exception as e:
                    logger.warning(f"Failed to initialize Web3 for chain {cid}: {e}")

        # C. Build Graph
        self._build_graph_nodes()
        self._build_bridge_edges()
        
        logger.info(f"✅ System Online. Tracking {self.graph.num_nodes()} nodes.")

    def _build_graph_nodes(self):
        logger.info("🕸️  Constructing Hyper-Graph Nodes...")
        for chain_id, tokens in self.inventory.items():
            for symbol, data in tokens.items():
                node_key = (chain_id, symbol)
                if node_key not in self.node_indices:
                    idx = self.graph.add_node({
                        "chain": chain_id,
                        "symbol": symbol,
                        "address": data['address'],
                        "decimals": data['decimals']
                    })
                    self.node_indices[node_key] = idx

    def _build_bridge_edges(self):
        logger.info("🌉 Building Virtual Bridge Edges...")
        for symbol in TokenDiscovery.BRIDGE_ASSETS:
            chains_with_asset = [cid for cid in self.inventory if symbol in self.inventory[cid]]
            for i in range(len(chains_with_asset)):
                for j in range(i + 1, len(chains_with_asset)):
                    chain_a, chain_b = chains_with_asset[i], chains_with_asset[j]
                    u, v = self.node_indices[(chain_a, symbol)], self.node_indices[(chain_b, symbol)]
                    self.graph.add_edge(u, v, {"type": "bridge", "weight": 0.0})
                    self.graph.add_edge(v, u, {"type": "bridge", "weight": 0.0})

    def _get_gas_price(self, chain_id):
        """Get gas price with safety ceiling and timeout protection"""
        try:
            if chain_id in self.web3_connections:
                w3 = self.web3_connections[chain_id]
                # Use block_identifier to ensure we get latest data with timeout
                wei_price = w3.eth.gas_price
                gwei_price = w3.from_wei(wei_price, 'gwei')
                
                # Apply safety ceiling
                if gwei_price > float(self.MAX_GAS_PRICE_GWEI):
                    logger.warning(f"⚠️ Gas price {gwei_price} exceeds maximum {self.MAX_GAS_PRICE_GWEI} on chain {chain_id}")
                    return float(self.MAX_GAS_PRICE_GWEI)
                    
                return gwei_price
        except TimeoutError:
            logger.error(f"Timeout fetching gas price for chain {chain_id}")
            return 0.0
        except Exception as e:
            logger.error(f"Gas price fetch failed for chain {chain_id}: {e}")
            return 0.0

    def _find_opportunities(self):
        opportunities = []
        for u_idx, v_idx, data in self.graph.edge_index_map().values():
            if data.get("type") == "bridge":
                src_node = self.graph.get_node_data(u_idx)
                dst_node = self.graph.get_node_data(v_idx)
                if src_node['chain'] != dst_node['chain']:
                    opportunities.append({
                        "src_chain": src_node['chain'],
                        "dst_chain": dst_node['chain'],
                        "token": src_node['symbol'],
                        "token_addr_src": src_node['address'],
                        "token_addr_dst": dst_node['address'],
                        "decimals": src_node['decimals']
                    })
        return opportunities

    def _evaluate_and_signal(self, opp, chain_gas_map):
        """
        FIXED VERSION: Route encoding now matches simulation
        """
        try:
            src_chain = opp['src_chain']
            dst_chain = opp['dst_chain']
            token_sym = opp['token']
            token_addr = opp['token_addr_src']
            decimals = opp['decimals']
            
            # 1. SAFETY CHECK (Liquidity Guard)
            commander = TitanCommander(src_chain)
            target_trade_usd = 10000
            target_raw = target_trade_usd * (10**decimals)
            
            safe_amount = commander.optimize_loan_size(token_addr, target_raw, decimals)
            if safe_amount == 0:
                logger.debug(f"Insufficient liquidity for {token_sym} on chain {src_chain}")
                return

            # 2. GET BRIDGE QUOTE (Cost 1) with validation
            try:
                quote = self.bridge.get_route(
                    src_chain, dst_chain, token_addr, str(safe_amount), 
                    "0x0000000000000000000000000000000000000000"
                )
                if not quote:
                    logger.debug(f"No bridge route available for {token_sym}: {src_chain} -> {dst_chain}")
                    return
                    
                if 'fee_usd' not in quote or 'est_output' not in quote:
                    logger.warning(f"Invalid bridge quote structure for {token_sym}")
                    return
                    
                fee_bridge_usd = Decimal(str(quote.get('fee_usd', 0)))
                
                max_bridge_fee = Decimal(target_trade_usd) * Decimal("0.05")
                if fee_bridge_usd > max_bridge_fee:
                    logger.warning(f"Bridge fee too high: ${fee_bridge_usd} for {token_sym}")
                    return
                    
            except Exception as e:
                logger.error(f"Bridge quote failed for {token_sym}: {e}")
                return

            # 3. GET REAL DEX PRICE (Revenue Simulation) - FIXED VERSION
            try:
                w3 = self.web3_connections.get(src_chain)
                if not w3:
                    logger.error(f"No Web3 connection for chain {src_chain}")
                    return
                    
                pricer = DexPricer(w3, src_chain)
                
                # Find WETH address dynamically
                weth_addr = self.inventory[src_chain].get('WETH', {}).get('address')
                if not weth_addr:
                    logger.debug(f"WETH not available on chain {src_chain}")
                    return

                # === SIMULATION STEP 1: Token → WETH (Uniswap) ===
                step1_out = pricer.get_univ3_price(
                    token_in=token_addr,      # Start with flash loan token
                    token_out=weth_addr,      # Convert to WETH
                    amount=safe_amount,
                    fee=500
                )
                
                if step1_out == 0:
                    logger.debug(f"Step 1 simulation failed for {token_sym} → WETH")
                    return
                
                logger.debug(f"Step 1: {safe_amount} {token_sym} → {step1_out} WETH")
                
                # === SIMULATION STEP 2: WETH → Token (Curve) ===
                # Check if Curve router exists
                curve_router = CHAINS[src_chain].get('curve_router')
                if not curve_router or curve_router == "0x0000000000000000000000000000000000000000":
                    logger.debug(f"Curve not available on chain {src_chain}")
                    return
                
                # FIX #2: Use new method signature with token addresses
                step2_out = pricer.get_curve_price(
                    pool_address=curve_router,
                    token_in=weth_addr,       # We have WETH from step 1
                    token_out=token_addr,     # Convert back to original token
                    amount=step1_out
                )
                
                if step2_out == 0:
                    logger.debug(f"Step 2 simulation failed for WETH → {token_sym}")
                    return
                
                logger.debug(f"Step 2: {step1_out} WETH → {step2_out} {token_sym}")
                
                # Verify profitability
                if step2_out <= safe_amount:
                    logger.debug(f"Not profitable: started {safe_amount}, ended {step2_out}")
                    return
                
                # Convert to USD for profit calculation
                revenue_usd = Decimal(step2_out) / Decimal(10**decimals)
                cost_usd = Decimal(safe_amount) / Decimal(10**decimals)
                
                # Calculate gas cost
                gas_price_gwei = chain_gas_map.get(src_chain, 0)
                gas_cost_usd = Decimal(str(gas_price_gwei)) * Decimal("500000") * Decimal("2000") / Decimal("1e9")
                
            except Exception as e:
                logger.error(f"DEX price simulation failed for {token_sym}: {e}")
                return

            # 4. PROFIT CALCULATION
            try:
                result = self.profit_engine.calculate_enhanced_profit(
                    amount=cost_usd,
                    amount_out=revenue_usd,
                    bridge_fee_usd=0,  # Intra-chain
                    gas_cost_usd=gas_cost_usd
                )
                
                if not result['is_profitable']:
                    logger.debug(f"Not profitable: {token_sym} (Net: ${result['net_profit']:.2f})")
                    return
                
                if result['net_profit'] < self.MIN_PROFIT_THRESHOLD_USD:
                    logger.debug(f"Profit below threshold: {token_sym} (${result['net_profit']:.2f})")
                    return

                logger.info(f"💰 PROFIT FOUND: {token_sym} | Net: ${result['net_profit']:.2f}")
                
            except Exception as e:
                logger.error(f"Profit calculation failed for {token_sym}: {e}")
                return

            # 5. PAYLOAD CONSTRUCTION - FIXED VERSION
            try:
                chain_conf = CHAINS.get(src_chain)
                if not chain_conf:
                    logger.error(f"Chain config not found for {src_chain}")
                    return
                
                # Validate routers are not zero addresses
                uni_router = chain_conf.get('uniswap_router', ZERO_ADDRESS)
                curve_router = chain_conf.get('curve_router', ZERO_ADDRESS)
                
                if is_zero_address(uni_router):
                    logger.warning(f"Uniswap router not configured for chain {src_chain}, skipping opportunity")
                    return
                if is_zero_address(curve_router):
                    logger.warning(f"Curve router not configured for chain {src_chain}, skipping opportunity")
                    return
                
                # === FIX #2: CORRECT ROUTE ENCODING ===
                
                # Get Curve indices using new method
                curve_indices = pricer.get_curve_indices(
                    pool_address=curve_router,
                    token_in=weth_addr,
                    token_out=token_addr
                )
                
                if curve_indices[0] is None:
                    logger.error(f"Cannot resolve Curve indices for route")
                    return
                
                # Protocol IDs
                protocols = [
                    1,  # Uniswap V3
                    2   # Curve
                ]
                
                # Router addresses
                routers = [
                    uni_router,
                    curve_router
                ]
                
                # === CRITICAL FIX: Path represents OUTPUT of each step ===
                # Step 1: Token → WETH, output is WETH
                # Step 2: WETH → Token, output is Token
                path = [
                    weth_addr,    # Output of protocol[0]
                    token_addr    # Output of protocol[1]
                ]
                
                # Protocol-specific parameters
                extras = [
                    # UniV3: fee tier (500 = 0.05%)
                    "0x" + encode(['uint24'], [500]).hex(),
                    
                    # Curve: indices (i=WETH, j=Token)
                    "0x" + encode(['int128', 'int128'], curve_indices).hex()
                ]
                
                # Log the complete route for verification
                logger.info(f"📋 Route constructed:")
                logger.info(f"   Flash loan: {safe_amount} {token_sym}")
                logger.info(f"   Step 1: {token_sym} → WETH via UniV3 (fee: 500)")
                logger.info(f"   Step 2: WETH → {token_sym} via Curve (i={curve_indices[0]}, j={curve_indices[1]})")
                logger.info(f"   Expected profit: ${result['net_profit']:.2f}")
                
            except Exception as e:
                logger.error(f"Payload construction failed for {token_sym}: {e}")
                return

            # 6. AI TUNING
            try:
                exec_params = self.optimizer.recommend_parameters(src_chain, "MEDIUM")
                
                # Validate AI parameters
                if exec_params.get('slippage', 0) > self.MAX_SLIPPAGE_BPS:
                    logger.warning(f"AI slippage {exec_params['slippage']} exceeds max {self.MAX_SLIPPAGE_BPS}, capping")
                    exec_params['slippage'] = self.MAX_SLIPPAGE_BPS
                
                max_priority = float(self.MAX_GAS_PRICE_GWEI) / 2
                if exec_params.get('priority', 0) > max_priority:
                    exec_params['priority'] = int(max_priority)
                    
            except Exception as e:
                logger.error(f"AI parameter tuning failed: {e}")
                exec_params = {"slippage": 50, "priority": 30}

            # 7. BROADCAST
            signal = {
                "type": "INTRA_CHAIN",
                "chainId": src_chain,
                "token": token_addr,
                "amount": str(safe_amount),
                "protocols": protocols,
                "routers": routers,
                "path": path,
                "extras": extras,
                "ai_params": exec_params,
                "metrics": {
                    "profit_usd": float(result['net_profit']),
                    "fees_usd": float(result['total_fees']),
                    "gas_price_gwei": float(chain_gas_map.get(src_chain, 0)),
                    "step1_output": step1_out,
                    "step2_output": step2_out
                },
                "timestamp": datetime.now().isoformat()
            }

            try:
                if self.redis_client:
                    self.redis_client.publish("trade_signals", json.dumps(signal))
                    logger.info(f"⚡ SIGNAL BROADCASTED for {token_sym}")
                    self.consecutive_failures = 0
            except redis.ConnectionError as e:
                logger.error(f"Redis connection error: {e}")
                self.consecutive_failures += 1
                self.redis_client = None
            except Exception as e:
                logger.error(f"Signal broadcast error: {e}")
                self.consecutive_failures += 1
                
        except Exception as e:
            logger.error(f"Unexpected error in _evaluate_and_signal for {opp.get('token', 'unknown')}: {e}")
            self.consecutive_failures += 1

    def scan_loop(self):
        logger.info("🚀 Titan Brain: Engaging Hyper-Parallel Scan Loop...")
        
        while True:
            try:
                # Circuit breaker check
                if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    logger.error(f"🛑 CIRCUIT BREAKER TRIGGERED: {self.consecutive_failures} consecutive failures")
                    logger.info("⏸️ Pausing for 60 seconds before retry...")
                    time.sleep(60)
                    self.consecutive_failures = 0  # Reset after cooldown
                    continue
                
                # 1. GAS CHECK with error handling
                try:
                    active_chains = list(self.web3_connections.keys())
                    gas_futures = {self.executor.submit(self._get_gas_price, cid): cid for cid in active_chains}
                    chain_gas_map = {}
                    
                    for f in as_completed(gas_futures, timeout=10):
                        try:
                            chain_id = gas_futures[f]
                            gas_price = f.result()
                            chain_gas_map[chain_id] = gas_price
                        except Exception as e:
                            logger.warning(f"Failed to get gas price for chain: {e}")
                            
                    if not chain_gas_map:
                        logger.warning("No gas prices available, waiting before retry")
                        time.sleep(5)
                        continue
                        
                except Exception as e:
                    logger.error(f"Gas check failed: {e}")
                    time.sleep(5)
                    continue

                # 2. FORECAST GUARD with validation
                try:
                    poly_gas = chain_gas_map.get(137, 0.0)
                    if poly_gas > 0:
                        # Check if gas price is within acceptable range
                        if poly_gas > float(self.MAX_GAS_PRICE_GWEI):
                            logger.warning(f"⚠️ Polygon gas price {poly_gas} exceeds maximum, waiting...")
                            time.sleep(10)
                            continue
                            
                        self.forecaster.ingest_gas(poly_gas)
                        if self.forecaster.should_wait():
                            logger.info("⏳ AI HOLD: Gas trend unfavorable.")
                            time.sleep(2)
                            continue
                except Exception as e:
                    logger.warning(f"Gas forecast check failed: {e}")
                    # Continue anyway as this is not critical
                
                # Reconnect Redis if needed (non-blocking)
                if self.redis_client is None:
                    logger.info("Attempting to reconnect Redis...")
                    self._init_redis_connection()

                # 3. FIND PATHS with error handling
                try:
                    candidates = self._find_opportunities()
                    if not candidates:
                        logger.debug("No opportunities found in this cycle")
                        time.sleep(5)
                        continue
                    
                    logger.info(f"🔍 Found {len(candidates)} potential opportunities")
                except Exception as e:
                    logger.error(f"Opportunity discovery failed: {e}")
                    time.sleep(5)
                    continue

                # 4. PARALLEL EVALUATION with error handling
                try:
                    scan_futures = [
                        self.executor.submit(self._evaluate_and_signal, opp, chain_gas_map) 
                        for opp in candidates
                    ]
                    
                    completed = 0
                    for f in as_completed(scan_futures, timeout=30):
                        try:
                            f.result()  # This will raise any exceptions from the worker
                            completed += 1
                        except Exception as e:
                            logger.error(f"Worker evaluation error: {e}")
                            
                    logger.debug(f"Completed {completed}/{len(candidates)} evaluations")
                    
                except Exception as e:
                    logger.error(f"Parallel evaluation failed: {e}")

                # Sleep between cycles
                time.sleep(1)
                
            except KeyboardInterrupt:
                logger.info("🛑 Shutting down gracefully...")
                self.executor.shutdown(wait=True)
                break
            except Exception as e:
                logger.error(f"Unexpected error in scan loop: {e}")
                time.sleep(5)

if __name__ == "__main__":
    brain = OmniBrain()
    brain.initialize()
    brain.scan_loop()