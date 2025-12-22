import time
import logging
import json
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
# Chains requiring PoA middleware due to Proof-of-Authority consensus
# Note: Celo uses BFT consensus but still requires PoA middleware for web3.py compatibility
POA_CHAINS = [137, 56, 250, 42220]  # Polygon, BSC, Fantom, Celo

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
        
        # 3. Communication (File-based signals)
        from pathlib import Path
        from core.config import SIGNALS_OUTGOING
        self.signals_dir = SIGNALS_OUTGOING
        logger.info(f"Signal output directory: {self.signals_dir}")
        
        # 4. Wallet Configuration
        import os
        self.wallet_address = os.getenv('EXECUTOR_ADDRESS', '0x0000000000000000000000000000000000000000')
        
        # Validate wallet address is configured
        if self.wallet_address == '0x0000000000000000000000000000000000000000' or \
           'YOUR' in self.wallet_address.upper():
            logger.warning("⚠️ EXECUTOR_ADDRESS not configured in .env - using placeholder for PAPER mode")
            # Use a valid Ethereum address for API calls (Vitalik's address as placeholder)
            self.wallet_address = "0xd8dA6BF26964aF9D7eEd9e03E53415D37aA96045"
        
        # 5. State
        self.node_indices = {} 
        self.executor = ThreadPoolExecutor(max_workers=20)
        
        # 5. Safety Limits
        self.MAX_GAS_PRICE_GWEI = Decimal("200.0")  # Maximum gas price ceiling
        self.MIN_PROFIT_THRESHOLD_USD = Decimal("1.0")  # Minimum $1 profit to execute
        self.MAX_SLIPPAGE_BPS = 100  # Maximum 1% slippage allowed
        self.consecutive_failures = 0
        self.MAX_CONSECUTIVE_FAILURES = 10  # Circuit breaker threshold
        
    def _cleanup_old_signals(self):
        """Clean up old signal files (keep last 100)"""
        try:
            signal_files = sorted([f for f in os.listdir(self.signals_dir) if f.endswith('.json')])
            if len(signal_files) > 100:
                for old_file in signal_files[:-100]:
                    os.remove(os.path.join(self.signals_dir, old_file))
        except Exception as e:
            logger.warning(f"Signal cleanup failed: {e}")

    def initialize(self):
        logger.info("🧠 Booting Apex-Omega Titan Brain...")
        
        # A. Load Assets - Dynamic token loading from 1inch API (100+ tokens per chain)
        from core.token_loader import TokenLoader
        
        target_chains = [1, 137, 42161, 10, 8453, 56, 43114]  # Major chains with good liquidity
        self.inventory = {}
        
        for chain_id in target_chains:
            logger.info(f"📥 Loading tokens for chain {chain_id}...")
            # Get 100+ tokens dynamically from 1inch
            tokens_list = TokenLoader.get_tokens(chain_id)
            
            if tokens_list:
                # Convert to dict format {symbol: {address, decimals}}
                self.inventory[chain_id] = {}
                for token in tokens_list[:100]:  # Top 100 by liquidity
                    symbol = token['symbol']
                    self.inventory[chain_id][symbol] = {
                        'address': token['address'],
                        'decimals': token['decimals']
                    }
                logger.info(f"   ✅ Loaded {len(self.inventory[chain_id])} tokens for chain {chain_id}")
            else:
                # Fallback to static registry
                logger.warning(f"   ⚠️ API failed, using static registry for chain {chain_id}")
                static_tokens = TokenDiscovery.fetch_all_chains([chain_id])
                self.inventory.update(static_tokens)
        
        # B. Initialize Web3 with timeout protection
        for cid, config in CHAINS.items():
            if config.get('rpc'):
                try:
                    # Add request timeout to prevent hanging
                    w3 = Web3(Web3.HTTPProvider(
                        config['rpc'],
                        request_kwargs={'timeout': 30}  # 30 second timeout for RPC calls
                    ))
                    # PoA middleware removed - web3.py v7+ handles PoA chains automatically
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
        """Get gas price with Alchemy fallback and safety ceiling"""
        import os
        
        # Alchemy RPC endpoints for major chains
        alchemy_map = {
            1: os.getenv('ALCHEMY_RPC_ETH'),
            137: os.getenv('ALCHEMY_RPC_POLY'),
            42161: os.getenv('ALCHEMY_RPC_ARB'),
            10: os.getenv('ALCHEMY_RPC_OPT'),
            8453: os.getenv('ALCHEMY_RPC_BASE')
        }
        
        # Always use Alchemy for supported chains to avoid rate limits
        if chain_id in alchemy_map and alchemy_map[chain_id]:
            try:
                w3 = Web3(Web3.HTTPProvider(alchemy_map[chain_id], request_kwargs={'timeout': 5}))
                wei_price = w3.eth.gas_price
                gwei_price = w3.from_wei(wei_price, 'gwei')
                
                if gwei_price > float(self.MAX_GAS_PRICE_GWEI):
                    logger.warning(f"⚠️ Gas price {gwei_price} exceeds max {self.MAX_GAS_PRICE_GWEI} on chain {chain_id}")
                    return float(self.MAX_GAS_PRICE_GWEI)
                    
                return gwei_price
            except Exception as e:
                logger.debug(f"Alchemy gas fetch failed for chain {chain_id}: {e}")
        
        # Fallback to configured RPC
        try:
            if chain_id in self.web3_connections:
                w3 = self.web3_connections[chain_id]
                wei_price = w3.eth.gas_price
                gwei_price = w3.from_wei(wei_price, 'gwei')
                
                if gwei_price > float(self.MAX_GAS_PRICE_GWEI):
                    logger.warning(f"⚠️ Gas price {gwei_price} exceeds max {self.MAX_GAS_PRICE_GWEI} on chain {chain_id}")
                    return float(self.MAX_GAS_PRICE_GWEI)
                    
                return gwei_price
        except Exception as e:
            logger.debug(f"Gas price fetch failed for chain {chain_id}: {e}")
        
        # Silently return 0 if all RPCs fail (rate limited)
        return 0.0

    def _find_opportunities(self):
        """
        Find INTRA-CHAIN arbitrage opportunities with FULL market coverage
        Scans 100+ tokens across multiple DEX combinations
        """
        opportunities = []
        
        # Target chains with deep liquidity
        target_chains = [1, 137, 42161, 10, 8453, 56, 43114]
        
        # DEX route variations per chain
        dex_routes = {
            1: [  # Ethereum - most liquid
                ('UNIV3', 'SUSHI'),
                ('UNIV3', 'UNIV2'),
                ('SUSHI', 'UNIV2'),
            ],
            137: [  # Polygon
                ('UNIV3', 'QUICKSWAP'),
                ('UNIV3', 'SUSHI'),
                ('QUICKSWAP', 'SUSHI'),
            ],
            42161: [  # Arbitrum
                ('UNIV3', 'SUSHI'),
                ('UNIV3', 'CAMELOT'),
                ('SUSHI', 'CAMELOT'),
            ],
            10: [  # Optimism
                ('UNIV3', 'SUSHI'),
            ],
            8453: [  # Base
                ('UNIV3', 'SUSHI'),
            ],
            56: [  # BSC
                ('PANCAKE', 'SUSHI'),
            ],
            43114: [  # Avalanche
                ('TRADERJOE', 'SUSHI'),
            ]
        }
        
        # Tiered token scanning strategy
        # Tier 1: High-priority stablecoins and major assets (scan every cycle)
        tier1_tokens = ['USDC', 'USDT', 'DAI', 'WETH', 'WBTC', 'ETH']
        
        # Tier 2: Popular DeFi tokens (scan every 2nd cycle)
        tier2_tokens = ['UNI', 'LINK', 'AAVE', 'CRV', 'MATIC', 'AVAX', 'BNB', 'SNX', 'MKR', 'COMP']
        
        # Tier 3: All other tokens (scan every 5th cycle)
        scan_counter = getattr(self, '_scan_counter', 0)
        self._scan_counter = scan_counter + 1
        
        for chain_id in target_chains:
            if chain_id not in self.inventory:
                continue
            
            tokens = self.inventory[chain_id]
            routes = dex_routes.get(chain_id, [('UNIV3', 'SUSHI')])
            
            # Build token list based on tier priority
            tokens_to_scan = []
            
            # Always scan Tier 1
            for token_sym in tier1_tokens:
                if token_sym in tokens:
                    tokens_to_scan.append(token_sym)
            
            # Scan Tier 2 every 2nd cycle
            if scan_counter % 2 == 0:
                for token_sym in tier2_tokens:
                    if token_sym in tokens and token_sym not in tokens_to_scan:
                        tokens_to_scan.append(token_sym)
            
            # Scan Tier 3 every 5th cycle (random sample of 20 tokens)
            if scan_counter % 5 == 0:
                import random
                tier3_tokens = [sym for sym in tokens.keys() 
                               if sym not in tier1_tokens and sym not in tier2_tokens]
                if tier3_tokens:
                    sampled_tokens = random.sample(tier3_tokens, min(20, len(tier3_tokens)))
                    tokens_to_scan.extend(sampled_tokens)
            
            # Generate opportunities for selected tokens
            for token_sym in tokens_to_scan:
                token_data = tokens[token_sym]
                
                # Create opportunity for EACH DEX route combination
                for dex1, dex2 in routes:
                    opportunities.append({
                        "src_chain": chain_id,
                        "dst_chain": chain_id,
                        "token": token_sym,
                        "token_addr_src": token_data['address'],
                        "token_addr_dst": token_data['address'],
                        "decimals": token_data['decimals'],
                        "route": (dex1, dex2),  # Track which DEX pair
                        "route_name": f"{dex1}→{dex2}"
                    })
        
        return opportunities

    def _evaluate_and_signal(self, opp, chain_gas_map):
        """
        Evaluate INTRA-CHAIN arbitrage with specific DEX route
        Tests multiple trade sizes as per README ($1.50-$10 profit target)
        """
        try:
            src_chain = opp['src_chain']
            dst_chain = opp['dst_chain']
            token_sym = opp['token']
            route_name = opp.get('route_name', 'UNIV3→SUSHI')
            dex1, dex2 = opp.get('route', ('UNIV3', 'SUSHI'))
            
            logger.info(f"🔎 {token_sym} Chain{src_chain} {route_name}")
            
            token_addr = opp['token_addr_src']
            decimals = opp['decimals']
            
            # 1. TEST MULTIPLE TRADE SIZES (README: optimize for $1.50-$10 profit)
            trade_sizes_usd = [500, 1000, 2000, 5000]  # Test various depths
            commander = TitanCommander(src_chain)
            
            # Find best profitable size
            for target_trade_usd in trade_sizes_usd:
                target_raw = target_trade_usd * (10**decimals)
                safe_amount = commander.optimize_loan_size(token_addr, target_raw, decimals)
                
                if safe_amount == 0:
                    continue  # Try next size
                
                # 2. SIMULATE DEX SWAPS with specific route
                try:
                    w3 = self.web3_connections.get(src_chain)
                    if not w3:
                        logger.info(f"❌ {token_sym}: No Web3 for chain {src_chain}")
                        return False
                    
                    pricer = DexPricer(w3, src_chain)
                    weth_addr = self.inventory[src_chain].get('WETH', {}).get('address')
                    
                    if not weth_addr:
                        logger.info(f"❌ {token_sym}: No WETH on chain {src_chain}")
                        return False
                    
                    # STEP 1: Token → WETH using DEX1
                    if dex1 == 'UNIV3':
                        step1_out = pricer.get_univ3_price(token_addr, weth_addr, safe_amount, fee=500)
                    else:
                        step1_out = pricer.get_univ2_price(dex1, token_addr, weth_addr, safe_amount)
                    
                    if step1_out == 0:
                        continue  # Try next size
                    
                    # STEP 2: WETH → Token using DEX2
                    step2_out = pricer.get_univ2_price(dex2, weth_addr, token_addr, step1_out)
                    
                    if step2_out == 0:
                        continue  # Try next size
                    
                    # Check profitability
                    if step2_out <= safe_amount:
                        continue  # Try next size
                    
                    # Calculate profit
                    revenue_usd = Decimal(step2_out) / Decimal(10**decimals)
                    cost_usd = Decimal(safe_amount) / Decimal(10**decimals)
                    
                    gas_price_gwei = chain_gas_map.get(src_chain, 0)
                    if gas_price_gwei == 0:
                        continue
                    
                    eth_price = Decimal("2000")
                    gas_cost_usd = Decimal(str(gas_price_gwei)) * Decimal("300000") * eth_price / Decimal("1e9")
                    
                    result = self.profit_engine.calculate_enhanced_profit(
                        amount=cost_usd,
                        amount_out=revenue_usd,
                        bridge_fee_usd=0,
                        gas_cost_usd=gas_cost_usd
                    )
                    
                    if result['is_profitable'] and result['net_profit'] >= self.MIN_PROFIT_THRESHOLD_USD:
                        # Found profitable trade at this size!
                        logger.info(f"💰 PROFIT: {token_sym} ${target_trade_usd} {route_name} = ${result['net_profit']:.2f}")
                        
                        # Continue with signal generation...
                        break  # Use this size
                        
                except Exception as e:
                    logger.debug(f"Size ${target_trade_usd} failed: {e}")
                    continue
            
            else:
                # No profitable size found after trying all sizes
                return False
            
            # If we get here, we found profitable trade with variables: safe_amount, step1_out, step2_out, result
            # 4. PAYLOAD CONSTRUCTION - Using specific DEX route
            try:
                chain_conf = CHAINS.get(src_chain)
                if not chain_conf:
                    return False
                
                # Get router addresses based on route
                from core.config import DEX_ROUTERS
                
                # Get router for DEX1
                if dex1 == 'UNIV3':
                    router1 = chain_conf.get('uniswap_router', ZERO_ADDRESS)
                    protocol1 = 1  # UniV3
                    extra1 = "0x" + encode(['uint24'], [500]).hex()  # 0.05% fee
                else:
                    router1 = DEX_ROUTERS.get(src_chain, {}).get(dex1, ZERO_ADDRESS)
                    protocol1 = 0  # UniV2-style
                    extra1 = "0x"
                
                # Get router for DEX2
                router2 = DEX_ROUTERS.get(src_chain, {}).get(dex2, ZERO_ADDRESS)
                protocol2 = 0  # All second hops are V2-style
                extra2 = "0x"
                
                if is_zero_address(router1) or is_zero_address(router2):
                    return False
                
                protocols = [protocol1, protocol2]
                routers = [router1, router2]
                path = [weth_addr, token_addr]  # Outputs of each step
                extras = [extra1, extra2]
                
            except Exception as e:
                logger.error(f"Payload construction failed: {e}")
                return False

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

            # Signal generated successfully with detailed info
            logger.info(f"⚡ SIGNAL GENERATED: {token_sym} on Chain {src_chain}")
            logger.info(f"   💰 Profit: ${result['net_profit']:.2f} | Fees: ${result['total_fees']:.2f}")
            logger.info(f"   🔄 Route: {' -> '.join(protocols)}")
            logger.info(f"   ⛽ Gas: {chain_gas_map.get(src_chain, 0):.1f} Gwei")
            self.consecutive_failures = 0
            
            # Write signal to file for bot.js consumption
            self._write_signal_to_file(signal)
            
            return True  # Signal generated successfully
                
        except Exception as e:
            logger.error(f"Unexpected error in _evaluate_and_signal for {opp.get('token', 'unknown')}: {e}")
            self.consecutive_failures += 1
            return False

    def _write_signal_to_file(self, signal):
        """Write signal to JSON file for bot.js consumption"""
        try:
            timestamp = int(time.time() * 1000)
            filename = f"signal_{timestamp}_{signal['token_symbol']}.json"
            filepath = os.path.join(self.signals_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(signal, f, indent=2)
            
            logger.info(f"📄 Signal written to: {filename}")
            
            # Cleanup old signals periodically
            if timestamp % 60000 < 1000:  # Roughly every minute
                self._cleanup_old_signals()
                
        except Exception as e:
            logger.error(f"Failed to write signal file: {e}")

    def scan_loop(self):
        logger.info("🚀 Titan Brain: Engaging Hyper-Parallel Scan Loop...")
        
        # Log initial coverage stats
        total_tokens = sum(len(tokens) for tokens in self.inventory.values())
        total_chains = len(self.inventory)
        logger.info(f"📊 Coverage: {total_tokens} tokens across {total_chains} chains")
        for chain_id, tokens in self.inventory.items():
            chain_name = CHAINS.get(chain_id, {}).get('name', f'Chain {chain_id}')
            logger.info(f"   • {chain_name}: {len(tokens)} tokens")
        
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
                    signals_generated = 0
                    for f in as_completed(scan_futures, timeout=30):
                        try:
                            result = f.result()  # This will raise any exceptions from the worker
                            completed += 1
                            if result:  # If signal was generated
                                signals_generated += 1
                        except Exception as e:
                            logger.error(f"Worker evaluation error: {e}")
                            
                    logger.info(f"📊 Cycle complete: {completed}/{len(candidates)} evaluated, {signals_generated} signals generated")
                    
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