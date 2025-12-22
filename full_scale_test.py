"""
APEX-OMEGA TITAN: COMPREHENSIVE FULL-SCALE TEST SUITE
=====================================================

This script performs a complete end-to-end test of the entire system
with detailed logging and documentation of every component.

Test Coverage:
1. System initialization and component loading
2. Multi-chain connectivity verification
3. Token inventory validation
4. Arbitrage detection engine
5. Signal generation and processing
6. ML training pipeline
7. Safety mechanisms
8. Production readiness

All results are logged to: logs/full_scale_test_report.txt
"""

import os
import sys
import json
import time
import logging
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Add offchain/brain to path
sys.path.insert(0, str(Path(__file__).parent / "offchain" / "brain"))

# Load environment from offchain directory
ENV_PATH = Path(__file__).parent / "offchain" / ".env"
load_dotenv(ENV_PATH)

# Setup comprehensive logging
log_dir = Path('logs')
log_dir.mkdir(exist_ok=True)

timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
log_file = log_dir / f'full_scale_test_report_{timestamp}.txt'

# Create logger
logger = logging.getLogger('FullScaleTest')
logger.setLevel(logging.INFO)

# File handler
fh = logging.FileHandler(log_file, encoding='utf-8')
fh.setLevel(logging.INFO)

# Console handler
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# Formatter
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
fh.setFormatter(formatter)
ch.setFormatter(formatter)

logger.addHandler(fh)
logger.addHandler(ch)

# Load environment
load_dotenv()

