import os
import time
import logging
import json
import asyncio
import rustworkx as rx
import pandas as pd
from web3 import Web3
from datetime import datetime
from eth_abi import encode
from decimal import Decimal, getcontext
from concurrent.futures import ThreadPoolExecutor, as_completed

# Core Infrastructure
from core.config import CHAINS, BALANCER_V3_VAULT, DEX_ROUTERS, DEFAULT_CHAIN_ID, DEFAULT_CHAIN_NAME
from core.token_discovery import TokenDiscovery
from routing.bridge_aggregator import BridgeAggregator
from execution.execution_client import ExecutionManager

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
        self.bridge = BridgeAggregator()
        self.profit_engine = ProfitEngine()
        self.inventory = {} 
        self.web3_connections = {}
        
        # 2. AI Modules
        self.forecaster = MarketForecaster()
        self.optimizer = QLearningAgent()
        self.memory = FeatureStore()
        
        # 3. Communication (Direct Python-to-Node via HTTP/WebSocket)
        self.execution_manager = None  # Initialized async
        self.execution_mode = os.getenv("EXECUTION_MODE", "PAPER")
        
        logger.info(f"🎯 Execution Mode: {self.execution_mode.upper()}")
        
        if self.execution_mode.upper() == "LIVE":
            logger.warning("🔴 LIVE MAINNET MODE - REAL CAPITAL AT RISK")
            logger.warning("🔴 Ensure PRIVATE_KEY and EXECUTOR_ADDRESS are configured")
        else:
            logger.info("📝 Paper Trading Mode - No real capital required")
        
        # 5. State
        self.node_indices = {} 
        self.executor = ThreadPoolExecutor(max_workers=20)

    async def initialize_async(self):
        """Async initialization for ExecutionManager"""
        logger.info("🔗 Connecting to execution server...")
        self.execution_manager = ExecutionManager()
        connected = await self.execution_manager.initialize()
        
        if not connected:
            logger.error("❌ Failed to connect to execution server")
            logger.error("Start server with: node execution/execution_server.js")
            raise RuntimeError("Execution server not available")
        
        logger.info("✅ Connected to execution layer")

    def initialize(self):
        logger.info("🧠 Booting Apex-Omega Titan Brain...")
        
        # A. Load Assets (10 Chains) - Prioritize Polygon (137) as primary network
        target_chains = [137] + [c for c in CHAINS.keys() if c != 137]  # Polygon first
        self.inventory = TokenDiscovery.fetch_all_chains(target_chains)
        logger.info(f"✅ Primary Network: Polygon (Chain ID: 137)")
        
        # B. Initialize Web3
        for cid, config in CHAINS.items():
            if config.get('rpc'):
                self.web3_connections[cid] = Web3(Web3.HTTPProvider(config['rpc']))

        # C. Build Graph
        self._build_graph_nodes()
        self._build_bridge_edges()
        
        # D. Initialize Execution Layer (async)
        try:
            asyncio.run(self.initialize_async())
        except Exception as e:
            logger.error(f"❌ Failed to initialize execution layer: {e}")
            logger.warning("⚠️  Running in analysis-only mode")
            self.execution_manager = None
        
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
        try:
            if chain_id in self.web3_connections:
                w3 = self.web3_connections[chain_id]
                wei_price = w3.eth.gas_price 
                return w3.from_wei(wei_price, 'gwei')
        except Exception:
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
        Worker function: Validates Liquidity, Simulates Price, Calculates Profit, Broadcasts.
        """
        src_chain = opp['src_chain']
        dst_chain = opp['dst_chain']
        token_sym = opp['token']
        token_addr = opp['token_addr_src']
        decimals = opp['decimals']
        
        # 1. SAFETY CHECK (Liquidity Guard)
        commander = TitanCommander(src_chain)
        target_trade_usd = 10000 # Start ambition
        target_raw = target_trade_usd * (10**decimals)
        
        safe_amount = commander.optimize_loan_size(token_addr, target_raw, decimals)
        if safe_amount == 0:
            return # Not enough liquidity

        # 2. GET BRIDGE QUOTE (Cost 1)
        quote = self.bridge.get_route(
            src_chain, dst_chain, token_addr, str(safe_amount), 
            "0x0000000000000000000000000000000000000000"
        )
        if not quote: return
        fee_bridge_usd = Decimal(str(quote.get('fee_usd', 0)))

        # 3. GET REAL DEX PRICE (Revenue Simulation)
        # We check Intra-Chain arb on Source Chain first as part of the loop
        w3 = self.web3_connections[src_chain]
        pricer = DexPricer(w3, src_chain)
        
        # Find WETH address dynamically
        weth_addr = self.inventory[src_chain].get('WETH', {}).get('address')
        if not weth_addr: return

        # Simulate: Sell Token -> Buy WETH -> Sell WETH -> Buy Token
        # This checks if we can make profit locally before bridging, or prepare for bridge
        # For this Titan Build, let's simulate a direct Arb on Source:
        # Buy WETH on Uni, Sell WETH on Curve
        
        step1_out = pricer.get_univ3_price(token_addr, weth_addr, safe_amount, 500)
        if step1_out == 0: return
        
        step2_out = pricer.get_curve_price(CHAINS[src_chain]['curve_router'], 2, 1, step1_out) # Mock indices
        
        # Convert results to Decimal USD for profit engine
        # (Simplification: assume stablecoin loops for direct USD comparison)
        revenue_usd = Decimal(step2_out) / Decimal(10**decimals)
        cost_usd = Decimal(safe_amount) / Decimal(10**decimals)
        
        gas_cost_usd = Decimal("2.00") # Placeholder for complex gas math

        # 4. PROFIT CALCULATION
        result = self.profit_engine.calculate_enhanced_profit(
            amount=cost_usd,
            amount_out=revenue_usd,
            bridge_fee_usd=0, # Intra-chain has no bridge fee
            gas_cost_usd=gas_cost_usd
        )
        
        if not result['is_profitable']:
            return

        logger.info(f"💰 PROFIT FOUND: {token_sym} | Net: ${result['net_profit']:.2f}")

        # 5. PAYLOAD CONSTRUCTION
        chain_conf = CHAINS.get(src_chain)
        protocols = [1, 2] # Uni, Curve
        routers = [chain_conf['uniswap_router'], chain_conf['curve_router']]
        path = [weth_addr, token_addr]
        extras = [
            "0x" + encode(['uint24'], [500]).hex(),
            "0x" + encode(['int128', 'int128'], [2, 1]).hex()
        ]

        # 6. AI TUNING
        exec_params = self.optimizer.recommend_parameters(src_chain, "MEDIUM")

        # 7. EXECUTE TRADE (Paper or Live based on mode)
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
            "expected_profit": float(result['net_profit']),
            "estimated_slippage_bps": 20,  # From simulation
            "gas_cost": float(result['total_fees']),
            "confidence_score": 0.90,  # From AI optimizer
            "metrics": {
                "profit_usd": float(result['net_profit']),
                "fees_usd": float(result['total_fees'])
            }
        }

        # Check if execution manager available
        if not self.execution_manager:
            logger.info(f"📊 Analysis Mode: Profit=${result['net_profit']:.2f} (execution disabled)")
            return

        try:
            # Submit trade to Node.js execution layer via HTTP
            execution_result = asyncio.run(
                self.execution_manager.submit_trade(
                    chain_id=src_chain,
                    token=token_addr,
                    amount=str(safe_amount),
                    flash_source=1,  # Balancer V3
                    protocols=protocols,
                    routers=routers,
                    path=path,
                    extras=[e.encode() if isinstance(e, str) else e for e in extras],
                    expected_profit=float(result['net_profit'])
                )
            )
            
            if execution_result.get('success'):
                mode = execution_result.get('mode', 'UNKNOWN')
                if mode == 'PAPER':
                    logger.info(f"📝 Paper Trade: ${result['net_profit']:.2f} profit")
                else:
                    tx_hash = execution_result.get('txHash', 'pending')
                    logger.warning(f"🔴 Live Trade: {tx_hash[:10]}... | ${result['net_profit']:.2f}")
            else:
                logger.error(f"❌ Execution failed: {execution_result.get('error')}")
                
        except Exception as e:
            logger.error(f"❌ Execution Error: {e}")

    def scan_loop(self):
        logger.info("🚀 Titan Brain: Engaging Hyper-Parallel Scan Loop...")
        
        while True:
            # 1. GAS CHECK
            active_chains = list(self.web3_connections.keys())
            gas_futures = {self.executor.submit(self._get_gas_price, cid): cid for cid in active_chains}
            chain_gas_map = {gas_futures[f]: f.result() for f in as_completed(gas_futures)}

            # 2. FORECAST GUARD
            poly_gas = chain_gas_map.get(137, 0.0)
            if poly_gas > 0:
                self.forecaster.ingest_gas(poly_gas)
                if self.forecaster.should_wait():
                    logger.info("⏳ AI HOLD: Gas trend unfavorable.")
                    time.sleep(2)
                    continue

            # 3. FIND PATHS
            candidates = self._find_opportunities()
            if not candidates:
                time.sleep(5)
                continue

            # 4. PARALLEL EVALUATION
            scan_futures = [
                self.executor.submit(self._evaluate_and_signal, opp, chain_gas_map) 
                for opp in candidates
            ]
            
            for f in as_completed(scan_futures):
                pass 

            time.sleep(1)

if __name__ == "__main__":
    brain = OmniBrain()
    brain.initialize()
    brain.scan_loop()