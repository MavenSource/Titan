require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

/**
 * OpenOceanManager - OpenOcean DEX Aggregator Integration
 * Supports 30+ chains with intelligent split routing
 * Best for: Best price discovery across 30+ chains
 */
class OpenOceanManager {
    /**
     * Initialize OpenOcean Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = "https://open-api.openocean.finance/v3";
        this.apiKey = process.env.OPENOCEAN_API_KEY || "";
        this.chainName = this._getChainName(chainId);
    }
    
    /**
     * Get chain name for OpenOcean API
     */
    _getChainName(chainId) {
        const chainNames = {
            1: "eth",
            137: "polygon",
            42161: "arbitrum",
            10: "optimism",
            8453: "base",
            56: "bsc",
            43114: "avax",
            250: "fantom",
            100: "xdai",
            42220: "celo",
            1284: "moonbeam",
            1285: "moonriver",
            25: "cronos",
            1313161554: "aurora"
        };
        return chainNames[chainId] || "eth";
    }
    
    /**
     * Get the best swap quote from OpenOcean
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            const swapUrl = `${this.apiUrl}/${this.chainName}/swap_quote`;
            const params = {
                inTokenAddress: srcToken,
                outTokenAddress: destToken,
                amount: amount,
                gasPrice: "5", // Will be overridden by bot
                slippage: slippageBps / 100, // Convert bps to percentage
                account: userAddress
            };
            
            const headers = this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {};
            const response = await axios.get(swapUrl, { 
                params: params,
                headers: headers
            });
            
            if (!response.data || !response.data.data) {
                console.log("⚠️ OpenOcean: No route found");
                return null;
            }
            
            const data = response.data.data;
            
            return {
                to: data.to,
                data: data.data,
                value: data.value || "0",
                estimatedOutput: data.outAmount,
                gasEstimate: data.estimatedGas || "500000",
                minOutAmount: data.minOutAmount,
                path: data.path || []
            };
            
        } catch (error) {
            console.error(`❌ OpenOcean Error: ${error.message}`);
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
            const quoteUrl = `${this.apiUrl}/${this.chainName}/quote`;
            const params = {
                inTokenAddress: srcToken,
                outTokenAddress: destToken,
                amount: amount,
                gasPrice: "5"
            };
            
            const headers = this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {};
            const response = await axios.get(quoteUrl, { 
                params: params,
                headers: headers
            });
            
            if (!response.data || !response.data.data) {
                return null;
            }
            
            const data = response.data.data;
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: data.outAmount,
                estimatedGas: data.estimatedGas || "500000",
                minOutAmount: data.minOutAmount,
                path: data.path || []
            };
            
        } catch (error) {
            console.error(`❌ OpenOcean Quote Error: ${error.message}`);
            return null;
        }
    }
}

module.exports = { OpenOceanManager };
