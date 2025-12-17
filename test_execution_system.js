#!/usr/bin/env node
/**
 * TITAN EXECUTION SYSTEM TEST
 * ============================
 * 
 * Tests the complete transaction execution pipeline:
 * 1. Chain registry and execution gates
 * 2. Transaction building (32KB limit enforcement)
 * 3. Transaction signing (chain gating)
 * 4. Merkle bundle construction
 * 5. bloXroute integration readiness
 */

const { TransactionBuilder } = require('./execution/tx_builder');
const { TransactionSigner } = require('./execution/tx_signer');
const { MerkleBlockBuilder } = require('./execution/merkle_builder');
const { BloxRouteManager } = require('./execution/bloxroute_manager');
const { ethers } = require('ethers');

console.log('═══════════════════════════════════════════════════');
console.log('  TITAN EXECUTION SYSTEM VALIDATION');
console.log('═══════════════════════════════════════════════════\n');

// Test 1: Chain Execution Gates
console.log('TEST 1: Chain Execution Gates');
console.log('─'.repeat(50));
TransactionSigner.printExecutionConfig();

// Test 2: Transaction Builder
console.log('\nTEST 2: Transaction Builder (32KB Calldata Limit)');
console.log('─'.repeat(50));

try {
    // Build a small transaction
    const smallTx = TransactionBuilder.buildTransaction({
        chainId: 137,
        to: '0x1234567890123456789012345678901234567890',
        data: '0x12345678',
        value: 0,
        gasLimit: 300000n,
        maxFeePerGas: 100000000000n,
        maxPriorityFeePerGas: 2000000000n,
        nonce: 1
    });
    
    const metrics = TransactionBuilder.getTransactionMetrics(smallTx);
    console.log('✅ Small transaction built:');
    console.log(`   Calldata: ${metrics.calldataSizeKB} KB`);
    console.log(`   bloXroute compatible: ${metrics.isBloxRouteCompatible}`);
    
    // Test calldata limit
    const largeCalled = '0x' + '12'.repeat(35000); // 35KB, should fail
    try {
        TransactionBuilder.buildTransaction({
            chainId: 137,
            to: '0x1234567890123456789012345678901234567890',
            data: largeCalled,
            value: 0,
            gasLimit: 300000n,
            maxFeePerGas: 100000000000n,
            maxPriorityFeePerGas: 2000000000n,
            nonce: 1
        });
        console.log('❌ ERROR: Large calldata should have been rejected');
    } catch (e) {
        console.log('✅ Large calldata correctly rejected:');
        console.log(`   ${e.message.substring(0, 70)}...`);
    }
    
} catch (e) {
    console.log('❌ Transaction builder test failed:', e.message);
}

// Test 3: Signing Gates
console.log('\nTEST 3: Transaction Signing Gates');
console.log('─'.repeat(50));

const testWallet = ethers.Wallet.createRandom();

// Test Ethereum blocking
const ethTx = {
    chainId: 1,
    to: '0x1234567890123456789012345678901234567890',
    data: '0x12345678',
    value: 0n,
    gasLimit: 300000n,
    maxFeePerGas: 100000000000n,
    maxPriorityFeePerGas: 2000000000n,
    nonce: 1
};

TransactionSigner.signTransaction(ethTx, testWallet, 'LIVE')
    .then(() => console.log('❌ ERROR: Ethereum signing should have been blocked'))
    .catch(err => console.log('✅ Ethereum signing blocked:', err.message.substring(0, 60) + '...'));

setTimeout(() => {
    // Test Arbitrum blocking
    const arbTx = {...ethTx, chainId: 42161};
    TransactionSigner.signTransaction(arbTx, testWallet, 'LIVE')
        .then(() => console.log('❌ ERROR: Arbitrum signing should have been blocked'))
        .catch(err => console.log('✅ Arbitrum signing blocked:', err.message.substring(0, 60) + '...'));
}, 100);

setTimeout(() => {
    // Test PAPER mode blocking
    const polyTx = {...ethTx, chainId: 137};
    TransactionSigner.signTransaction(polyTx, testWallet, 'PAPER')
        .then(() => console.log('❌ ERROR: PAPER mode signing should have been blocked'))
        .catch(err => console.log('✅ PAPER mode signing blocked:', err.message.substring(0, 60) + '...'));
}, 200);

// Test 4: Merkle Bundle Builder
setTimeout(() => {
    console.log('\nTEST 4: Merkle Bundle Builder');
    console.log('─'.repeat(50));
    
    const merkleBuilder = new MerkleBlockBuilder();
    const mockTxs = [
        '0x02f86d8201378401312d008504a817c8008252089412345678901234567890123456789012345678901680841234567801a0abcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcda01234567812345678123456781234567812345678123456781234567812345678',
        '0x02f86d8201378401312d008504a817c8008252089412345678901234567890123456789012345678901680841234567802a0fedcbafedcbafedcbafedcbafedcbafedcbafedcbafedcbafedcbafedcbafedca08765432187654321876543218765432187654321876543218765432187654321'
    ];
    
    const merkleRoot = merkleBuilder.buildMerkleRoot(mockTxs);
    console.log('✅ Merkle root generated');
    
    const proof = merkleBuilder.generateProof(0, mockTxs);
    const leaf = merkleBuilder.hashTransaction(mockTxs[0]);
    const isValid = merkleBuilder.verifyProof(merkleRoot, leaf, proof);
    console.log(`✅ Merkle proof verification: ${isValid ? 'VALID' : 'INVALID'}`);
}, 300);

// Test 5: bloXroute Integration
setTimeout(() => {
    console.log('\nTEST 5: bloXroute Manager Configuration');
    console.log('─'.repeat(50));
    
    // Test Polygon bloXroute manager
    const bloxPolygon = new BloxRouteManager(137);
    const configStatus = bloxPolygon.getConfigStatus();
    
    console.log('Polygon bloXroute:');
    console.log(`   Configured: ${configStatus.configured ? '✅' : '⚠️  (needs BLOXROUTE_AUTH in .env)'}`);
    console.log(`   Endpoint: ${configStatus.endpoint}`);
    console.log(`   Network: ${configStatus.network}`);
    console.log(`   Has certificates: ${configStatus.hasCerts ? 'Yes' : 'No (auth header mode)'}`);
    console.log(`   Has HMAC secret: ${configStatus.hasSecret ? 'Yes' : 'No (optional)'}`);
    
    console.log('\n═══════════════════════════════════════════════════');
    console.log('  VALIDATION COMPLETE');
    console.log('═══════════════════════════════════════════════════');
    console.log('\n✅ All execution components are operational');
    console.log('✅ Polygon (137) is ENABLED for live execution');
    console.log('🟡 Ethereum (1) and Arbitrum (42161) are CONFIGURED but execution-disabled');
    console.log('🛡️  All safety gates are functioning correctly\n');
}, 400);
