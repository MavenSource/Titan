require('dotenv').config();
const { OneInchManager } = require('./oneinch_manager');
const { ZeroXManager } = require('./zerox_manager');
const { CoWSwapManager } = require('./cowswap_manager');
const { OpenOceanManager } = require('./openocean_manager');
const { KyberSwapManager } = require('./kyberswap_manager');
const { RangoManager } = require('./rango_manager');
const { JupiterManager } = require('./jupiter_manager');
const { LifiExecutionEngine } = require('./lifi_manager');

/**
 * AggregatorSelector - Intelligent routing to optimal DEX aggregator
 * Routes trades to the best aggregator based on trade characteristics
 */
class AggregatorSelector {
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        
        // Initialize all managers
        this.managers = {
            ONEINCH: new OneInchManager(chainId, provider),
            ZEROX: new ZeroXManager(chainId, provider),
            COWSWAP: new CoWSwapManager(chainId, provider),
            OPENOCEAN: new OpenOceanManager(chainId, provider),
            KYBERSWAP: new KyberSwapManager(chainId, provider),
            RANGO: new RangoManager(chainId, provider),
            JUPITER: new JupiterManager(chainId, provider),
            LIFI: LifiExecutionEngine // Static methods
        };
        
        // Configuration
        this.config = {
            HIGH_VALUE_THRESHOLD: parseFloat(process.env.HIGH_VALUE_THRESHOLD_USD || '1000'),
            COWSWAP_MIN_VALUE: parseFloat(process.env.COWSWAP_MIN_VALUE_USD || '1000'),
            SPEED_CRITICAL_CHAINS: [137, 42161, 10], // Polygon, Arbitrum, Optimism
            RANGO_EXOTIC_CHAINS: [59144, 534352, 5000], // Linea, Scroll, Mantle
            PARALLEL_QUOTE_TIMEOUT: parseInt(process.env.PARALLEL_QUOTE_TIMEOUT || '5000'),
            ENABLE_PARALLEL_QUOTES: this._parseBooleanEnv(process.env.ENABLE_PARALLEL_QUOTES || 'true'),
            MIN_QUOTE_COMPARISON_COUNT: parseInt(process.env.MIN_QUOTE_COMPARISON_COUNT || '3')
        };
        
