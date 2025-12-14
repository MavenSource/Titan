require('dotenv').config();
const { ethers } = require('ethers');

/**
 * GasManager - EIP-1559 Gas Fee Optimization Engine
 * Manages dynamic gas pricing for optimal transaction execution
 */
class GasManager {
    /**
     * Initialize Gas Manager for a specific chain
     * @param {ethers.Provider} provider - Ethers JSON-RPC provider
     * @param {number} chainId - EIP-155 Chain ID
     */
    constructor(provider, chainId) {
        if (!provider || !chainId) {
            throw new Error("GasManager requires provider and chainId");
        }
        
        this.provider = provider;
        this.chainId = chainId;
        
        // Configuration per chain
        this.config = this._getChainConfig(chainId);
        
        // Gas cost database (empirically measured)
        this.GAS_COSTS = {
            FLASH_LOAN_OVERHEAD: 150000,      // Balancer/Aave flash loan setup
            UNIV3_SWAP: 120000,               // Uniswap V3 swap
            UNIV2_SWAP: 90000,                // Uniswap V2 fork swap
            CURVE_SWAP: 90000,                // Curve stable swap
            BALANCER_SWAP: 100000,            // Balancer V2 swap
            PARASWAP: 180000,                 // ParaSwap aggregator
            REPAYMENT: 100000,                // Flash loan repayment
            COMPLEXITY_BUFFER: 50000,         // Extra buffer for complex routes (3+ hops)
            MAX_FALLBACK_GAS: 800000          // Maximum conservative estimate
        };
        
        // NEW: Strategy-specific gas optimization settings
        this.gasStrategy = process.env.GAS_STRATEGY || 'ADAPTIVE'; // ADAPTIVE, FAST, SAFE
        this.mevGasMultiplier = parseFloat(process.env.MEV_GAS_MULTIPLIER) || 1.5;
        this.batchGasDiscount = 0.95; // 5% discount for batch operations
    }
    
    /**
     * Get chain-specific gas configuration
     * @param {number} chainId - Chain ID
     * @returns {object} Gas configuration
     */
    _getChainConfig(chainId) {
        const configs = {
            1: { // Ethereum
                name: "Ethereum",
                maxPriorityFee: 3, // 3 Gwei
                gasLimitMultiplier: 1.2,
                supportsEIP1559: true
            },
            137: { // Polygon
                name: "Polygon",
                maxPriorityFee: 50, // 50 Gwei
                gasLimitMultiplier: 1.2,
                supportsEIP1559: true
            },
            42161: { // Arbitrum
                name: "Arbitrum",
                maxPriorityFee: 0.1, // 0.1 Gwei
                gasLimitMultiplier: 1.15,
                supportsEIP1559: true
            },
            10: { // Optimism
                name: "Optimism",
                maxPriorityFee: 0.001, // 0.001 Gwei
                gasLimitMultiplier: 1.15,
                supportsEIP1559: true
            }
        };
        
        return configs[chainId] || {
            name: "Unknown",
            maxPriorityFee: 2,
            gasLimitMultiplier: 1.2,
            supportsEIP1559: true
        };
    }
    
