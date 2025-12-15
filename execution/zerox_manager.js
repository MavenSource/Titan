require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

/**
 * ZeroXManager - 0x/Matcha DEX Aggregator Integration
 * Supports multi-chain routing and limit orders
 * Best for: Multi-chain routing and limit orders
 */
class ZeroXManager {
    /**
     * Initialize 0x Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = this._getApiUrl(chainId);
        this.apiKey = process.env.ZEROX_API_KEY || "";
    }
    
    /**
     * Get API URL for specific chain
     */
    _getApiUrl(chainId) {
        const baseUrls = {
            1: "https://api.0x.org", // Ethereum
            137: "https://polygon.api.0x.org", // Polygon
            42161: "https://arbitrum.api.0x.org", // Arbitrum
            10: "https://optimism.api.0x.org", // Optimism
            8453: "https://base.api.0x.org", // Base
            56: "https://bsc.api.0x.org", // BSC
            43114: "https://avalanche.api.0x.org" // Avalanche
        };
        return baseUrls[chainId] || "https://api.0x.org";
    }
    
    /**
     * Get the best swap quote from 0x
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            const swapUrl = `${this.apiUrl}/swap/v1/quote`;
            const params = {
                buyToken: destToken,
                sellToken: srcToken,
                sellAmount: amount,
                takerAddress: userAddress,
                slippagePercentage: slippageBps / 10000, // Convert bps to decimal (100 bps = 0.01)
                skipValidation: false,
                enableSlippageProtection: true
            };
            
            const headers = this.apiKey ? { '0x-api-key': this.apiKey } : {};
            const response = await axios.get(swapUrl, { 
                params: params,
                headers: headers
            });
            
            if (!response.data || !response.data.to) {
                console.log("⚠️ 0x: No route found");
                return null;
            }
            
            const data = response.data;
            
            return {
                to: data.to,
                data: data.data,
                value: data.value || "0",
                estimatedOutput: data.buyAmount,
                gasEstimate: data.estimatedGas || data.gas || "500000",
                price: data.price,
                guaranteedPrice: data.guaranteedPrice,
                sources: data.sources || []
            };
            
        } catch (error) {
            console.error(`❌ 0x Error: ${error.message}`);
            if (error.response) {
                console.error(`Response: ${JSON.stringify(error.response.data)}`);
            }
            return null;
        }
    }
    
    /**
     * Get a quote without building transaction (faster)
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @returns {Promise<object|null>} Quote data or null if failed
     */
    async getQuote(srcToken, destToken, amount) {
        try {
            const priceUrl = `${this.apiUrl}/swap/v1/price`;
            const params = {
                buyToken: destToken,
                sellToken: srcToken,
                sellAmount: amount
            };
            
            const headers = this.apiKey ? { '0x-api-key': this.apiKey } : {};
            const response = await axios.get(priceUrl, { 
                params: params,
                headers: headers
            });
            
            if (!response.data || !response.data.buyAmount) {
                return null;
            }
            
            const data = response.data;
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: data.buyAmount,
                estimatedGas: data.estimatedGas || data.gas || "500000",
                price: data.price,
                sources: data.sources || []
            };
            
        } catch (error) {
            console.error(`❌ 0x Quote Error: ${error.message}`);
            return null;
        }
    }
}

module.exports = { ZeroXManager };
