require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

/**
 * RangoManager - Rango Exchange Integration
 * Supports 70+ chains with cross-chain bridge aggregation
 * Best for: Complex cross-chain arbitrage paths
 */
class RangoManager {
    /**
     * Initialize Rango Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = "https://api.rango.exchange";
        this.apiKey = process.env.RANGO_API_KEY || "";
    }
    
    /**
     * Get the best swap quote from Rango
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            // Rango requires specific blockchain identifiers
            const swapUrl = `${this.apiUrl}/basic/swap`;
            const params = {
                from: {
                    blockchain: this._getBlockchainId(this.chainId),
                    symbol: srcToken,
                    address: srcToken
                },
                to: {
                    blockchain: this._getBlockchainId(this.chainId),
                    symbol: destToken,
                    address: destToken
                },
                amount: amount,
                fromAddress: userAddress,
                toAddress: userAddress,
                slippage: slippageBps / 100 // Convert bps to percentage
            };
            
            const headers = this.apiKey ? { 'API-KEY': this.apiKey } : {};
            const response = await axios.post(swapUrl, params, { headers });
            
            if (!response.data || !response.data.route) {
                console.log("⚠️ Rango: No route found");
                return null;
            }
            
            const route = response.data.route;
            
            return {
                to: route.to || userAddress,
                data: route.data || "0x",
                value: route.value || "0",
                estimatedOutput: route.outputAmount || "0",
                gasEstimate: "500000",
                routeId: response.data.requestId
            };
            
        } catch (error) {
            console.error(`❌ Rango Error: ${error.message}`);
            if (error.response) {
                console.error(`Response: ${JSON.stringify(error.response.data)}`);
            }
            return null;
        }
    }
    
    /**
     * Get a quote without building transaction
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @returns {Promise<object|null>} Quote data or null if failed
     */
    async getQuote(srcToken, destToken, amount) {
        try {
            // For now, use the same swap endpoint but extract quote only
            const result = await this.getBestSwap(srcToken, destToken, amount, "0x0000000000000000000000000000000000000001", 100);
            
            if (!result) {
                return null;
            }
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: result.estimatedOutput,
                estimatedGas: "500000"
            };
            
        } catch (error) {
            console.error(`❌ Rango Quote Error: ${error.message}`);
            return null;
        }
    }
    
    /**
     * Get Rango blockchain identifier from chain ID
     */
    _getBlockchainId(chainId) {
        const blockchainIds = {
            1: "ETH",
            137: "POLYGON",
            42161: "ARBITRUM",
            10: "OPTIMISM",
            8453: "BASE",
            56: "BSC",
            43114: "AVAX_CCHAIN",
            250: "FANTOM"
        };
        return blockchainIds[chainId] || "ETH";
    }
}

module.exports = { RangoManager };
