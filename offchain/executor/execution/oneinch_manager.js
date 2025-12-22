require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

/**
 * OneInchManager - 1inch DEX Aggregator Integration
 * Uses 1inch Pathfinder for optimal routing across multiple DEXs
 * Best for: Fast single-chain arbitrage (<1s execution)
 */
class OneInchManager {
    /**
     * Initialize 1inch Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = "https://api.1inch.dev/swap/v6.0";
        this.apiKey = process.env.ONEINCH_API_KEY || "";
        this.referrerAddress = process.env.ONEINCH_REFERRER_ADDRESS || "0x0000000000000000000000000000000000000000";
    }
    
    /**
     * Get the best swap quote from 1inch
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            // Step 1: Get Quote
            const quoteUrl = `${this.apiUrl}/${this.chainId}/quote`;
            const quoteParams = {
                src: srcToken,
                dst: destToken,
                amount: amount
            };
            
            const headers = this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {};
            const quoteResponse = await axios.get(quoteUrl, { 
                params: quoteParams,
                headers: headers
            });
            
            if (!quoteResponse.data || !quoteResponse.data.dstAmount) {
                console.log("⚠️ 1inch: No route found");
                return null;
            }
            
            const estimatedOutput = quoteResponse.data.dstAmount;
            
            // Step 2: Get Swap Transaction
            const swapUrl = `${this.apiUrl}/${this.chainId}/swap`;
            const swapParams = {
                src: srcToken,
                dst: destToken,
                amount: amount,
                from: userAddress,
                slippage: slippageBps / 100, // Convert bps to percentage
                referrer: this.referrerAddress,
                disableEstimate: false,
                allowPartialFill: false
            };
            
            const swapResponse = await axios.get(swapUrl, { 
                params: swapParams,
                headers: headers
            });
            
            if (!swapResponse.data || !swapResponse.data.tx) {
                console.log("⚠️ 1inch: Transaction building failed");
                return null;
            }
            
            const txData = swapResponse.data.tx;
            
            return {
                to: txData.to,
                data: txData.data,
                value: txData.value || "0",
                estimatedOutput: estimatedOutput,
                gasEstimate: txData.gas || "500000",
                protocols: swapResponse.data.protocols || []
            };
            
        } catch (error) {
            console.error(`❌ 1inch Error: ${error.message}`);
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
            const quoteUrl = `${this.apiUrl}/${this.chainId}/quote`;
            const quoteParams = {
                src: srcToken,
                dst: destToken,
                amount: amount
            };
            
            const headers = this.apiKey ? { 'Authorization': `Bearer ${this.apiKey}` } : {};
            const quoteResponse = await axios.get(quoteUrl, { 
                params: quoteParams,
                headers: headers
            });
            
            if (!quoteResponse.data || !quoteResponse.data.dstAmount) {
                return null;
            }
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: quoteResponse.data.dstAmount,
                estimatedGas: quoteResponse.data.estimatedGas || "500000",
                protocols: quoteResponse.data.protocols || []
            };
            
        } catch (error) {
            console.error(`❌ 1inch Quote Error: ${error.message}`);
            return null;
        }
    }
}

module.exports = { OneInchManager };
