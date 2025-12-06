const { ethers } = require('ethers');

/**
 * Gas Manager - EIP-1559 Dynamic Gas Fee Optimization
 * Implements intelligent gas pricing strategies for optimal execution
 */
class GasManager {
    constructor(provider, chainId) {
        this.provider = provider;
        this.chainId = chainId;
        this.gasLimitMultiplier = parseFloat(process.env.GAS_LIMIT_MULTIPLIER || "1.2");
        this.maxPriorityFeeGwei = parseFloat(process.env.MAX_PRIORITY_FEE_GWEI || "50");
    }

    /**
     * Get dynamic gas fees based on strategy
     * @param {string} strategy - 'SLOW', 'STANDARD', 'RAPID'
     * @returns {Promise<Object>} { maxFeePerGas, maxPriorityFeePerGas, gasLimit }
     */
    async getDynamicGasFees(strategy = 'STANDARD') {
        try {
            // Get current base fee from latest block
            const block = await this.provider.getBlock('latest');
            const baseFee = block.baseFeePerGas;
            
            // Calculate priority fee based on strategy
            let priorityFeeGwei;
            switch(strategy) {
                case 'SLOW':
                    priorityFeeGwei = 1.0; // Low priority
                    break;
                case 'RAPID':
                    priorityFeeGwei = Math.min(this.maxPriorityFeeGwei, 5.0); // High priority
                    break;
                case 'STANDARD':
                default:
                    priorityFeeGwei = 2.0; // Medium priority
            }
            
            const priorityFee = ethers.parseUnits(priorityFeeGwei.toString(), 'gwei');
            
            // Max fee = 2 * baseFee + priorityFee (with buffer for volatility)
            const maxFeePerGas = (baseFee * 2n) + priorityFee;
            
            return {
                maxFeePerGas: maxFeePerGas,
                maxPriorityFeePerGas: priorityFee,
                type: 2 // EIP-1559 transaction
            };
        } catch (error) {
            console.error('Error calculating gas fees:', error);
            // Fallback to legacy gas pricing
            const gasPrice = await this.provider.getGasPrice();
            return {
                gasPrice: gasPrice * 120n / 100n, // 20% buffer
                type: 0 // Legacy transaction
            };
        }
    }

    /**
     * Estimate gas limit with safety buffer
     * @param {Object} txRequest - Transaction request object
     * @returns {Promise<bigint>} Estimated gas limit with buffer
     */
    async estimateGasLimit(txRequest) {
        try {
            const estimate = await this.provider.estimateGas(txRequest);
            // Apply safety multiplier (default 1.2x = 20% buffer)
            const buffered = (estimate * BigInt(Math.floor(this.gasLimitMultiplier * 100))) / 100n;
            return buffered;
        } catch (error) {
            console.error('Gas estimation failed:', error);
            // Return a conservative default for complex arbitrage
            return 500000n;
        }
    }

    /**
     * Check if current gas price is favorable for execution
     * @param {number} thresholdGwei - Maximum acceptable gas price
     * @returns {Promise<boolean>} True if gas price is below threshold
     */
    async isGasPriceFavorable(thresholdGwei = 50) {
        try {
            const block = await this.provider.getBlock('latest');
            const baseFee = block.baseFeePerGas;
            const baseFeeGwei = parseFloat(ethers.formatUnits(baseFee, 'gwei'));
            
            return baseFeeGwei < thresholdGwei;
        } catch (error) {
            console.error('Error checking gas price:', error);
            return true; // Proceed if check fails
        }
    }

    /**
     * Calculate total transaction cost in native token
     * @param {bigint} gasLimit - Gas limit for transaction
     * @param {bigint} maxFeePerGas - Max fee per gas unit
     * @returns {string} Transaction cost in ETH/MATIC/etc
     */
    calculateTxCost(gasLimit, maxFeePerGas) {
        const totalCost = gasLimit * maxFeePerGas;
        return ethers.formatEther(totalCost);
    }

    /**
     * Get recommended gas strategy based on network congestion
     * @returns {Promise<string>} 'SLOW', 'STANDARD', or 'RAPID'
     */
    async getRecommendedStrategy() {
        try {
            const block = await this.provider.getBlock('latest');
            const gasUsed = block.gasUsed;
            const gasLimit = block.gasLimit;
            
            // Calculate utilization percentage
            const utilization = (Number(gasUsed) / Number(gasLimit)) * 100;
            
            if (utilization > 90) {
                return 'RAPID'; // Network is congested, need high priority
            } else if (utilization > 70) {
                return 'STANDARD'; // Normal conditions
            } else {
                return 'SLOW'; // Low congestion, can save on fees
            }
        } catch (error) {
            console.error('Error determining strategy:', error);
            return 'STANDARD';
        }
    }
}

module.exports = { GasManager };
