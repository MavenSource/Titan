#!/usr/bin/env python3
"""
Test Python-to-Node.js execution communication without Redis
"""

import asyncio
import logging
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from execution.execution_client import ExecutionManager, TradeSignal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger("TestExecution")

async def test_connection():
    """Test basic connection to execution server"""
    print("\n" + "="*80)
    print("TEST 1: Connection to Execution Server")
    print("="*80)
    
    manager = ExecutionManager()
    connected = await manager.initialize()
    
    if connected:
        print("✅ Successfully connected to execution server")
        
        # Get stats
        stats = await manager.get_statistics()
        print(f"\n📊 Server Statistics:")
        print(f"  Mode: {stats['server'].get('mode', 'UNKNOWN')}")
        print(f"  Chains: {stats['server'].get('providers', 0)}")
        print(f"  Uptime: {stats['server'].get('uptime', 0):.0f}s")
        
        await manager.close()
        return True
    else:
        print("❌ Failed to connect to execution server")
        print("\n⚠️  Make sure server is running:")
        print("   node execution/execution_server.js")
        return False

async def test_paper_trade():
    """Test paper trade execution"""
    print("\n" + "="*80)
    print("TEST 2: Paper Trade Execution")
    print("="*80)
    
    manager = ExecutionManager()
    await manager.initialize()
    
    # Create test signal for Ethereum mainnet
    result = await manager.submit_trade(
        chain_id=1,
        token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC on Ethereum
        amount="1000000000",  # 1000 USDC (6 decimals)
        flash_source=1,  # Balancer V3
        protocols=[0, 1],  # Uniswap V2, V3
        routers=[
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",  # Uniswap V2
            "0xE592427A0AEce92De3Edee1F18E0157C05861564"   # Uniswap V3
        ],
        path=[
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"   # WETH
        ],
        extras=[b'', b''],
        expected_profit=50.0
    )
    
    if result.get('success'):
        print(f"✅ Paper trade executed successfully")
        print(f"  Mode: {result.get('mode')}")
        print(f"  Expected Profit: ${result.get('expected_profit')}")
        await manager.close()
        return True
    else:
        print(f"❌ Paper trade failed: {result.get('error')}")
        await manager.close()
        return False

async def test_multi_chain():
    """Test trades on multiple chains"""
    print("\n" + "="*80)
    print("TEST 3: Multi-Chain Execution")
    print("="*80)
    
    manager = ExecutionManager()
    await manager.initialize()
    
    # Test signals for different chains
    test_chains = [
        {
            "name": "Ethereum",
            "chain_id": 1,
            "token": "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",  # USDC
            "amount": "1000000000"
        },
        {
            "name": "Polygon",
            "chain_id": 137,
            "token": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC
            "amount": "1000000000"
        },
        {
            "name": "Arbitrum",
            "chain_id": 42161,
            "token": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # USDC
            "amount": "1000000000"
        }
    ]
    
    success_count = 0
    
    for test in test_chains:
        print(f"\n  Testing {test['name']}...")
        
        result = await manager.submit_trade(
            chain_id=test['chain_id'],
            token=test['token'],
            amount=test['amount'],
            flash_source=1,
            protocols=[0],
            routers=["0x0000000000000000000000000000000000000000"],
            path=[test['token']],
            extras=[b''],
            expected_profit=25.0
        )
        
        if result.get('success'):
            print(f"  ✅ {test['name']}: Success")
            success_count += 1
        else:
            print(f"  ❌ {test['name']}: {result.get('error', 'Failed')}")
    
    print(f"\n📊 Results: {success_count}/{len(test_chains)} chains successful")
    
    await manager.close()
    return success_count == len(test_chains)

async def test_statistics():
    """Test statistics retrieval"""
    print("\n" + "="*80)
    print("TEST 4: Statistics Retrieval")
    print("="*80)
    
    manager = ExecutionManager()
    await manager.initialize()
    
    # Submit a few test trades
    for i in range(3):
        await manager.submit_trade(
            chain_id=1,
            token="0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            amount="1000000000",
            flash_source=1,
            protocols=[0],
            routers=["0x0000000000000000000000000000000000000000"],
            path=["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"],
            extras=[b''],
            expected_profit=10.0 * (i + 1)
        )
    
    # Get combined statistics
    stats = await manager.get_statistics()
    
    print("\n📊 Client Statistics:")
    print(f"  Sent: {stats['client']['sent']}")
    print(f"  Succeeded: {stats['client']['succeeded']}")
    print(f"  Failed: {stats['client']['failed']}")
    
    print("\n📊 Server Statistics:")
    print(f"  Total Signals: {stats['server'].get('total_signals', 0)}")
    print(f"  Executed: {stats['server'].get('executed', 0)}")
    print(f"  Paper: {stats['server'].get('paper_executed', 0)}")
    print(f"  Failed: {stats['server'].get('failed', 0)}")
    print(f"  Total Profit: ${stats['server'].get('total_profit', 0):.2f}")
    
    await manager.close()
    return True

async def run_all_tests():
    """Run all tests"""
    print("\n" + "="*80)
    print("TITAN EXECUTION LAYER - PYTHON-TO-NODE COMMUNICATION TEST")
    print("="*80)
    print("\n⚠️  Prerequisites:")
    print("  1. Node.js execution server must be running")
    print("  2. Command: node execution/execution_server.js")
    print("  3. Server listens on http://localhost:8545")
    print("\n")
    
    results = {
        "Connection": False,
        "Paper Trade": False,
        "Multi-Chain": False,
        "Statistics": False
    }
    
    try:
        # Test 1: Connection
        results["Connection"] = await test_connection()
        
        if not results["Connection"]:
            print("\n❌ Connection test failed. Cannot proceed with other tests.")
            print("Make sure execution server is running!")
            return False
        
        # Test 2: Paper Trade
        results["Paper Trade"] = await test_paper_trade()
        
        # Test 3: Multi-Chain
        results["Multi-Chain"] = await test_multi_chain()
        
        # Test 4: Statistics
        results["Statistics"] = await test_statistics()
        
    except Exception as e:
        print(f"\n❌ Test suite error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Print summary
    print("\n" + "="*80)
    print("TEST RESULTS SUMMARY")
    print("="*80)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {test_name}: {status}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n🎉 All tests passed! Python-to-Node communication working perfectly.")
        print("✅ Ready for production use")
    else:
        print("\n⚠️  Some tests failed. Check server logs for details.")
    
    print("="*80 + "\n")
    
    return all_passed

if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)
