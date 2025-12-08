require('dotenv').config();
const axios = require('axios');

/**
 * ParaSwapManager - DEX Aggregator Integration
 * Finds best swap routes across multiple DEXs using ParaSwap API
 */
class ParaSwapManager {
    /**
     * Initialize ParaSwap Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = "https://apiv5.paraswap.io";
        this.partnerAddress = process.env.PARASWAP_PARTNER_ADDRESS || "0x0000000000000000000000000000000000000000";
    }
    
    /**
     * Get the best swap quote from ParaSwap
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress) {
        try {
            // Step 1: Get Price Quote
            const priceUrl = `${this.apiUrl}/prices`;
            const priceParams = {
                srcToken: srcToken,
                destToken: destToken,
                amount: amount,
                srcDecimals: 18, // Should be fetched dynamically in production
                destDecimals: 18,
                side: "SELL",
                network: this.chainId,
                partner: this.partnerAddress
            };
            
            const priceResponse = await axios.get(priceUrl, { params: priceParams });
            
            if (!priceResponse.data || !priceResponse.data.priceRoute) {
                console.log("⚠️ ParaSwap: No route found");
                return null;
            }
            
            const priceRoute = priceResponse.data.priceRoute;
            
            // Step 2: Build Transaction
            const txUrl = `${this.apiUrl}/transactions/${this.chainId}`;
            const txParams = {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: priceRoute.destAmount,
                priceRoute: priceRoute,
                userAddress: userAddress,
                partner: this.partnerAddress,
                slippage: 100 // 1% slippage (in basis points)
            };
            
            const txResponse = await axios.post(txUrl, txParams);
            
            if (!txResponse.data) {
                console.log("⚠️ ParaSwap: Transaction building failed");
                return null;
            }
            
            const txData = txResponse.data;
            
            return {
                to: txData.to,
                data: txData.data,
                value: txData.value || "0",
                estimatedOutput: priceRoute.destAmount,
                gasEstimate: txData.gas || "500000"
            };
            
        } catch (error) {
            console.error(`❌ ParaSwap Error: ${error.message}`);
            if (error.response) {
                console.error(`Response: ${JSON.stringify(error.response.data)}`);
            }
            return null;
        }
    }
    
    /**
     * Get token decimals (helper function)
     * @param {string} tokenAddress - Token contract address
     * @returns {Promise<number>} Token decimals
     */
    async getTokenDecimals(tokenAddress) {
        if (!this.provider) {
            return 18; // Default
        }
        
        try {
            const tokenContract = new ethers.Contract(
                tokenAddress,
                ['function decimals() view returns (uint8)'],
                this.provider
            );
            return await tokenContract.decimals();
        } catch (error) {
            return 18; // Default fallback
        }
    }
}

module.exports = { ParaSwapManager };
