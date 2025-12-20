"""
Quick test script to verify all systems are wired correctly
"""
import sys
import os

print("="*70)
print("  TITAN SYSTEM TEST")
print("="*70)
print()

# Test 1: Imports
print("TEST 1: Component Imports")
print("-"*70)

try:
    from ml.brain import OmniBrain
    print("✅ OmniBrain")
except Exception as e:
    print(f"❌ OmniBrain: {e}")
    
try:
    from core.titan_commander_core import TitanCommander
    print("✅ TitanCommander")
except Exception as e:
    print(f"❌ TitanCommander: {e}")

try:
    from ml.cortex.forecaster import MarketForecaster
    print("✅ MarketForecaster")
except Exception as e:
    print(f"❌ MarketForecaster: {e}")

try:
    from ml.cortex.rl_optimizer import QLearningAgent
    print("✅ QLearningAgent")
except Exception as e:
    print(f"❌ QLearningAgent: {e}")

print()

# Test 2: File Structure
print("TEST 2: File Structure")
print("-"*70)

from pathlib import Path

files_to_check = [
    'execution/bot.js',
    'execution/gas_manager.js',
    'execution/aggregator_selector.js',
    'mainnet_orchestrator.py',
    'system_wiring.py',
    'mainnet_health_monitor.py'
]

for file in files_to_check:
    if Path(file).exists():
        print(f"✅ {file}")
    else:
        print(f"❌ {file} NOT FOUND")

print()

# Test 3: Directories
print("TEST 3: Signal Directories")
print("-"*70)

dirs = ['signals/outgoing', 'signals/processed', 'logs']
for d in dirs:
    path = Path(d)
    path.mkdir(parents=True, exist_ok=True)
    if path.exists():
        print(f"✅ {d}")
    else:
        print(f"❌ {d}")

print()

# Test 4: Environment
print("TEST 4: Environment Configuration")
print("-"*70)

from dotenv import load_dotenv
load_dotenv()

mode = os.getenv('EXECUTION_MODE', 'PAPER')
print(f"Execution Mode: {mode}")

rpc_count = 0
rpcs = ['RPC_ETHEREUM', 'RPC_POLYGON', 'RPC_ARBITRUM', 'RPC_OPTIMISM', 'RPC_BASE']
for rpc in rpcs:
    val = os.getenv(rpc, '')
    if val and 'YOUR_' not in val:
        print(f"✅ {rpc} configured")
        rpc_count += 1
    else:
        print(f"⚠️  {rpc} not configured")

print(f"\nTotal RPCs configured: {rpc_count}/5")

print()

# Test 5: Quick Brain Test
print("TEST 5: OmniBrain Initialization Test")
print("-"*70)

try:
    brain = OmniBrain()
    print("✅ OmniBrain instance created")
    print(f"   Signal directory: {brain.signals_dir}")
    print(f"   Wallet address: {brain.wallet_address[:10]}...")
except Exception as e:
    print(f"❌ OmniBrain initialization failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("="*70)
print("  TEST COMPLETE")
print("="*70)