    /**
     * Get dynamic gas fees based on network conditions
     * @param {string} speed - "SLOW", "STANDARD", or "RAPID"
     * @returns {Promise<object>} Gas fee object {maxFeePerGas, maxPriorityFeePerGas}
     */
    async getDynamicGasFees(speed = "STANDARD") {
        try {
            // Fetch current base fee from latest block
            const feeData = await this.provider.getFeeData();
            
            if (!this.config.supportsEIP1559 || !feeData.maxFeePerGas) {
                // Fallback to legacy gas price for non-EIP1559 chains
                return {
                    gasPrice: feeData.gasPrice
                };
            }
            
            // EIP-1559 Logic
            const baseFee = feeData.maxFeePerGas;
            
            // Priority fee based on speed
            let priorityFeeGwei;
            switch (speed) {
                case "SLOW":
                    priorityFeeGwei = this.config.maxPriorityFee * 0.5;
                    break;
                case "RAPID":
                    priorityFeeGwei = this.config.maxPriorityFee * 2;
                    break;
                default: // STANDARD
                    priorityFeeGwei = this.config.maxPriorityFee;
            }
            
            const priorityFee = ethers.parseUnits(priorityFeeGwei.toString(), "gwei");
            
            // Max fee = (baseFee * 2) + priorityFee (allows for base fee increase)
            const maxFee = (baseFee * 2n) + priorityFee;
            
            return {
                maxFeePerGas: maxFee,
                maxPriorityFeePerGas: priorityFee
            };
            
        } catch (error) {
            console.error(`⚠️ Gas Fee Fetch Error: ${error.message}`);
            
            // Fallback to safe defaults
            const fallbackPriority = ethers.parseUnits(
                this.config.maxPriorityFee.toString(), 
                "gwei"
            );
            const fallbackMax = ethers.parseUnits("100", "gwei"); // 100 Gwei cap
            
            return {
                maxFeePerGas: fallbackMax,
                maxPriorityFeePerGas: fallbackPriority
            };
        }
    }
    
    /**
     * Estimate gas limit with safety buffer
     * @param {object} txRequest - Transaction request object
     * @param {object} routeInfo - Route information for intelligent fallback (optional)
     * @returns {Promise<bigint>} Safe gas limit
     */
    async estimateGasWithBuffer(txRequest, routeInfo = null) {
        try {
            // Try actual gas estimation first
            const estimate = await this.provider.estimateGas(txRequest);
            
            // Apply safety multiplier
            const safeGasLimit = (estimate * BigInt(Math.floor(this.config.gasLimitMultiplier * 100))) / 100n;
            
            console.log(`✅ Gas estimated: ${estimate.toString()} (with buffer: ${safeGasLimit.toString()})`);
            return safeGasLimit;
            
        } catch (error) {
            console.error(`⚠️ Gas Estimation Failed: ${error.message}`);
            
            // INTELLIGENT FALLBACK: Calculate based on route complexity
            const fallbackGas = this._calculateFallbackGas(routeInfo);
            
            console.log(`📊 Using intelligent fallback: ${fallbackGas.toString()} gas`);
            return fallbackGas;
        }
    }
    
    /**
     * Calculate fallback gas estimate based on route complexity
     * @param {object} routeInfo - Route information (protocols, routers, etc.)
     * @returns {bigint} Estimated gas limit
     */
    _calculateFallbackGas(routeInfo) {
        let totalGas = this.GAS_COSTS.FLASH_LOAN_OVERHEAD;
        
        if (!routeInfo || !routeInfo.protocols) {
            // No route info - use maximum conservative estimate
            console.warn('⚠️ No route info provided, using maximum estimate');
            return BigInt(this.GAS_COSTS.MAX_FALLBACK_GAS);
        }
        
        // Add gas for each protocol in the route
        const protocols = routeInfo.protocols || [];
        
        for (let i = 0; i < protocols.length; i++) {
            const protocolId = protocols[i];
            
            switch (protocolId) {
                case 1: // Uniswap V3
                    totalGas += this.GAS_COSTS.UNIV3_SWAP;
                    console.log(`   Protocol ${i+1}: UniV3 (+${this.GAS_COSTS.UNIV3_SWAP} gas)`);
                    break;
                case 2: // Curve
                    totalGas += this.GAS_COSTS.CURVE_SWAP;
                    console.log(`   Protocol ${i+1}: Curve (+${this.GAS_COSTS.CURVE_SWAP} gas)`);
                    break;
                case 3: // Balancer V2
                    totalGas += this.GAS_COSTS.BALANCER_SWAP;
                    console.log(`   Protocol ${i+1}: Balancer (+${this.GAS_COSTS.BALANCER_SWAP} gas)`);
                    break;
                case 4: // ParaSwap
                    totalGas += this.GAS_COSTS.PARASWAP;
                    console.log(`   Protocol ${i+1}: ParaSwap (+${this.GAS_COSTS.PARASWAP} gas)`);
                    break;
                default:
                    // Unknown protocol - use conservative estimate
                    totalGas += this.GAS_COSTS.UNIV3_SWAP;
                    console.log(`   Protocol ${i+1}: Unknown (+${this.GAS_COSTS.UNIV3_SWAP} gas)`);
            }
        }
        
        // Add repayment overhead
        totalGas += this.GAS_COSTS.REPAYMENT;
        
        // Add extra buffer for complex routes (3+ hops)
        if (protocols.length >= 3) {
            totalGas += this.GAS_COSTS.COMPLEXITY_BUFFER;
            console.log(`   Added complexity buffer: +${this.GAS_COSTS.COMPLEXITY_BUFFER} gas`);
        }
        
        console.log(`   Base gas: ${totalGas}`);
        
        // Apply safety multiplier
        const safeGas = Math.floor(totalGas * this.config.gasLimitMultiplier);
        console.log(`   With ${this.config.gasLimitMultiplier}x multiplier: ${safeGas}`);
        
        return BigInt(safeGas);
    }
    