        // Aggregator preferences from env
        this.aggregatorPreference = (process.env.AGGREGATOR_PREFERENCE || 'auto').toLowerCase().split(',');
    }
    
    /**
     * Parse boolean environment variables safely
     */
    _parseBooleanEnv(value) {
        if (!value) return false;
        const normalized = value.toLowerCase().trim();
        return normalized === 'true' || normalized === '1' || normalized === 'yes';
    }
    
    /**
     * Select the optimal aggregator for a trade
     * @param {object} trade - Trade parameters
     * @returns {string} Aggregator name
     */
    selectOptimalAggregator(trade) {
        // If user specified preference, honor it (unless auto)
        if (this.aggregatorPreference[0] !== 'auto' && this.aggregatorPreference.length > 0) {
            return this.aggregatorPreference[0].toUpperCase();
        }
        
        // 1. Solana trades → Jupiter (ONLY option)
        if (trade.chain === 'solana' || trade.chainId === 'solana') {
            return 'JUPITER';
        }
        
        // 2. High-value trades ($1000+) → CoW Swap (MEV protection)
        if (trade.valueUSD && trade.valueUSD >= this.config.COWSWAP_MIN_VALUE) {
            return 'COWSWAP';
        }
        
        // 3. Cross-chain (70+ chains) → Rango > LiFi
        if (trade.isCrossChain) {
            if (trade.needsExoticChains || this.config.RANGO_EXOTIC_CHAINS.includes(trade.chainId)) {
                return 'RANGO';
            }
            return 'LIFI'; // Intent-based bridging
        }
        
        // 4. Speed-critical (<1s) → 1inch (Pathfinder)
        if (trade.priority === 'SPEED' || this.config.SPEED_CRITICAL_CHAINS.includes(trade.chainId)) {
            return 'ONEINCH';
        }
        
        // 5. Multi-chain price discovery → OpenOcean
        if (trade.needsBestPrice && trade.chains && trade.chains > 15) {
            return 'OPENOCEAN';
        }
        
        // 6. Limit orders → 0x/Matcha
        if (trade.isLimitOrder) {
            return 'ZEROX';
        }
        
        // 7. Multi-chain with rewards → KyberSwap
        if (trade.needsRewards) {
            return 'KYBERSWAP';
        }
        
        // 8. Default: 1inch for best general performance
        return 'ONEINCH';
    }
    
    /**
     * Execute a trade using the optimal aggregator with fallback
     * @param {object} trade - Trade parameters
     * @returns {Promise<object|null>} Execution result
     */
    async executeTrade(trade) {
        const primary = this.selectOptimalAggregator(trade);
        
        console.log(`🎯 Selected aggregator: ${primary}`);
        
        try {
            return await this._executeWithAggregator(primary, trade);
        } catch (error) {
            console.error(`❌ ${primary} execution failed:`, error.message);
            return await this.fallbackExecution(trade, primary);
        }
    }
    
    /**
     * Execute with a specific aggregator
     */
    async _executeWithAggregator(aggregator, trade) {
        const manager = this.managers[aggregator];
        
        if (!manager) {
            throw new Error(`Aggregator ${aggregator} not available`);
        }
        
        // Cross-chain trades use different method
        if (trade.isCrossChain && aggregator === 'LIFI') {
            return await LifiExecutionEngine.bridgeAssets(
                trade.source_chain,
                trade.dest_chain,
                trade.token,
                trade.dest_token || trade.token,
                trade.amount,
                {
                    order: 'FASTEST',
                    slippage: 0.005,
                    preferIntentBased: true
                }
            );
        }
        
        // Regular swap
        return await manager.getBestSwap(
            trade.token,
            trade.destToken || trade.path[0],
            trade.amount,
            trade.userAddress,
            trade.slippageBps || 100
        );
    }
    
    /**
     * Fallback to next best aggregator
     */
    async fallbackExecution(trade, failedAggregator) {
        const fallbackChain = ['ONEINCH', 'OPENOCEAN', 'ZEROX', 'KYBERSWAP'];
        
        for (const aggregator of fallbackChain) {
            if (aggregator === failedAggregator) continue;
            
            console.log(`🔄 Trying fallback: ${aggregator}`);
            
            try {
                const result = await this._executeWithAggregator(aggregator, trade);
                if (result) {
                    console.log(`✅ Fallback successful with ${aggregator}`);
                    return result;
                }
            } catch (error) {
                console.error(`❌ ${aggregator} fallback failed:`, error.message);
                continue;
            }
        }
        
        console.error('❌ All aggregators failed');
        return null;
    }
    
    /**
     * Get quotes from multiple aggregators in parallel
     * @param {object} trade - Trade parameters
     * @returns {Promise<object>} Best quote with aggregator info
     */
    async getMultiAggregatorQuotes(trade) {
        if (!this.config.ENABLE_PARALLEL_QUOTES) {
            // Just use the selected aggregator
            const aggregator = this.selectOptimalAggregator(trade);
            const quote = await this.managers[aggregator].getQuote(
                trade.token,
                trade.destToken || trade.path[0],
                trade.amount
            );
            return { aggregator, quote };
        }
        
        console.log('📊 Fetching quotes from multiple aggregators...');
        
        // Query all aggregators in parallel
        const promises = [
            this._getQuoteWithTimeout('ONEINCH', trade),
            this._getQuoteWithTimeout('ZEROX', trade),
            this._getQuoteWithTimeout('OPENOCEAN', trade),
            this._getQuoteWithTimeout('KYBERSWAP', trade)
        ];
        
        // Don't include CoW for small trades (has fees)
        if (trade.valueUSD && trade.valueUSD >= this.config.HIGH_VALUE_THRESHOLD) {
            promises.push(this._getQuoteWithTimeout('COWSWAP', trade));
        }
        
        const results = await Promise.allSettled(promises);
        const quotes = [];
        
        for (const result of results) {
            if (result.status === 'fulfilled' && result.value && result.value.quote) {
                quotes.push(result.value);
            }
        }
        
        if (quotes.length === 0) {
            console.warn('⚠️ No quotes received from any aggregator');
            return null;
        }
        
        console.log(`✅ Received ${quotes.length} quotes`);
        
        // Select best quote (highest output amount)
        return this.selectBestQuote(quotes);
    }
    
    /**
     * Get quote with timeout
     */
    async _getQuoteWithTimeout(aggregator, trade) {
        return Promise.race([
            (async () => {
                const manager = this.managers[aggregator];
                const quote = await manager.getQuote(
                    trade.token,
                    trade.destToken || trade.path[0],
                    trade.amount
                );
                return { aggregator, quote };
            })(),
            new Promise((_, reject) =>
                setTimeout(() => reject(new Error('Timeout')), this.config.PARALLEL_QUOTE_TIMEOUT)
            )
        ]);
    }
    
    /**
     * Select the best quote from multiple aggregators
     */
    selectBestQuote(quotes) {
        let best = null;
        let bestAmount = BigInt(0);
        
        for (const { aggregator, quote } of quotes) {
            if (!quote || !quote.destAmount) continue;
            
            const amount = BigInt(quote.destAmount);
            
            if (amount > bestAmount) {
                bestAmount = amount;
                best = { aggregator, quote };
            }
        }
        
        if (best) {
            console.log(`🏆 Best quote: ${best.aggregator} with output ${bestAmount.toString()}`);
        }
        
        return best;
    }
}

module.exports = { AggregatorSelector };
