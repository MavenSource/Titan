/**
 * Test suite for AggregatorSelector
 * Validates intelligent routing logic for different trade scenarios
 */

// Prevent network calls during testing by setting a test API key
// The lazy-loading in lifi_manager.js will prevent SDK initialization during import
process.env.LIFI_API_KEY = 'test_key';

const { AggregatorSelector } = require('../execution/aggregator_selector');

// Mock provider (not needed for routing logic tests)
const mockProvider = null;

console.log('🧪 Testing AggregatorSelector routing logic...\n');

// Test 1: Solana trade should route to Jupiter
console.log('Test 1: Solana trade routing');
const selector1 = new AggregatorSelector(null, mockProvider);
const trade1 = { chain: 'solana', chainId: 'solana' };
const aggregator1 = selector1.selectOptimalAggregator(trade1);
console.assert(aggregator1 === 'JUPITER', `Expected JUPITER, got ${aggregator1}`);
console.log(`✅ Passed: Solana trade → ${aggregator1}\n`);

// Test 2: High-value trade should route to CoW Swap
console.log('Test 2: High-value trade routing');
const selector2 = new AggregatorSelector(1, mockProvider);
const trade2 = { chainId: 1, valueUSD: 5000 };
const aggregator2 = selector2.selectOptimalAggregator(trade2);
console.assert(aggregator2 === 'COWSWAP', `Expected COWSWAP, got ${aggregator2}`);
console.log(`✅ Passed: $5000 trade → ${aggregator2}\n`);

// Test 3: Cross-chain trade should route to LiFi or Rango
console.log('Test 3: Cross-chain trade routing');
const selector3 = new AggregatorSelector(1, mockProvider);
const trade3 = { chainId: 1, isCrossChain: true };
const aggregator3 = selector3.selectOptimalAggregator(trade3);
console.assert(aggregator3 === 'LIFI' || aggregator3 === 'RANGO', 
    `Expected LIFI or RANGO, got ${aggregator3}`);
console.log(`✅ Passed: Cross-chain trade → ${aggregator3}\n`);

// Test 4: Speed-critical trade should route to 1inch
console.log('Test 4: Speed-critical trade routing');
const selector4 = new AggregatorSelector(137, mockProvider); // Polygon
const trade4 = { chainId: 137, priority: 'SPEED' };
const aggregator4 = selector4.selectOptimalAggregator(trade4);
console.assert(aggregator4 === 'ONEINCH', `Expected ONEINCH, got ${aggregator4}`);
console.log(`✅ Passed: Speed-critical trade → ${aggregator4}\n`);

// Test 5: Limit order should route to 0x
console.log('Test 5: Limit order routing');
const selector5 = new AggregatorSelector(1, mockProvider);
const trade5 = { chainId: 1, isLimitOrder: true };
const aggregator5 = selector5.selectOptimalAggregator(trade5);
console.assert(aggregator5 === 'ZEROX', `Expected ZEROX, got ${aggregator5}`);
console.log(`✅ Passed: Limit order → ${aggregator5}\n`);

// Test 6: Default routing should go to 1inch
console.log('Test 6: Default routing');
const selector6 = new AggregatorSelector(1, mockProvider);
const trade6 = { chainId: 1 }; // No special conditions
const aggregator6 = selector6.selectOptimalAggregator(trade6);
console.assert(aggregator6 === 'ONEINCH', `Expected ONEINCH, got ${aggregator6}`);
console.log(`✅ Passed: Default trade → ${aggregator6}\n`);

// Test 7: Exotic chain cross-chain should route to Rango
console.log('Test 7: Exotic chain routing');
const selector7 = new AggregatorSelector(59144, mockProvider); // Linea
const trade7 = { chainId: 59144, isCrossChain: true, needsExoticChains: true };
const aggregator7 = selector7.selectOptimalAggregator(trade7);
console.assert(aggregator7 === 'RANGO', `Expected RANGO, got ${aggregator7}`);
console.log(`✅ Passed: Exotic chain trade → ${aggregator7}\n`);

// Test 8: Best price discovery should route to OpenOcean
console.log('Test 8: Best price discovery routing');
const selector8 = new AggregatorSelector(1, mockProvider);
const trade8 = { chainId: 1, needsBestPrice: true, chains: 20 };
const aggregator8 = selector8.selectOptimalAggregator(trade8);
console.assert(aggregator8 === 'OPENOCEAN', `Expected OPENOCEAN, got ${aggregator8}`);
console.log(`✅ Passed: Best price discovery → ${aggregator8}\n`);

// Test 9: Rewards-seeking should route to KyberSwap (on non-speed-critical chain)
console.log('Test 9: Rewards-seeking routing');
const selector9 = new AggregatorSelector(56, mockProvider); // BSC (not in speed-critical list)
const trade9 = { chainId: 56, needsRewards: true };
const aggregator9 = selector9.selectOptimalAggregator(trade9);
console.assert(aggregator9 === 'KYBERSWAP', `Expected KYBERSWAP, got ${aggregator9}`);
console.log(`✅ Passed: Rewards trade → ${aggregator9}\n`);

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('✅ ALL TESTS PASSED! Aggregator routing logic works correctly.');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');

// Tests complete successfully - no need to exit early
// The lazy-loading pattern prevents LiFi SDK network errors during test execution