    /**
     * Calculate total transaction cost in native token units
     * @param {bigint} gasLimit - Gas limit for transaction
     * @param {bigint} maxFeePerGas - Max fee per gas (wei)
     * @returns {bigint} Total cost in wei
     */
    calculateTxCost(gasLimit, maxFeePerGas) {
        return gasLimit * maxFeePerGas;
    }
    
    /**
     * Estimate gas cost in USD
     * @param {bigint} gasLimit - Gas limit for transaction
     * @param {bigint} gasPrice - Gas price (wei)
     * @param {number} ethPriceUsd - ETH price in USD (default: 2000)
     * @returns {number} Estimated cost in USD
     */
    estimateGasCostUSD(gasLimit, gasPrice, ethPriceUsd = 2000) {
        const gasCostWei = gasLimit * gasPrice;
        const gasCostEth = Number(ethers.formatEther(gasCostWei));
        return gasCostEth * ethPriceUsd;
    }
    
    /**
     * Check if current gas prices are acceptable for trading
     * @param {number} maxGweiThreshold - Maximum acceptable gas price in Gwei
     * @returns {Promise<boolean>} True if gas is acceptable
     */
    async isGasAcceptable(maxGweiThreshold = 100) {
        const feeData = await this.provider.getFeeData();
        const currentGasPrice = feeData.gasPrice || feeData.maxFeePerGas;
        
        const currentGwei = Number(ethers.formatUnits(currentGasPrice, "gwei"));
        
        return currentGwei <= maxGweiThreshold;
    }

    /**
     * Helper to apply gas multiplier to base value
     * Supports multipliers with up to 4 decimal places precision
     * @private
     */
    _applyGasMultiplier(baseValue, multiplier) {
        if (!baseValue) return undefined;
        // Scale by 10000 to support multipliers like 1.5555 (4 decimal places)
        const multiplierScaled = BigInt(Math.round(multiplier * 10000));
        return (baseValue * multiplierScaled) / 10000n;
    }

