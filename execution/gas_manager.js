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
     * @returns {Promise<bigint>} Safe gas limit
     */
    async estimateGasWithBuffer(txRequest) {
        try {
            const estimate = await this.provider.estimateGas(txRequest);
            
            // Apply safety multiplier
            const buffer = Math.floor(this.config.gasLimitMultiplier * 100) / 100;
            const safeGasLimit = (estimate * BigInt(Math.floor(buffer * 100))) / 100n;
            
            return safeGasLimit;
            
        } catch (error) {
            console.error(`⚠️ Gas Estimation Failed: ${error.message}`);
            
            // Return conservative fallback
            return 500000n; // 500k gas units
        }
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