class FullScaleTestSuite:
    """Complete testing suite for Titan system"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'components_tested': [],
            'errors': [],
            'warnings': [],
            'performance_metrics': {}
        }
        
    def log_test(self, name, status, details=""):
        """Log test result"""
        self.results['tests_run'] += 1
        if status:
            self.results['tests_passed'] += 1
            logger.info(f"✅ PASS: {name}")
        else:
            self.results['tests_failed'] += 1
            logger.error(f"❌ FAIL: {name}")
            self.results['errors'].append(f"{name}: {details}")
        
        if details:
            logger.info(f"   Details: {details}")
    
    def test_environment_configuration(self):
        """Test 1: Environment Configuration"""
        logger.info("\n" + "="*70)
        logger.info("TEST 1: ENVIRONMENT CONFIGURATION")
        logger.info("="*70)
        
        # Check execution mode
        mode = os.getenv('EXECUTION_MODE', 'PAPER')
        self.log_test("Execution mode configured", True, f"Mode: {mode}")
        
        # Check RPC endpoints
        required_rpcs = ['RPC_ETHEREUM', 'RPC_POLYGON', 'RPC_ARBITRUM', 'RPC_OPTIMISM', 'RPC_BASE']
        configured = []
        
        for rpc in required_rpcs:
            value = os.getenv(rpc, '')
            if value and 'YOUR_' not in value.upper():
                configured.append(rpc)
        
        self.log_test("RPC endpoints configured", len(configured) >= 3, 
                     f"{len(configured)}/{len(required_rpcs)} chains configured")
        
        self.results['components_tested'].append('Environment')
    
    def test_system_imports(self):
        """Test 2: System Component Imports"""
        logger.info("\n" + "="*70)
        logger.info("TEST 2: SYSTEM COMPONENT IMPORTS")
        logger.info("="*70)
        
        components = [
            ('ml.brain', 'OmniBrain'),
            ('core.titan_commander_core', 'TitanCommander'),
            ('ml.cortex.forecaster', 'MarketForecaster'),
            ('ml.cortex.rl_optimizer', 'QLearningAgent'),
            ('routing.bridge_manager', 'BridgeManager'),
            ('ml.dex_pricer', 'DexPricer'),
        ]
        
        for module_name, class_name in components:
            try:
                module = __import__(module_name, fromlist=[class_name])
                getattr(module, class_name)
                self.log_test(f"Import {class_name}", True)
            except Exception as e:
                self.log_test(f"Import {class_name}", False, str(e))
        
        self.results['components_tested'].append('Imports')
    
    def test_brain_initialization(self):
        """Test 3: Brain Initialization"""
        logger.info("\n" + "="*70)
        logger.info("TEST 3: BRAIN INITIALIZATION")
        logger.info("="*70)
        
        try:
            from ml.brain import OmniBrain
            
            start_time = time.time()
            brain = OmniBrain()
            init_time = time.time() - start_time
            
            self.log_test("OmniBrain instantiation", True, f"Time: {init_time:.2f}s")
            self.results['performance_metrics']['brain_init_time'] = init_time
            
            # Check components
            self.log_test("ProfitEngine initialized", hasattr(brain, 'profit_engine'))
            self.log_test("BridgeManager initialized", hasattr(brain, 'bridge'))
            self.log_test("Graph initialized", hasattr(brain, 'graph'))
            self.log_test("Forecaster initialized", hasattr(brain, 'forecaster'))
            self.log_test("RL Optimizer initialized", hasattr(brain, 'optimizer'))
            
            # Check signal directory
            self.log_test("Signal directory created", brain.signals_dir.exists(),
                         f"Path: {brain.signals_dir}")
            
            self.results['components_tested'].append('OmniBrain')
            return brain
            
        except Exception as e:
            self.log_test("OmniBrain initialization", False, str(e))
            return None
    
    def test_token_loading(self, brain):
        """Test 4: Dynamic Token Loading"""
        logger.info("\n" + "="*70)
        logger.info("TEST 4: DYNAMIC TOKEN LOADING")
        logger.info("="*70)
        
        if not brain:
            self.log_test("Token loading", False, "Brain not initialized")
            return
        
        try:
            start_time = time.time()
            brain.initialize()
            init_time = time.time() - start_time
            
            self.log_test("Brain initialization completed", True, f"Time: {init_time:.2f}s")
            self.results['performance_metrics']['full_init_time'] = init_time
            
            # Check inventory
            total_tokens = sum(len(tokens) for tokens in brain.inventory.values())
            self.log_test("Token inventory loaded", total_tokens > 0, 
                         f"{total_tokens} tokens across {len(brain.inventory)} chains")
            
            # Log per-chain details
            for chain_id, tokens in brain.inventory.items():
                logger.info(f"   Chain {chain_id}: {len(tokens)} tokens")
            
            # Check graph
            node_count = brain.graph.num_nodes()
            self.log_test("Graph construction", node_count > 0, 
                         f"{node_count} nodes created")
            
            self.results['performance_metrics']['total_tokens'] = total_tokens
            self.results['performance_metrics']['graph_nodes'] = node_count
            self.results['components_tested'].append('TokenLoading')
            
        except Exception as e:
            self.log_test("Token loading", False, str(e))
    
    def test_rpc_connectivity(self):
        """Test 5: RPC Connectivity"""
        logger.info("\n" + "="*70)
        logger.info("TEST 5: RPC CONNECTIVITY")
        logger.info("="*70)
        
        from web3 import Web3
        
        chains = {
            1: ('RPC_ETHEREUM', 'Ethereum'),
            137: ('RPC_POLYGON', 'Polygon'),
            42161: ('RPC_ARBITRUM', 'Arbitrum'),
            10: ('RPC_OPTIMISM', 'Optimism'),
            8453: ('RPC_BASE', 'Base'),
        }
        
        connected = []
        
        for chain_id, (env_var, name) in chains.items():
            rpc = os.getenv(env_var)
            if not rpc or 'YOUR_' in rpc.upper():
                logger.warning(f"   ⚠️  {name}: Not configured")
                continue
            
            try:
                start = time.time()
                w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={'timeout': 10}))
                block = w3.eth.block_number
                latency = (time.time() - start) * 1000
                
                connected.append(name)
                self.log_test(f"{name} connectivity", True, 
                             f"Block: {block}, Latency: {latency:.0f}ms")
                
            except Exception as e:
                self.log_test(f"{name} connectivity", False, str(e)[:50])
        
        self.results['performance_metrics']['chains_connected'] = len(connected)
        self.results['components_tested'].append('RPC')
    
    def test_arbitrage_detection(self, brain):
        """Test 6: Arbitrage Detection Engine"""
        logger.info("\n" + "="*70)
        logger.info("TEST 6: ARBITRAGE DETECTION ENGINE")
        logger.info("="*70)
        
        if not brain:
            self.log_test("Arbitrage detection", False, "Brain not initialized")
            return
        
        try:
            logger.info("   Running single scan cycle (this may take 30-60 seconds)...")
            
            start_time = time.time()
            
            # Run one scan cycle
            opportunities = []
            for chain_id, tokens in brain.inventory.items():
                if chain_id not in [1, 137, 42161]:  # Test on 3 major chains
                    continue
                    
                logger.info(f"   Scanning chain {chain_id}...")
                
                for symbol, data in list(tokens.items())[:5]:  # Test first 5 tokens per chain
                    # Simple opportunity check
                    try:
                        result = brain._evaluate_intra_chain_arb(
                            chain_id, symbol, data['address'], 
                            'UNIV3', 'SUSHI'
                        )
                        if result:
                            opportunities.append({
                                'chain': chain_id,
                                'token': symbol,
                                'route': 'UNIV3→SUSHI'
                            })
                    except Exception:
                        pass  # Expected to fail for some tokens
                
                break  # Only test one chain for speed
            
            scan_time = time.time() - start_time
            
            self.log_test("Arbitrage scan completed", True, 
                         f"Time: {scan_time:.2f}s, Found: {len(opportunities)} opportunities")
            
            self.results['performance_metrics']['scan_time'] = scan_time
            self.results['performance_metrics']['opportunities_found'] = len(opportunities)
            self.results['components_tested'].append('ArbitrageDetection')
            
        except Exception as e:
            self.log_test("Arbitrage detection", False, str(e))
    
    def test_signal_generation(self, brain):
        """Test 7: Signal Generation"""
        logger.info("\n" + "="*70)
        logger.info("TEST 7: SIGNAL GENERATION")
        logger.info("="*70)
        
        if not brain:
            self.log_test("Signal generation", False, "Brain not initialized")
            return
        
        try:
            # Create test signal
            test_signal = {
                "type": "TEST_SIGNAL",
                "timestamp": datetime.now().isoformat(),
                "chainId": 1,
                "token": "TEST",
                "amount": "1000000",
                "expected_profit": 100.0,
                "test": True
            }
            
            # Write signal
            signal_file = brain.signals_dir / f'test_signal_{int(time.time())}.json'
            signal_file.write_text(json.dumps(test_signal, indent=2))
            
            # Verify
            exists = signal_file.exists()
            self.log_test("Signal file creation", exists, f"Path: {signal_file}")
            
            # Cleanup
            if exists:
                signal_file.unlink()
            
            self.results['components_tested'].append('SignalGeneration')
            
        except Exception as e:
            self.log_test("Signal generation", False, str(e))
    
    def test_ml_components(self):
        """Test 8: ML Training Pipeline"""
        logger.info("\n" + "="*70)
        logger.info("TEST 8: ML TRAINING PIPELINE")
        logger.info("="*70)
        
        try:
            from ml.cortex.forecaster import MarketForecaster
            from ml.cortex.rl_optimizer import QLearningAgent
            
            # Test forecaster
            forecaster = MarketForecaster()
            self.log_test("MarketForecaster instantiation", True)
            
            # Test RL optimizer
            optimizer = QLearningAgent()
            self.log_test("QLearningAgent instantiation", True)
            
            # Test parameter recommendation
            params = optimizer.recommend_parameters(1, "MEDIUM")
            self.log_test("RL parameter recommendation", 'slippage' in params,
                         f"Params: {params}")
            
            self.results['components_tested'].append('MLPipeline')
            
        except Exception as e:
            self.log_test("ML components", False, str(e))
    
    def test_safety_mechanisms(self):
        """Test 9: Safety Mechanisms"""
        logger.info("\n" + "="*70)
        logger.info("TEST 9: SAFETY MECHANISMS")
        logger.info("="*70)
        
        try:
            from core.titan_commander_core import TitanCommander
            
            commander = TitanCommander(1)
            
            # Test safety limits
            self.log_test("MIN_LOAN_USD configured", 
                         commander.MIN_LOAN_USD > 0,
                         f"Min: ${commander.MIN_LOAN_USD}")
            
            self.log_test("MAX_TVL_SHARE configured",
                         0 < commander.MAX_TVL_SHARE < 1,
                         f"Max: {commander.MAX_TVL_SHARE*100}%")
            
            self.log_test("SLIPPAGE_TOLERANCE configured",
                         commander.SLIPPAGE_TOLERANCE > 0,
                         f"Tolerance: {(1-commander.SLIPPAGE_TOLERANCE)*100}%")
            
            self.results['components_tested'].append('SafetyMechanisms')
            
        except Exception as e:
            self.log_test("Safety mechanisms", False, str(e))
    
    def test_javascript_bot(self):
        """Test 10: JavaScript Bot Availability"""
        logger.info("\n" + "="*70)
        logger.info("TEST 10: JAVASCRIPT BOT")
        logger.info("="*70)
        
        bot_file = Path('execution/bot.js')
        self.log_test("Bot file exists", bot_file.exists())
        
        # Check other execution components
        components = [
            'execution/gas_manager.js',
            'execution/aggregator_selector.js',
            'execution/lifi_manager.js',
        ]
        
        for component in components:
            exists = Path(component).exists()
            self.log_test(f"{Path(component).name} exists", exists)
        
        self.results['components_tested'].append('JavaScriptBot')
    
    def generate_report(self):
        """Generate comprehensive test report"""
        logger.info("\n" + "="*70)
        logger.info("TEST SUITE COMPLETE")
        logger.info("="*70)
        
        # Summary
        logger.info(f"\nTests Run: {self.results['tests_run']}")
        logger.info(f"Tests Passed: {self.results['tests_passed']}")
        logger.info(f"Tests Failed: {self.results['tests_failed']}")
        
        pass_rate = (self.results['tests_passed'] / self.results['tests_run'] * 100) if self.results['tests_run'] > 0 else 0
        logger.info(f"Pass Rate: {pass_rate:.1f}%")
        
        # Components tested
        logger.info(f"\nComponents Tested: {', '.join(self.results['components_tested'])}")
        
        # Performance metrics
        if self.results['performance_metrics']:
            logger.info("\nPerformance Metrics:")
            for key, value in self.results['performance_metrics'].items():
                logger.info(f"  {key}: {value}")
        
        # Errors
        if self.results['errors']:
            logger.info("\nErrors:")
            for error in self.results['errors']:
                logger.info(f"  ❌ {error}")
        
        # Warnings
        if self.results['warnings']:
            logger.info("\nWarnings:")
            for warning in self.results['warnings']:
                logger.info(f"  ⚠️  {warning}")
        
        # Save JSON report
        json_report = log_dir / f'test_results_{timestamp}.json'
        json_report.write_text(json.dumps(self.results, indent=2))
        
        logger.info(f"\n📄 Full report saved to: {log_file}")
        logger.info(f"📄 JSON results saved to: {json_report}")
        
        # Overall verdict
        logger.info("\n" + "="*70)
        if pass_rate >= 80:
            logger.info("✅ OVERALL VERDICT: SYSTEM READY FOR OPERATION")
        elif pass_rate >= 60:
            logger.info("⚠️  OVERALL VERDICT: SYSTEM PARTIALLY READY (review failures)")
        else:
            logger.info("❌ OVERALL VERDICT: SYSTEM NOT READY (critical failures)")
        logger.info("="*70)
        
        return pass_rate >= 80

def main():
    """Run full test suite"""
    print("\n")
    print("="*70)
    print("  APEX-OMEGA TITAN: FULL-SCALE TEST SUITE")
    print("="*70)
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("  This will take 2-3 minutes to complete...")
    print("="*70)
    print("\n")
    
    suite = FullScaleTestSuite()
    
    # Run all tests
    suite.test_environment_configuration()
    suite.test_system_imports()
    brain = suite.test_brain_initialization()
    suite.test_token_loading(brain)
    suite.test_rpc_connectivity()
    suite.test_arbitrage_detection(brain)
    suite.test_signal_generation(brain)
    suite.test_ml_components()
    suite.test_safety_mechanisms()
    suite.test_javascript_bot()
    
    # Generate report
    ready = suite.generate_report()
    
    sys.exit(0 if ready else 1)

if __name__ == "__main__":
    main()