    /**
     * NEW: Calculate optimal gas for MEV strategies
     * Different strategies have different timing requirements and gas needs
     * @param {string} strategy - Strategy type: SANDWICH, BATCH_MERKLE, JIT_LIQUIDITY, STANDARD
     * @param {number} blockNumber - Target block number
     * @returns {Promise<object>} Strategy-optimized gas parameters
     */
    async calculateMEVGas(strategy, blockNumber = null) {
        console.log(`⛽ Calculating MEV gas for strategy: ${strategy}`);
        
        // Get base gas estimation
        const baseGas = await this.getDynamicGasFees('STANDARD');
        
        // Apply strategy-specific adjustments
        switch(strategy) {
            case 'SANDWICH':
                // Front-run needs high priority to guarantee position
                return {
                    maxPriorityFeePerGas: this._applyGasMultiplier(baseGas.maxPriorityFeePerGas || baseGas.gasPrice, this.mevGasMultiplier),
                    maxFeePerGas: this._applyGasMultiplier(baseGas.maxFeePerGas, 1.10),
                    gasPrice: this._applyGasMultiplier(baseGas.gasPrice, 1.50),
                    gasLimit: null, // Will be estimated separately
                    reason: 'High priority for frontrunning'
                };
                
            case 'BATCH_MERKLE':
                // Batches are less time-sensitive and save gas
                return {
                    maxPriorityFeePerGas: this._applyGasMultiplier(baseGas.maxPriorityFeePerGas, 0.95),
                    maxFeePerGas: baseGas.maxFeePerGas,
                    gasPrice: this._applyGasMultiplier(baseGas.gasPrice, 0.95),
                    gasLimit: null, // Batches use less gas per trade
                    reason: 'Lower priority acceptable for batches'
                };
                
            case 'JIT_LIQUIDITY':
                // JIT needs to land before target TX but not extreme priority
                return {
                    maxPriorityFeePerGas: this._applyGasMultiplier(baseGas.maxPriorityFeePerGas, 1.20),
                    maxFeePerGas: this._applyGasMultiplier(baseGas.maxFeePerGas, 1.10),
                    gasPrice: this._applyGasMultiplier(baseGas.gasPrice, 1.20),
                    gasLimit: null,
                    reason: 'Medium-high priority for JIT timing'
                };
                
            case 'STANDARD':
            default:
                // Standard arbitrage - normal priority
                return baseGas;
        }
    }

    /**
     * NEW: Get gas strategy based on network conditions
     * Dynamically adjusts between SAFE, ADAPTIVE, and FAST based on profit margin
     * @param {number} expectedProfitUSD - Expected profit in USD
     * @param {number} estimatedGasCostUSD - Estimated gas cost in USD
     * @returns {string} Recommended strategy: SAFE, ADAPTIVE, or FAST
     */
    getRecommendedStrategy(expectedProfitUSD, estimatedGasCostUSD) {
        const profitMargin = expectedProfitUSD - estimatedGasCostUSD;
        const marginPercent = (profitMargin / expectedProfitUSD) * 100;
        
        if (marginPercent < 10) {
            // Tight margin - use SAFE to avoid overpaying
            console.log(`💡 Tight margin (${marginPercent.toFixed(1)}%) - Recommending SAFE strategy`);
            return 'SAFE';
        } else if (marginPercent > 50) {
            // Large margin - can afford FAST for better execution
            console.log(`💡 Large margin (${marginPercent.toFixed(1)}%) - Recommending FAST strategy`);
            return 'FAST';
        } else {
            // Medium margin - use ADAPTIVE
            console.log(`💡 Medium margin (${marginPercent.toFixed(1)}%) - Recommending ADAPTIVE strategy`);
            return 'ADAPTIVE';
        }
    }

    /**
     * NEW: Calculate batch-optimized gas limit
     * Batches use significantly less gas per trade
     * @param {number} tradeCount - Number of trades in batch
     * @returns {bigint} Optimized gas limit for batch
     */
    calculateBatchGasLimit(tradeCount) {
        if (tradeCount <= 0) return BigInt(300000);
        
        // Batch: Base overhead + per-trade cost
        const batchBaseGas = 150000;
        const perTradeGas = 1500;
        const estimatedGas = batchBaseGas + (tradeCount * perTradeGas);
        
        // Add safety buffer
        const safeGasLimit = Math.floor(estimatedGas * this.config.gasLimitMultiplier);
        
        console.log(`⛽ Batch Gas: ${tradeCount} trades = ${safeGasLimit.toLocaleString()} gas`);
        
        return BigInt(safeGasLimit);
    }
}

module.exports = { GasManager };
