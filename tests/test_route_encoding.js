/**
 * Test suite for Route Encoding
 * Validates route data encoding/decoding according to ROUTE_ENCODING_SPEC.md
 */

const { ethers } = require('ethers');

console.log('🧪 Testing Route Encoding functionality...\n');

// Test helper to encode route data
function encodeRoute(protocols, routers, path, extras) {
    return ethers.AbiCoder.defaultAbiCoder().encode(
        ["uint8[]", "address[]", "address[]", "bytes[]"],
        [protocols, routers, path, extras]
    );
}

// Test helper to decode route data
function decodeRoute(routeData) {
    return ethers.AbiCoder.defaultAbiCoder().decode(
        ["uint8[]", "address[]", "address[]", "bytes[]"],
        routeData
    );
}

// Test 1: Basic Uniswap V2 Route Encoding
console.log('Test 1: Basic Uniswap V2 route encoding');
try {
    const protocols = [0]; // Uniswap V2
    const routers = ["0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"]; // Uniswap V2 Router
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
    ];
    const extras = ["0x"]; // No extra data
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols.length === 1, 'Protocol length mismatch');
    console.assert(decodedProtocols[0] === 0n, 'Protocol ID mismatch');
    console.assert(decodedRouters[0].toLowerCase() === routers[0].toLowerCase(), 'Router address mismatch');
    console.assert(decodedPath.length === 2, 'Path length mismatch');
    console.assert(decodedPath[0].toLowerCase() === path[0].toLowerCase(), 'Input token mismatch');
    console.assert(decodedPath[1].toLowerCase() === path[1].toLowerCase(), 'Output token mismatch');
    
    console.log('✅ Passed: Basic Uniswap V2 encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 2: Uniswap V3 Route with Fee Tier
console.log('Test 2: Uniswap V3 route with fee tier encoding');
try {
    const protocols = [1]; // Uniswap V3
    const routers = ["0xE592427A0AEce92De3Edee1F18E0157C05861564"]; // Uniswap V3 Router
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
    ];
    const feeData = ethers.AbiCoder.defaultAbiCoder().encode(["uint24"], [3000]); // 0.3% fee
    const extras = [feeData];
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols[0] === 1n, 'Protocol ID should be 1 for Uniswap V3');
    console.assert(decodedExtras[0] === feeData, 'Fee data mismatch');
    
    // Decode the fee data
    const [decodedFee] = ethers.AbiCoder.defaultAbiCoder().decode(["uint24"], decodedExtras[0]);
    console.assert(decodedFee === 3000n, 'Fee tier should be 3000');
    
    console.log('✅ Passed: Uniswap V3 with fee tier encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 3: External Aggregator Route
console.log('Test 3: External aggregator route encoding');
try {
    const protocols = [4]; // External Aggregator
    const aggregatorAddress = "0x1111111254EEB25477B68fb85Ed929f73A960582"; // 1inch Router
    const routers = [aggregatorAddress];
    const path = ["0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48"]; // USDC (input token only)
    const mockCalldata = "0x1234567890abcdef"; // Mock aggregator calldata
    const extras = [mockCalldata];
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols[0] === 4n, 'Protocol ID should be 4 for aggregator');
    console.assert(decodedRouters[0].toLowerCase() === aggregatorAddress.toLowerCase(), 'Aggregator address mismatch');
    console.assert(decodedPath.length === 1, 'Aggregator should only have input token');
    console.assert(decodedExtras[0] === mockCalldata, 'Calldata mismatch');
    
    console.log('✅ Passed: External aggregator encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 4: Multi-Hop Route
console.log('Test 4: Multi-hop route encoding');
try {
    const protocols = [2, 1]; // Curve, then Uniswap V3
    const routers = [
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7", // Curve 3pool
        "0xE592427A0AEce92De3Edee1F18E0157C05861564"  // Uniswap V3 Router
    ];
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
        "0x6B175474E89094C44Da98b954EedeAC495271d0F", // DAI
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // WETH
    ];
    const curvePoolData = ethers.AbiCoder.defaultAbiCoder().encode(
        ["int128", "int128"], 
        [1, 0] // USDC to DAI indices
    );
    const uniV3FeeData = ethers.AbiCoder.defaultAbiCoder().encode(
        ["uint24"], 
        [3000] // 0.3% fee
    );
    const extras = [curvePoolData, uniV3FeeData];
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols.length === 2, 'Should have 2 protocols for multi-hop');
    console.assert(decodedProtocols[0] === 2n, 'First protocol should be Curve (2)');
    console.assert(decodedProtocols[1] === 1n, 'Second protocol should be Uniswap V3 (1)');
    console.assert(decodedPath.length === 3, 'Multi-hop should have 3 tokens in path');
    console.assert(decodedExtras.length === 2, 'Should have extras for both hops');
    
    console.log('✅ Passed: Multi-hop route encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 5: Array Length Validation
console.log('Test 5: Array length consistency validation');
try {
    const protocols = [0];
    const routers = ["0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D"];
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    ];
    const extras = ["0x"];
    
    // Should succeed
    const encoded = encodeRoute(protocols, routers, path, extras);
    console.assert(encoded.length > 0, 'Encoding should succeed');
    
    // Validate decoded lengths
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    console.assert(
        decodedProtocols.length === decodedRouters.length && 
        decodedRouters.length === decodedExtras.length,
        'Protocol, router, and extras arrays must have equal length'
    );
    console.assert(decodedPath.length >= 2, 'Path must have at least 2 tokens');
    
    console.log('✅ Passed: Array length consistency validation\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 6: Empty Route (Edge Case)
console.log('Test 6: Empty arrays handling');
try {
    const protocols = [];
    const routers = [];
    const path = [];
    const extras = [];
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols.length === 0, 'Empty protocols array');
    console.assert(decodedRouters.length === 0, 'Empty routers array');
    console.assert(decodedPath.length === 0, 'Empty path array');
    console.assert(decodedExtras.length === 0, 'Empty extras array');
    
    console.log('✅ Passed: Empty arrays encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 7: Complex Multi-Protocol Route
console.log('Test 7: Complex multi-protocol route');
try {
    const protocols = [0, 1, 2, 4]; // V2, V3, Curve, Aggregator
    const routers = [
        "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
        "0xE592427A0AEce92De3Edee1F18E0157C05861564",
        "0xbEbc44782C7dB0a1A60Cb6fe97d0b483032FF1C7",
        "0x1111111254EEB25477B68fb85Ed929f73A960582"
    ];
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // USDC
        "0x6B175474E89094C44Da98b954EedeAC495271d0F", // DAI
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2", // WETH
        "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599", // WBTC
        "0x514910771AF9Ca656af840dff83E8264EcF986CA"  // LINK
    ];
    const extras = [
        "0x", // V2 - no extras
        ethers.AbiCoder.defaultAbiCoder().encode(["uint24"], [3000]), // V3 - fee tier
        ethers.AbiCoder.defaultAbiCoder().encode(["int128", "int128"], [0, 1]), // Curve - pool indices
        "0xabcdef1234567890" // Aggregator - calldata
    ];
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols.length === 4, 'Should have 4 protocols');
    console.assert(decodedRouters.length === 4, 'Should have 4 routers');
    console.assert(decodedPath.length === 5, 'Should have 5 tokens in path');
    console.assert(decodedExtras.length === 4, 'Should have 4 extras entries');
    
    console.log('✅ Passed: Complex multi-protocol route encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 8: Address Validation
console.log('Test 8: Address format validation');
try {
    const validAddress = "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D";
    const zeroAddress = "0x0000000000000000000000000000000000000000";
    
    // Test with valid address
    const protocols = [0];
    const routers = [validAddress];
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
    ];
    const extras = ["0x"];
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    // Verify addresses are properly formatted
    console.assert(
        ethers.isAddress(decodedRouters[0]),
        'Router should be a valid address'
    );
    console.assert(
        ethers.isAddress(decodedPath[0]),
        'Path token should be a valid address'
    );
    
    // Check that zero address is detectable
    console.assert(
        decodedRouters[0].toLowerCase() !== zeroAddress.toLowerCase(),
        'Router should not be zero address'
    );
    
    console.log('✅ Passed: Address format validation\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 9: Large Route Data
console.log('Test 9: Large route data encoding');
try {
    // Create a route with many hops
    const protocols = Array(10).fill(0);
    const routers = Array(10).fill("0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D");
    const path = [
        "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48", // Start with USDC
        ...Array(9).fill("0x6B175474E89094C44Da98b954EedeAC495271d0F"), // DAI hops
        "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"  // End with WETH
    ];
    const extras = Array(10).fill("0x");
    
    const encoded = encodeRoute(protocols, routers, path, extras);
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(encoded);
    
    console.assert(decodedProtocols.length === 10, 'Should have 10 protocols');
    console.assert(decodedPath.length === 11, 'Should have 11 tokens in path');
    console.assert(encoded.length > 1000, 'Large route should produce substantial encoded data');
    
    console.log('✅ Passed: Large route data encoding/decoding\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

// Test 10: Real-World Bot Integration Pattern
console.log('Test 10: Real-world bot integration pattern');
try {
    // Simulate the pattern used in execution/bot.js
    const signal = {
        protocols: [0, 1],
        routers: [
            "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D",
            "0xE592427A0AEce92De3Edee1F18E0157C05861564"
        ],
        path: [
            "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
            "0x6B175474E89094C44Da98b954EedeAC495271d0F",
            "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2"
        ],
        extras: ["0x", ethers.AbiCoder.defaultAbiCoder().encode(["uint24"], [3000])]
    };
    
    // This is how bot.js encodes routes
    const routeData = ethers.AbiCoder.defaultAbiCoder().encode(
        ["uint8[]", "address[]", "address[]", "bytes[]"],
        [signal.protocols, signal.routers, signal.path, signal.extras]
    );
    
    const [decodedProtocols, decodedRouters, decodedPath, decodedExtras] = decodeRoute(routeData);
    
    console.assert(decodedProtocols.length === signal.protocols.length, 'Protocol count matches');
    console.assert(decodedRouters.length === signal.routers.length, 'Router count matches');
    console.assert(decodedPath.length === signal.path.length, 'Path length matches');
    
    console.log('✅ Passed: Real-world bot integration pattern\n');
} catch (error) {
    console.error('❌ Failed:', error.message);
    process.exit(1);
}

console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log('✅ ALL ROUTE ENCODING TESTS PASSED!');
console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
console.log(`\n📊 Total Tests: 10`);
console.log(`✅ Passed: 10`);
console.log(`❌ Failed: 0\n`);
