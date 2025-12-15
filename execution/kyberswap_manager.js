require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

/**
 * KyberSwapManager - KyberSwap DEX Aggregator Integration
 * Supports dynamic routing across 14+ chains
 * Best for: Multi-chain routing with rewards
 */
class KyberSwapManager {
    /**
     * Initialize KyberSwap Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = "https://aggregator-api.kyberswap.com";
        this.clientId = process.env.KYBERSWAP_CLIENT_ID || "titan-bot";
        this.chainName = this._getChainName(chainId);
    }
    
    /**
     * Get chain name for KyberSwap API
     */
    _getChainName(chainId) {
        const chainNames = {
            1: "ethereum",
            137: "polygon",
            42161: "arbitrum",
            10: "optimism",
            8453: "base",
            56: "bsc",
            43114: "avalanche",
            250: "fantom",
            59144: "linea",
            534352: "scroll"
        };
        return chainNames[chainId] || "ethereum";
    }
    
    /**
     * Get the best swap quote from KyberSwap
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            // Step 1: Get Route
            const routeUrl = `${this.apiUrl}/${this.chainName}/api/v1/routes`;
            const routeParams = {
                tokenIn: srcToken,
                tokenOut: destToken,
                amountIn: amount,
                saveGas: false,
                gasInclude: true
            };
            
            const routeResponse = await axios.get(routeUrl, { 
                params: routeParams,
                headers: { 'x-client-id': this.clientId }
            });
            
            if (!routeResponse.data || !routeResponse.data.data || !routeResponse.data.data.routeSummary) {
                console.log("⚠️ KyberSwap: No route found");
                return null;
            }
            
            const routeSummary = routeResponse.data.data.routeSummary;
            
            // Step 2: Build Swap Transaction
            const swapUrl = `${this.apiUrl}/${this.chainName}/api/v1/route/build`;
            const swapRequest = {
                routeSummary: routeSummary,
                sender: userAddress,
                recipient: userAddress,
                slippageTolerance: slippageBps, // KyberSwap uses bps
                deadline: Math.floor(Date.now() / 1000) + 1200, // 20 minutes
                source: this.clientId
            };
            
            const swapResponse = await axios.post(swapUrl, swapRequest, {
                headers: { 'x-client-id': this.clientId }
            });
            
            if (!swapResponse.data || !swapResponse.data.data) {
                console.log("⚠️ KyberSwap: Transaction building failed");
                return null;
            }
            
            const txData = swapResponse.data.data;
            
            return {
                to: txData.to,
                data: txData.data,
                value: txData.value || "0",
                estimatedOutput: routeSummary.amountOut,
                gasEstimate: routeSummary.gas || "500000",
                amountOutMin: routeSummary.amountOutMin
            };
            
        } catch (error) {
            console.error(`❌ KyberSwap Error: ${error.message}`);
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
            const routeUrl = `${this.apiUrl}/${this.chainName}/api/v1/routes`;
            const routeParams = {
                tokenIn: srcToken,
                tokenOut: destToken,
                amountIn: amount,
                saveGas: false,
                gasInclude: true
            };
            
            const response = await axios.get(routeUrl, { 
                params: routeParams,
                headers: { 'x-client-id': this.clientId }
            });
            
            if (!response.data || !response.data.data || !response.data.data.routeSummary) {
                return null;
            }
            
            const routeSummary = response.data.data.routeSummary;
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: routeSummary.amountOut,
                estimatedGas: routeSummary.gas || "500000",
                amountOutMin: routeSummary.amountOutMin
            };
            
        } catch (error) {
            console.error(`❌ KyberSwap Quote Error: ${error.message}`);
            return null;
        }
    }
}

module.exports = { KyberSwapManager };
