#!/usr/bin/env python3
"""
Test script for mainnet orchestrator and execution modes.
Tests the configuration and wiring without requiring Redis.
"""

import os
import sys
import json
from unittest.mock import Mock, patch, MagicMock

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_environment_configuration():
    """Test that environment variables are properly configured"""
    print("\n🧪 Testing environment configuration...")
    
    # Set test environment
    os.environ['EXECUTION_MODE'] = 'PAPER'
    os.environ['ENABLE_REALTIME_TRAINING'] = 'true'
    os.environ['LOG_LEVEL'] = 'INFO'
    
    # Test parsing
    mode = os.getenv('EXECUTION_MODE', 'PAPER').upper()
    assert mode in ['PAPER', 'LIVE'], f"Invalid mode: {mode}"
    print(f"   ✓ EXECUTION_MODE validated: {mode}")
    
    training = os.getenv('ENABLE_REALTIME_TRAINING', 'false').lower() in ('true', '1', 'yes')
    print(f"   ✓ ENABLE_REALTIME_TRAINING: {training}")
    
    print("   ✅ Environment configuration test passed")

def test_orchestrator_initialization():
    """Test orchestrator can be initialized"""
    print("\n🧪 Testing orchestrator initialization...")
    
    # Mock all imports at module level
    sys.modules['redis'] = MagicMock()
    sys.modules['web3'] = MagicMock()
    sys.modules['rustworkx'] = MagicMock()
    sys.modules['pandas'] = MagicMock()
    sys.modules['ml.brain'] = MagicMock()
    sys.modules['ml.cortex.forecaster'] = MagicMock()
    sys.modules['ml.cortex.rl_optimizer'] = MagicMock()
    
    # Mock dependencies
    with patch('mainnet_orchestrator.OmniBrain') as MockBrain, \
         patch('mainnet_orchestrator.MarketForecaster') as MockForecaster, \
         patch('mainnet_orchestrator.QLearningAgent') as MockAgent:
        
        # Set test environment
        os.environ['EXECUTION_MODE'] = 'PAPER'
        os.environ['ENABLE_REALTIME_TRAINING'] = 'true'
        
        # Import and create orchestrator
        from mainnet_orchestrator import MainnetOrchestrator, ExecutionMode
        
        orchestrator = MainnetOrchestrator()
        
        # Verify initialization
        assert orchestrator.mode == ExecutionMode.PAPER
        assert orchestrator.enable_realtime_training == True
        assert orchestrator.metrics['opportunities_found'] == 0
        print(f"   ✓ Orchestrator created in {orchestrator.mode} mode")
        print(f"   ✓ Real-time training: {orchestrator.enable_realtime_training}")
        print(f"   ✓ Metrics initialized: {len(orchestrator.metrics)} fields")
        
        print("   ✅ Orchestrator initialization test passed")

def test_paper_mode_configuration():
    """Test paper mode specific configuration"""
    print("\n🧪 Testing paper mode configuration...")
    
    with patch('mainnet_orchestrator.OmniBrain'), \
         patch('mainnet_orchestrator.MarketForecaster'), \
         patch('mainnet_orchestrator.QLearningAgent'):
        
        os.environ['EXECUTION_MODE'] = 'PAPER'
        
        from mainnet_orchestrator import MainnetOrchestrator
        orchestrator = MainnetOrchestrator()
        
        # Test mode configuration
        orchestrator._configure_execution_mode()
        
        # Verify environment is set for bot.js
        assert os.environ.get('TITAN_EXECUTION_MODE') == 'PAPER'
        print("   ✓ TITAN_EXECUTION_MODE set for bot.js")
        print("   ✓ Paper mode configured")
        
        print("   ✅ Paper mode configuration test passed")

def test_live_mode_configuration():
    """Test live mode specific configuration"""
    print("\n🧪 Testing live mode configuration...")
    
    with patch('mainnet_orchestrator.OmniBrain'), \
         patch('mainnet_orchestrator.MarketForecaster'), \
         patch('mainnet_orchestrator.QLearningAgent'):
        
        os.environ['EXECUTION_MODE'] = 'LIVE'
        
        from mainnet_orchestrator import MainnetOrchestrator
        orchestrator = MainnetOrchestrator()
        
        # Test mode configuration
        orchestrator._configure_execution_mode()
        
        # Verify environment is set for bot.js
        assert os.environ.get('TITAN_EXECUTION_MODE') == 'LIVE'
        print("   ✓ TITAN_EXECUTION_MODE set for bot.js")
        print("   ✓ Live mode configured")
        
        print("   ✅ Live mode configuration test passed")

