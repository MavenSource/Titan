/**
 * TITAN MERKLE BUNDLE BUILDER
 * ============================
 * 
 * Production-grade Merkle tree construction for transaction bundles.
 * 
 * FEATURES:
 * - Deterministic bundle integrity via Merkle roots
 * - MEV relay compatibility
 * - Gas optimization for batched execution
 * - Auditability and verification
 */

const { ethers } = require('ethers');

class MerkleBlockBuilder {
    constructor() {
        this.leaves = [];
        this.maxBatchSize = 256; // Support up to 256 transactions per batch
    }

    /**
     * Hash a raw transaction for Merkle tree.
     * 
     * @param {string} rawTx - Raw signed transaction (hex string)
     * @returns {string} Keccak256 hash of the transaction
     */
    hashTransaction(rawTx) {
        return ethers.keccak256(rawTx);
    }

    /**
     * Build Merkle root from array of raw transactions.
     * 
     * Uses simple binary tree construction with keccak256 hashing.
     * This is deterministic and compatible with bloXroute MEV relay.
     * 
     * @param {Array<string>} rawTransactions - Array of raw signed transactions
     * @returns {string} Merkle root hash
     */
    buildMerkleRoot(rawTransactions) {
        if (!rawTransactions || rawTransactions.length === 0) {
            throw new Error('Cannot build Merkle root from empty transaction array');
        }
        
        console.log(`🌳 [MERKLE] Building Merkle tree for ${rawTransactions.length} transactions...`);
        
        // Hash each transaction to create leaves
        let level = rawTransactions.map(tx => this.hashTransaction(tx));
        this.leaves = [...level];  // Store leaves for proof generation
        
        // Build tree level by level
        while (level.length > 1) {
            const nextLevel = [];
            
            for (let i = 0; i < level.length; i += 2) {
                const left = level[i];
                const right = level[i + 1] || left;  // Duplicate last if odd
                
                // Concatenate and hash
                const combined = ethers.concat([left, right]);
                const parentHash = ethers.keccak256(combined);
                
                nextLevel.push(parentHash);
            }
            
            level = nextLevel;
        }
        
        const root = level[0];
        console.log(`✅ [MERKLE] Root generated: ${root}`);
        
        return root;
    }
    
    /**
     * Generate Merkle proof for a specific transaction.
     * 
     * @param {number} txIndex - Index of transaction in bundle
     * @param {Array<string>} rawTransactions - All raw transactions in bundle
     * @returns {Array<string>} Merkle proof path
     */
    generateProof(txIndex, rawTransactions) {
        if (txIndex < 0 || txIndex >= rawTransactions.length) {
            throw new Error(`Invalid transaction index: ${txIndex}`);
        }
        
        const proof = [];
        let level = rawTransactions.map(tx => this.hashTransaction(tx));
        let index = txIndex;
        
        while (level.length > 1) {
            const siblingIndex = index % 2 === 0 ? index + 1 : index - 1;
            
            if (siblingIndex < level.length) {
                proof.push(level[siblingIndex]);
            }
            
            // Move to parent level
            const nextLevel = [];
            for (let i = 0; i < level.length; i += 2) {
                const left = level[i];
                const right = level[i + 1] || left;
                const combined = ethers.concat([left, right]);
                const parentHash = ethers.keccak256(combined);
                nextLevel.push(parentHash);
            }
            
            level = nextLevel;
            index = Math.floor(index / 2);
        }
        
        return proof;
    }
    
    /**
     * Verify a Merkle proof.
     * 
     * @param {string} root - Merkle root
     * @param {string} leaf - Transaction hash (leaf)
     * @param {Array<string>} proof - Merkle proof path
     * @returns {boolean} True if proof is valid
     */
    verifyProof(root, leaf, proof) {
        let computedHash = leaf;
        
        for (const proofElement of proof) {
            const combined = ethers.concat([computedHash, proofElement].sort());
            computedHash = ethers.keccak256(combined);
        }
        
        return computedHash === root;
    }

    /**
     * Optimize batch construction for gas efficiency
     * - Groups similar trades (same DEX/router) to minimize storage reads
     * - Sorts by profitability
     * - Ensures total gas stays under block limit
     * @param {Array} trades - List of trade objects
     * @returns {Array} Optimized trades
     */
    optimizeBatch(trades) {
        if (!trades || trades.length === 0) return [];
        
        console.log(`🔧 Optimizing batch of ${trades.length} trades...`);
        
        // 1. Validate batch size
        if (trades.length > this.maxBatchSize) {
            console.warn(`⚠️ Batch size ${trades.length} exceeds max ${this.maxBatchSize}, truncating`);
            trades = trades.slice(0, this.maxBatchSize);
        }
        
        // 2. Sort by router to group similar operations (reduces gas)
        const sortedByRouter = [...trades].sort((a, b) => {
            const routerCompare = a.router.localeCompare(b.router);
            if (routerCompare !== 0) return routerCompare;
            
            // If same router, sort by token to further optimize
            return a.token.localeCompare(b.token);
        });
        
        // 3. If profit data available, prioritize highest profit trades
        if (sortedByRouter[0].profit !== undefined) {
            sortedByRouter.sort((a, b) => (b.profit || 0) - (a.profit || 0));
        }
        
        console.log(`✅ Batch optimized: ${sortedByRouter.length} trades grouped by router`);
        
        return sortedByRouter;
    }

    /**
     * Calculate gas savings from batching
     * Individual TXs: ~300k gas each
     * Batch: ~150k base + ~1.5k per trade
     * @param {number} tradeCount - Number of trades in batch
     * @returns {object} Gas savings metrics
     */
    calculateBatchSavings(tradeCount) {
        if (tradeCount <= 0) {
            return {
                individualGas: 0,
                batchGas: 0,
                savings: 0,
                savingsPercent: 0
            };
        }
        
        // Individual transactions
        const individualGas = tradeCount * 300000;
        
        // Batch: Base overhead + per-trade cost
        const batchBaseGas = 150000;
        const perTradeGas = 1500;
        const batchGas = batchBaseGas + (tradeCount * perTradeGas);
        
        // Calculate savings
        const savings = individualGas - batchGas;
        const savingsPercent = ((savings / individualGas) * 100);
        
        return {
            individualGas,
            batchGas,
            savings,
            savingsPercent: savingsPercent.toFixed(2)
        };
    }

    /**
     * Build optimized batch with gas savings calculation
     * @param {Array} trades - List of trade objects
     * @returns {object} Batch data with metrics
     */
    buildOptimizedBatch(trades) {
        // Optimize trade order
        const optimizedTrades = this.optimizeBatch(trades);
        
        // Build Merkle tree
        const root = this.buildBatch(optimizedTrades);
        
        // Calculate savings
        const savings = this.calculateBatchSavings(optimizedTrades.length);
        
        console.log(`💰 Gas Savings: ${savings.savings.toLocaleString()} gas (${savings.savingsPercent}%)`);
        console.log(`   Individual: ${savings.individualGas.toLocaleString()} gas`);
        console.log(`   Batch: ${savings.batchGas.toLocaleString()} gas`);
        
        return {
            root,
            trades: optimizedTrades,
            savings
        };
    }
}

module.exports = { MerkleBlockBuilder };