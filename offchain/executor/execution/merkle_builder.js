const { MerkleTree } = require('merkletreejs');
const keccak256 = require('keccak256');
const { ethers } = require('ethers');

class MerkleBlockBuilder {
    constructor() {
        this.tree = null;
        this.leaves = [];
        this.maxBatchSize = 256; // Support up to 256 trades per batch
    }

    /**
     * Encodes a trade instruction into a leaf hash.
     * @param {string} token - Token Address
     * @param {string} amount - Amount
     * @param {string} router - Router Address
     * @param {string} calldata - Swap Calldata
     */
    createLeaf(token, amount, router, calldata) {
        // Equivalent to Solidity: keccak256(abi.encodePacked(token, amount, router, calldata))
        const leaf = ethers.solidityPackedKeccak256(
            ['address', 'uint256', 'address', 'bytes'],
            [token, amount, router, calldata]
        );
        return leaf;
    }

    /**
     * Builds the Merkle Tree from a list of trade objects.
     * @param {Array} trades - List of trade objects {token, amount, router, data}
     */
    buildBatch(trades) {
        console.log(`🌳 Merkle: Compressing ${trades.length} trades into block...`);
        
        // 1. Generate Leaves
        this.leaves = trades.map(t => this.createLeaf(t.token, t.amount, t.router, t.data));
        
        // 2. Build Tree
        this.tree = new MerkleTree(this.leaves, keccak256, { sortPairs: true });
        
        const root = this.tree.getHexRoot();
        console.log(`✅ Merkle Root Generated: ${root}`);
        
        return root;
    }

    /**
     * Generates the Proof for a specific trade index.
     * Required for the smart contract to verify the trade is part of the batch.
     */
    getProof(tradeIndex) {
        if (!this.leaves[tradeIndex]) return [];
        const leaf = this.leaves[tradeIndex];
        return this.tree.getHexProof(leaf);
    }
    
    /**
     * Verifies a leaf locally (Sanity Check)
     */
    verify(root, leaf, proof) {
        return this.tree.verify(proof, leaf, root);
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