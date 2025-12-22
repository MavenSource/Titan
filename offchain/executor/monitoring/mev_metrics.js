/**
 * MEVMetrics - Performance Tracking for MEV Strategies
 * 
 * Tracks:
 * - Merkle batch executions and gas savings
 * - Order splitting performance
 * - JIT liquidity opportunities
 * - MEV bundle submissions
 */
class MEVMetrics {
    constructor() {
        this.metrics = {
            merkleBatches: {
                executed: 0,
                tradesPerBatch: [],
                gasPerBatch: [],
                savingsTotal: 0,
                avgTradesPerBatch: 0,
                avgGasSaved: 0
            },
            orderSplitting: {
                tradesOptimized: 0,
                slippageSaved: 0,
                avgSlippageSavings: 0,
                dollarSavings: 0
            },
            jitLiquidity: {
                opportunitiesFound: 0,
                executed: 0,
                totalFees: 0,
                avgFees: 0,
                successRate: 0
            },
            mevBundles: {
                submitted: 0,
                included: 0,
                rejected: 0,
                inclusionRate: 0
            }
        };
        
        // Start time for tracking
        this.startTime = Date.now();
    }

    /**
     * Record Merkle batch execution
     * @param {number} tradeCount - Number of trades in batch
     * @param {number} gasUsed - Actual gas used
     * @param {number} gasSaved - Gas saved vs individual TXs
     */
    recordMerkleBatch(tradeCount, gasUsed, gasSaved) {
        this.metrics.merkleBatches.executed++;
        this.metrics.merkleBatches.tradesPerBatch.push(tradeCount);
        this.metrics.merkleBatches.gasPerBatch.push(gasUsed);
        this.metrics.merkleBatches.savingsTotal += gasSaved;
        
        // Calculate averages
        this.metrics.merkleBatches.avgTradesPerBatch = 
            this.metrics.merkleBatches.tradesPerBatch.reduce((sum, t) => sum + t, 0) / 
            this.metrics.merkleBatches.executed;
        
        this.metrics.merkleBatches.avgGasSaved = 
            this.metrics.merkleBatches.savingsTotal / 
            this.metrics.merkleBatches.executed;
        
        console.log(`📊 Merkle Batch #${this.metrics.merkleBatches.executed}: ${tradeCount} trades, saved ${gasSaved.toLocaleString()} gas`);
    }

    /**
     * Record order splitting optimization
     * @param {number} slippageSaved - Slippage percentage saved
     * @param {number} dollarAmount - Trade size in USD
     */
    recordOrderSplit(slippageSaved, dollarAmount) {
        this.metrics.orderSplitting.tradesOptimized++;
        this.metrics.orderSplitting.slippageSaved += slippageSaved;
        
        const dollarSavings = (slippageSaved / 100) * dollarAmount;
        this.metrics.orderSplitting.dollarSavings += dollarSavings;
        
        this.metrics.orderSplitting.avgSlippageSavings = 
            this.metrics.orderSplitting.slippageSaved / 
            this.metrics.orderSplitting.tradesOptimized;
        
        console.log(`📊 Order Split: Saved ${slippageSaved.toFixed(4)}% slippage ($${dollarSavings.toFixed(2)})`);
    }

    /**
     * Record JIT liquidity opportunity
     * @param {boolean} executed - Whether opportunity was executed
     * @param {number} feesEarned - LP fees earned (if executed)
     */
    recordJITOpportunity(executed, feesEarned = 0) {
        this.metrics.jitLiquidity.opportunitiesFound++;
        
        if (executed) {
            this.metrics.jitLiquidity.executed++;
            this.metrics.jitLiquidity.totalFees += feesEarned;
            this.metrics.jitLiquidity.avgFees = 
                this.metrics.jitLiquidity.totalFees / 
                this.metrics.jitLiquidity.executed;
        }
        
        this.metrics.jitLiquidity.successRate = 
            (this.metrics.jitLiquidity.executed / this.metrics.jitLiquidity.opportunitiesFound) * 100;
        
        console.log(`📊 JIT: ${executed ? 'Executed' : 'Found'}, Fees: $${feesEarned.toFixed(2)}`);
    }

    /**
     * Record MEV bundle submission
     * @param {boolean} included - Whether bundle was included
     */
    recordMEVBundle(included) {
        this.metrics.mevBundles.submitted++;
        
        if (included) {
            this.metrics.mevBundles.included++;
        } else {
            this.metrics.mevBundles.rejected++;
        }
        
        this.metrics.mevBundles.inclusionRate = 
            (this.metrics.mevBundles.included / this.metrics.mevBundles.submitted) * 100;
        
        console.log(`📊 MEV Bundle: ${included ? 'Included' : 'Rejected'}`);
    }