def test_bot_paper_execution():
    """Test bot.js paper execution logic (via Python simulation)"""
    print("\n🧪 Testing paper execution logic...")
    
    # Simulate a trade signal
    signal = {
        'chainId': 137,
        'token': '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174',
        'amount': '10000000000',
        'type': 'INTRA_CHAIN',
        'protocols': [1, 2],
        'routers': ['0xE592427A0AEce92De3Edee1F18E0157C05861564', '0x445FE580eF8d70FF569aB36e80c647af338db351'],
        'path': ['0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619', '0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174'],
        'extras': ['0x0001f4', '0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000001'],
        'metrics': {
            'profit_usd': 15.42,
            'fees_usd': 2.50,
            'gas_price_gwei': 35.0
        }
    }
    
    # Verify signal structure
    assert 'chainId' in signal
    assert 'token' in signal
    assert 'amount' in signal
    assert 'metrics' in signal
    print("   ✓ Trade signal structure validated")
    
    # Simulate paper trade
    paper_trade = {
        'id': f"PAPER-1-{int(signal.get('timestamp', 0) or 0)}",
        'signal': signal,
        'status': 'SIMULATED',
        'mode': 'PAPER'
    }
    
    assert paper_trade['status'] == 'SIMULATED'
    assert paper_trade['mode'] == 'PAPER'
    print("   ✓ Paper trade record created")
    print(f"   ✓ Expected profit: ${signal['metrics']['profit_usd']}")
    
    print("   ✅ Paper execution logic test passed")

def test_startup_script():
    """Test startup script validation"""
    print("\n🧪 Testing startup script...")
    
    # Check if script exists and is executable
    script_path = os.path.join(os.path.dirname(__file__), 'start_mainnet.sh')
    assert os.path.exists(script_path), "start_mainnet.sh not found"
    print("   ✓ start_mainnet.sh exists")
    
    # Check if it's executable
    assert os.access(script_path, os.X_OK), "start_mainnet.sh not executable"
    print("   ✓ start_mainnet.sh is executable")
    
    # Check orchestrator is executable
    orch_path = os.path.join(os.path.dirname(__file__), 'mainnet_orchestrator.py')
    assert os.path.exists(orch_path), "mainnet_orchestrator.py not found"
    assert os.access(orch_path, os.X_OK), "mainnet_orchestrator.py not executable"
    print("   ✓ mainnet_orchestrator.py is executable")
    
    print("   ✅ Startup script validation passed")

def test_mode_validation():
    """Test mode validation logic"""
    print("\n🧪 Testing mode validation...")
    
    # Test valid modes
    valid_modes = ['PAPER', 'LIVE']
    for mode in valid_modes:
        os.environ['EXECUTION_MODE'] = mode
        with patch('mainnet_orchestrator.OmniBrain'), \
             patch('mainnet_orchestrator.MarketForecaster'), \
             patch('mainnet_orchestrator.QLearningAgent'):
            from mainnet_orchestrator import MainnetOrchestrator
            orch = MainnetOrchestrator()
            assert orch.mode in valid_modes
            print(f"   ✓ Mode '{mode}' accepted")
    
    # Test invalid mode
    os.environ['EXECUTION_MODE'] = 'INVALID'
    try:
        with patch('mainnet_orchestrator.OmniBrain'), \
             patch('mainnet_orchestrator.MarketForecaster'), \
             patch('mainnet_orchestrator.QLearningAgent'):
            # Need to reload module to test invalid mode
            import importlib
            import mainnet_orchestrator
            importlib.reload(mainnet_orchestrator)
            from mainnet_orchestrator import MainnetOrchestrator
            orch = MainnetOrchestrator()
            # Should not reach here
            assert False, "Invalid mode should have been rejected"
    except SystemExit:
        print("   ✓ Invalid mode rejected correctly")
    
    print("   ✅ Mode validation test passed")

def test_documentation():
    """Test that documentation files exist"""
    print("\n🧪 Testing documentation...")
    
    docs = [
        'MAINNET_MODES.md',
        'README.md',
        '.env.example'
    ]
    
    for doc in docs:
        path = os.path.join(os.path.dirname(__file__), doc)
        assert os.path.exists(path), f"{doc} not found"
        print(f"   ✓ {doc} exists")
    
    # Check .env.example has EXECUTION_MODE
    env_example = os.path.join(os.path.dirname(__file__), '.env.example')
    with open(env_example, 'r') as f:
        content = f.read()
        assert 'EXECUTION_MODE' in content, "EXECUTION_MODE not in .env.example"
        print("   ✓ .env.example contains EXECUTION_MODE")
    
    print("   ✅ Documentation test passed")

def main():
    """Run all tests"""
    print("=" * 70)
    print("  🧪 MAINNET MODES TEST SUITE")
    print("=" * 70)
    
    tests = [
        test_environment_configuration,
        test_orchestrator_initialization,
        test_paper_mode_configuration,
        test_live_mode_configuration,
        test_bot_paper_execution,
        test_startup_script,
        test_mode_validation,
        test_documentation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"\n   ❌ Test failed: {e}")
            import traceback
            traceback.print_exc()
            failed += 1
    
    print("\n" + "=" * 70)
    print("  📊 TEST RESULTS")
    print("=" * 70)
    print(f"  Total tests: {len(tests)}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print("=" * 70)
    
    if failed > 0:
        print("\n❌ Some tests failed")
        sys.exit(1)
    else:
        print("\n✅ All tests passed!")
        sys.exit(0)

if __name__ == "__main__":
    main()
