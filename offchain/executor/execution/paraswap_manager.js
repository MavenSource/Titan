require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

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
    constructor(chainId, provider = null, slippageBps = 100) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = "https://apiv5.paraswap.io";
        this.partnerAddress = process.env.PARASWAP_PARTNER_ADDRESS || "0x0000000000000000000000000000000000000000";
        this.slippageBps = slippageBps; // Slippage tolerance in basis points (100 bps = 1%)
    }
    
    /**
     * Get the best swap quote from ParaSwap
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Optional slippage override in basis points (default: uses constructor value)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = null) {
        try {
            // Fetch token decimals dynamically
            const srcDecimals = await this.getTokenDecimals(srcToken);
            const destDecimals = await this.getTokenDecimals(destToken);
            
            // Step 1: Get Price Quote
            const priceUrl = `${this.apiUrl}/prices`;
            const priceParams = {
                srcToken: srcToken,
                destToken: destToken,
                amount: amount,
                srcDecimals: srcDecimals,
                destDecimals: destDecimals,
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
                slippage: slippageBps !== null ? slippageBps : this.slippageBps
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
                // Use ParaSwap's gas estimate or conservative fallback for complex multi-protocol routes
                // 500k covers most scenarios including multi-hop swaps through aggregators
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