    /**
     * Generate comprehensive report
     * @returns {object} Complete metrics report
     */
    generateReport() {
        const uptimeHours = (Date.now() - this.startTime) / (1000 * 60 * 60);
        
        return {
            uptime: {
                hours: uptimeHours.toFixed(2),
                startTime: new Date(this.startTime).toISOString()
            },
            summary: {
                totalMEVProfit: this.metrics.jitLiquidity.totalFees,
                totalGasSaved: this.metrics.merkleBatches.savingsTotal,
                totalSlippageSaved: this.metrics.orderSplitting.dollarSavings
            },
            merkleBatches: {
                ...this.metrics.merkleBatches,
                perHour: (this.metrics.merkleBatches.executed / uptimeHours).toFixed(2)
            },
            orderSplitting: {
                ...this.metrics.orderSplitting,
                avgSlippageSavingsPercent: this.metrics.orderSplitting.avgSlippageSavings.toFixed(4),
                perHour: (this.metrics.orderSplitting.tradesOptimized / uptimeHours).toFixed(2)
            },
            jitLiquidity: {
                ...this.metrics.jitLiquidity,
                successRatePercent: this.metrics.jitLiquidity.successRate.toFixed(2),
                opportunitiesPerHour: (this.metrics.jitLiquidity.opportunitiesFound / uptimeHours).toFixed(2)
            },
            mevBundles: {
                ...this.metrics.mevBundles,
                inclusionRatePercent: this.metrics.mevBundles.inclusionRate.toFixed(2)
            }
        };
    }

    /**
     * Print formatted report to console
     */
    printReport() {
        const report = this.generateReport();
        
        console.log('\n╔═══════════════════════════════════════════════════════════╗');
        console.log('║           TITAN MEV PERFORMANCE REPORT                  ║');
        console.log('╚═══════════════════════════════════════════════════════════╝');
        console.log(`\n⏱️  Uptime: ${report.uptime.hours} hours`);
        console.log(`📅 Started: ${report.uptime.startTime}\n`);
        
        console.log('💰 SUMMARY:');
        console.log(`   Total MEV Profit: $${report.summary.totalMEVProfit.toFixed(2)}`);
        console.log(`   Total Gas Saved: ${report.summary.totalGasSaved.toLocaleString()} gas`);
        console.log(`   Total Slippage Saved: $${report.summary.totalSlippageSaved.toFixed(2)}\n`);
        
        console.log('🌳 MERKLE BATCHES:');
        console.log(`   Executed: ${report.merkleBatches.executed}`);
        console.log(`   Avg Trades/Batch: ${report.merkleBatches.avgTradesPerBatch.toFixed(1)}`);
        console.log(`   Avg Gas Saved: ${report.merkleBatches.avgGasSaved.toLocaleString()} gas`);
        console.log(`   Rate: ${report.merkleBatches.perHour}/hour\n`);
        
        console.log('📊 ORDER SPLITTING:');
        console.log(`   Trades Optimized: ${report.orderSplitting.tradesOptimized}`);
        console.log(`   Avg Slippage Savings: ${report.orderSplitting.avgSlippageSavingsPercent}%`);
        console.log(`   Dollar Savings: $${report.orderSplitting.dollarSavings.toFixed(2)}`);
        console.log(`   Rate: ${report.orderSplitting.perHour}/hour\n`);
        
        console.log('⚡ JIT LIQUIDITY:');
        console.log(`   Opportunities Found: ${report.jitLiquidity.opportunitiesFound}`);
        console.log(`   Executed: ${report.jitLiquidity.executed}`);
        console.log(`   Success Rate: ${report.jitLiquidity.successRatePercent}%`);
        console.log(`   Total Fees: $${report.jitLiquidity.totalFees.toFixed(2)}`);
        console.log(`   Avg Fees: $${report.jitLiquidity.avgFees.toFixed(2)}`);
        console.log(`   Rate: ${report.jitLiquidity.opportunitiesPerHour}/hour\n`);
        
        console.log('📦 MEV BUNDLES:');
        console.log(`   Submitted: ${report.mevBundles.submitted}`);
        console.log(`   Included: ${report.mevBundles.included}`);
        console.log(`   Rejected: ${report.mevBundles.rejected}`);
        console.log(`   Inclusion Rate: ${report.mevBundles.inclusionRatePercent}%\n`);
        
        console.log('═══════════════════════════════════════════════════════════\n');
    }

    /**
     * Export metrics as JSON
     * @returns {string} JSON string of metrics
     */
    exportJSON() {
        return JSON.stringify(this.generateReport(), null, 2);
    }

    /**
     * Reset all metrics
     */
    reset() {
        this.metrics = {
            merkleBatches: {
                executed: 0,
                tradesPerBatch: [],
                gasPerBatch: [],
                savingsTotal: 0,
                avgTradesPerBatch: 0,
                avgGasSaved: 0
            },
            orderSplitting: {
                tradesOptimized: 0,
                slippageSaved: 0,
                avgSlippageSavings: 0,
                dollarSavings: 0
            },
            jitLiquidity: {
                opportunitiesFound: 0,
                executed: 0,
                totalFees: 0,
                avgFees: 0,
                successRate: 0
            },
            mevBundles: {
                submitted: 0,
                included: 0,
                rejected: 0,
                inclusionRate: 0
            }
        };
        
        this.startTime = Date.now();
        console.log('📊 MEV metrics reset');
    }
}

module.exports = { MEVMetrics };
