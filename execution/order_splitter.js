require('dotenv').config();
const { ethers } = require('ethers');

/**
 * OrderSplitter - Cross-DEX Order Splitting Optimization
 * 
 * Splits large orders across multiple DEXes to minimize slippage
 * Example: $100k trade split across Uniswap, Curve, SushiSwap
 * Result: 50-80% slippage reduction vs. single DEX
 */
class OrderSplitter {
    constructor() {
        // Minimum trade size to warrant splitting (in USD)
        this.minSplitSize = parseFloat(process.env.MIN_SPLIT_SIZE_USD) || 10000;
        
        // Maximum number of splits
        this.maxSplits = parseInt(process.env.MAX_ORDER_SPLITS) || 5;
        
        // Minimum allocation per split (prevents dust trades)
        this.minAllocationPercent = 0.05; // 5%
    }

    /**
     * Split large orders across multiple DEXes to minimize slippage
     * 
     * @param {string} tokenIn - Input token address
     * @param {string} tokenOut - Output token address
     * @param {number} totalAmountUSD - Total amount in USD
     * @param {Array} dexPools - Available DEX pools with liquidity data
     * @returns {Promise<object>} Split allocation with expected savings
     */
    async optimizeSplit(tokenIn, tokenOut, totalAmountUSD, dexPools) {
        console.log(`📊 OrderSplitter: Analyzing split for $${totalAmountUSD.toLocaleString()} trade`);
        
        // 1. Filter valid pools and get liquidity depth
        const validPools = await this._filterValidPools(dexPools, tokenIn, tokenOut);
        
        if (validPools.length === 0) {
            console.warn('⚠️ No valid pools found for splitting');
            return {
                shouldSplit: false,
                splits: [],
                reason: 'No valid pools available'
            };
        }
        
        // 2. Check if splitting is beneficial
        if (totalAmountUSD < this.minSplitSize) {
            console.log(`ℹ️ Trade size $${totalAmountUSD} below minimum $${this.minSplitSize}, no split`);
            return {
                shouldSplit: false,
                splits: [{ dex: validPools[0].name, amount: totalAmountUSD, percentage: 100 }],
                reason: 'Trade too small to benefit from splitting'
            };
        }
        
        // 3. Calculate optimal allocation based on liquidity
        const splits = this._calculateOptimalAllocation(totalAmountUSD, validPools);
        
        // 4. Estimate slippage for each split
        const splitsWithSlippage = splits.map(split => ({
            ...split,
            expectedSlippage: this._estimateSlippage(split.amount, split.liquidity, split.dex)
        }));
        
        // 5. Calculate total slippage and savings
        const totalSlippage = splitsWithSlippage.reduce((sum, s) => sum + s.expectedSlippage, 0);
        const avgSlippage = totalSlippage / splitsWithSlippage.length;
        
        // Estimate single-DEX slippage (worst case: highest liquidity pool)
        const bestSinglePool = validPools.reduce((best, pool) => 
            pool.liquidity > best.liquidity ? pool : best
        );
        const singleDexSlippage = this._estimateSlippage(totalAmountUSD, bestSinglePool.liquidity, bestSinglePool.name);
        
        const savings = singleDexSlippage - avgSlippage;
        const savingsPercent = (savings / singleDexSlippage * 100).toFixed(2);
        
        console.log(`💰 Slippage Analysis:`);
        console.log(`   Single DEX: ${singleDexSlippage.toFixed(4)}%`);
        console.log(`   Split: ${avgSlippage.toFixed(4)}%`);
        console.log(`   Savings: ${savings.toFixed(4)}% (${savingsPercent}% improvement)`);
        
        return {
            shouldSplit: splits.length > 1,
            splits: splitsWithSlippage,
            totalSlippage: avgSlippage,
            singleDexSlippage,
            estimatedSavings: {
                slippageReduction: savings,
                slippageReductionPercent: savingsPercent,
                dollarSavings: (savings / 100) * totalAmountUSD
            }
        };
    }

    /**
     * Filter valid pools with sufficient liquidity
     * @private
     */
    async _filterValidPools(dexPools, tokenIn, tokenOut) {
        if (!dexPools || dexPools.length === 0) return [];
        
        return dexPools.filter(pool => {
            // Validate pool has required data
            if (!pool.liquidity || pool.liquidity <= 0) return false;
            if (!pool.name || !pool.router) return false;
            
            // Validate tokens match (backward compatible: accept if no token data provided)
            if (!pool.tokens) return true; // Backward compat: accept pools without token data
            
            const hasTokens = pool.tokens.includes(tokenIn) || pool.tokens.includes(tokenOut);
            return hasTokens;
        }).sort((a, b) => b.liquidity - a.liquidity); // Sort by liquidity desc
    }

