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
            REPAYMENT: 100000                 // Flash loan repayment
        };
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
            return BigInt(800000); // Maximum for complex multi-hop
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
        
        // Apply safety multiplier
        const safeGas = Math.floor(totalGas * this.config.gasLimitMultiplier);
        
        // Add extra buffer for complex routes (3+ hops)
        if (protocols.length >= 3) {
            const complexityBuffer = 50000;
            totalGas += complexityBuffer;
            console.log(`   Added complexity buffer: +${complexityBuffer} gas`);
        }
        
        console.log(`   Base gas: ${totalGas}`);
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
}

module.exports = { GasManager };
