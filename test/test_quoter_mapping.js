/**
 * Test for OmniSDKEngine Quoter Address Mapping
 * Verifies:
 * 1. Correct quoter addresses for all supported chains
 * 2. Fail-closed behavior for unsupported chains
 */

const { OmniSDKEngine } = require('../execution/omniarb_sdk_engine.js');

// Test data: chains we support
const SUPPORTED_CHAINS = {
    1: "Ethereum Mainnet",
    137: "Polygon",
    42161: "Arbitrum One",
    10: "Optimism",
    8453: "Base",
    56: "BNB Smart Chain",
    43114: "Avalanche",
    42220: "Celo",
    324: "zkSync Era",
    81457: "Blast"
};

// Chains without official Uniswap V3 deployment
const UNSUPPORTED_CHAINS = {
    250: "Fantom",
    59144: "Linea",
    534352: "Scroll",
    5000: "Mantle",
    204: "opBNB"
};

console.log("🧪 Testing Quoter Address Mapping");
console.log("=".repeat(60));

// Test 1: Verify supported chains have quoter addresses
console.log("\n✅ Test 1: Supported chains should have quoter addresses");
let passedSupported = 0;
let failedSupported = 0;

for (const [chainId, name] of Object.entries(SUPPORTED_CHAINS)) {
    try {
        // Create a dummy RPC URL for testing (we only test the mapping)
        const engine = new OmniSDKEngine(parseInt(chainId), "https://dummy.rpc.url");
        const quoterAddr = engine.QUOTER_V3_ADDR;
        
        if (quoterAddr && quoterAddr.startsWith('0x') && quoterAddr.length === 42) {
            console.log(`  ✓ Chain ${chainId} (${name}): ${quoterAddr}`);
            passedSupported++;
        } else {
            console.log(`  ✗ Chain ${chainId} (${name}): Invalid address format`);
            failedSupported++;
        }
    } catch (error) {
        console.log(`  ✗ Chain ${chainId} (${name}): ${error.message}`);
        failedSupported++;
    }
}

// Test 2: Verify unsupported chains throw errors (fail-closed)
console.log("\n✅ Test 2: Unsupported chains should throw errors (fail-closed)");
let passedUnsupported = 0;
let failedUnsupported = 0;

for (const [chainId, name] of Object.entries(UNSUPPORTED_CHAINS)) {
    try {
        new OmniSDKEngine(parseInt(chainId), "https://dummy.rpc.url");
        console.log(`  ✗ Chain ${chainId} (${name}): Should have thrown error but didn't`);
        failedUnsupported++;
    } catch (error) {
        if (error.message.includes('QuoterV2 not available')) {
            console.log(`  ✓ Chain ${chainId} (${name}): Correctly threw error`);
            passedUnsupported++;
        } else {
            console.log(`  ✗ Chain ${chainId} (${name}): Wrong error: ${error.message}`);
            failedUnsupported++;
        }
    }
}

// Test 3: Verify no fallback to default address
console.log("\n✅ Test 3: Unknown chain should not fallback to default");
let passedUnknown = 0;
let failedUnknown = 0;
const UNKNOWN_CHAIN = 999999;
try {
    const engine = new OmniSDKEngine(UNKNOWN_CHAIN, "https://dummy.rpc.url");
    console.log(`  ✗ Unknown chain ${UNKNOWN_CHAIN}: Should have thrown error but didn't`);
    failedUnknown++;
} catch (error) {
    if (error.message.includes('QuoterV2 not available')) {
        console.log(`  ✓ Unknown chain ${UNKNOWN_CHAIN}: Correctly threw error (no fallback)`);
        passedUnknown++;
    } else {
        console.log(`  ✗ Unknown chain ${UNKNOWN_CHAIN}: Wrong error: ${error.message}`);
        failedUnknown++;
    }
}

// Summary
console.log("\n" + "=".repeat(60));
console.log("📊 Test Summary:");
console.log(`  Supported chains: ${passedSupported}/${passedSupported + failedSupported} passed`);
console.log(`  Fail-closed tests: ${passedUnsupported}/${passedUnsupported + failedUnsupported} passed`);
console.log(`  Unknown chain test: ${passedUnknown}/${passedUnknown + failedUnknown} passed`);

const totalPassed = passedSupported + passedUnsupported + passedUnknown;
const totalFailed = failedSupported + failedUnsupported + failedUnknown;
const totalTests = totalPassed + totalFailed;

if (totalFailed === 0) {
    console.log(`\n✅ All ${totalTests} tests PASSED!`);
    process.exit(0);
} else {
    console.log(`\n❌ ${totalFailed} of ${totalTests} tests FAILED!`);
    process.exit(1);
}