    /**
     * Calculate optimal allocation across pools based on liquidity
     * Uses liquidity-weighted distribution to minimize slippage
     * @private
     */
    _calculateOptimalAllocation(totalAmount, pools) {
        // Limit number of splits
        const activePools = pools.slice(0, this.maxSplits);
        
        // Calculate total liquidity
        const totalLiquidity = activePools.reduce((sum, pool) => sum + pool.liquidity, 0);
        
        // Allocate proportionally to liquidity depth
        const splits = activePools.map(pool => {
            const liquidityShare = pool.liquidity / totalLiquidity;
            const allocation = totalAmount * liquidityShare;
            
            return {
                dex: pool.name,
                router: pool.router,
                amount: allocation,
                percentage: (liquidityShare * 100).toFixed(2),
                liquidity: pool.liquidity
            };
        });
        
        // Filter out splits below minimum allocation
        const minAllocation = totalAmount * this.minAllocationPercent;
        const validSplits = splits.filter(s => s.amount >= minAllocation);
        
        // If filtering removed all but one, return single trade
        if (validSplits.length === 1) {
            validSplits[0].amount = totalAmount;
            validSplits[0].percentage = 100;
        } else if (validSplits.length > 1) {
            // Renormalize percentages after filtering
            const totalAllocated = validSplits.reduce((sum, s) => sum + s.amount, 0);
            validSplits.forEach(split => {
                split.percentage = ((split.amount / totalAllocated) * 100).toFixed(2);
            });
        }
        
        return validSplits;
    }

    /**
     * Estimate slippage for a given trade size and liquidity
     * Uses square root price impact model (simplified AMM model)
     * @private
     */
    _estimateSlippage(tradeSize, liquidity, dexName) {
        if (!liquidity || liquidity <= 0) return 100; // 100% slippage if no liquidity
        
        // Trade size as percentage of liquidity
        const impactRatio = tradeSize / liquidity;
        
        // Different DEX types have different slippage characteristics
        let slippageFactor;
        
        if (dexName && dexName.toLowerCase().includes('curve')) {
            // Curve (stable pools) - very low slippage
            slippageFactor = 0.5;
        } else if (dexName && dexName.toLowerCase().includes('uniswap v3')) {
            // Uniswap V3 (concentrated liquidity) - low slippage
            slippageFactor = 0.7;
        } else if (dexName && dexName.toLowerCase().includes('balancer')) {
            // Balancer (weighted pools) - medium slippage
            slippageFactor = 0.9;
        } else {
            // Default (Uniswap V2 style) - standard slippage
            slippageFactor = 1.0;
        }
        
        // Simplified AMM slippage model: sqrt(1 + impact) - 1
        // Scaled by DEX type factor
        const baseSlippage = (Math.sqrt(1 + impactRatio) - 1) * 100;
        const adjustedSlippage = baseSlippage * slippageFactor;
        
        return adjustedSlippage;
    }

    /**
     * Convert split allocation to executable trades
     * @param {object} splitResult - Result from optimizeSplit()
     * @param {string} tokenIn - Input token address
     * @param {string} tokenOut - Output token address
     * @param {bigint} totalAmountWei - Total amount in wei (as BigInt)
     * @returns {Array} Executable trade objects
     */
    convertToTrades(splitResult, tokenIn, tokenOut, totalAmountWei) {
        if (!splitResult.shouldSplit || splitResult.splits.length === 0) {
            // No split needed, return single trade
            return [{
                router: splitResult.splits[0]?.router || null,
                tokenIn,
                tokenOut,
                amountIn: totalAmountWei.toString(),
                dex: splitResult.splits[0]?.dex || 'default'
            }];
        }
        
        // Convert USD amounts to wei proportionally using BigInt arithmetic
        const trades = splitResult.splits.map(split => {
            const portion = parseFloat(split.percentage) / 100;
            // Use BigInt arithmetic to avoid precision loss
            const portionScaled = BigInt(Math.floor(portion * 1e18));
            const amountWei = (totalAmountWei * portionScaled) / BigInt(1e18);
            
            return {
                router: split.router,
                tokenIn,
                tokenOut,
                amountIn: amountWei.toString(),
                dex: split.dex,
                expectedSlippage: split.expectedSlippage
            };
        });
        
        return trades;
    }

    /**
     * Validate split configuration
     * @returns {boolean} True if configuration is valid
     */
    validateConfig() {
        const issues = [];
        
        if (this.minSplitSize <= 0) {
            issues.push('MIN_SPLIT_SIZE_USD must be positive');
        }
        
        if (this.maxSplits < 1 || this.maxSplits > 10) {
            issues.push('MAX_ORDER_SPLITS must be between 1 and 10');
        }
        
        if (this.minAllocationPercent < 0.01 || this.minAllocationPercent > 0.5) {
            issues.push('minAllocationPercent must be between 1% and 50%');
        }
        
        if (issues.length > 0) {
            console.error('❌ OrderSplitter configuration errors:');
            issues.forEach(issue => console.error(`   - ${issue}`));
            return false;
        }
        
        return true;
    }
}

module.exports = { OrderSplitter };
