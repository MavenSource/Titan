require('dotenv').config();
const axios = require('axios');
const { ethers } = require('ethers');

/**
 * CoWSwapManager - CoW Protocol Integration
 * Provides MEV protection through batch auctions and solver competition
 * Best for: High-value trades ($1000+) needing MEV protection
 */
class CoWSwapManager {
    /**
     * Initialize CoW Swap Manager
     * @param {number} chainId - EIP-155 Chain ID
     * @param {object} provider - Ethers provider (optional, for validation)
     */
    constructor(chainId, provider = null) {
        this.chainId = chainId;
        this.provider = provider;
        this.apiUrl = this._getApiUrl(chainId);
        this.appCode = process.env.COWSWAP_APP_CODE || "titan-arbitrage";
    }
    
    /**
     * Get API URL for specific chain
     */
    _getApiUrl(chainId) {
        const baseUrls = {
            1: "https://api.cow.fi/mainnet/api/v1", // Ethereum
            100: "https://api.cow.fi/xdai/api/v1", // Gnosis Chain
            42161: "https://api.cow.fi/arbitrum_one/api/v1", // Arbitrum (if supported)
            11155111: "https://api.cow.fi/sepolia/api/v1" // Sepolia testnet
        };
        return baseUrls[chainId] || "https://api.cow.fi/mainnet/api/v1";
    }
    
    /**
     * Get CoW Protocol app data hash
     */
    _getAppData() {
        return ethers.id(this.appCode).slice(0, 66);
    }
    
    /**
     * Get the best swap quote from CoW Protocol
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @param {string} userAddress - User wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            // CoW Protocol uses a different flow: create order -> sign -> submit
            // For simplicity, we'll get a quote here
            const quoteUrl = `${this.apiUrl}/quote`;
            
            const quoteRequest = {
                sellToken: srcToken,
                buyToken: destToken,
                sellAmountBeforeFee: amount,
                from: userAddress,
                receiver: userAddress,
                appData: this._getAppData(), // App identifier
                kind: "sell",
                partiallyFillable: false,
                validTo: Math.floor(Date.now() / 1000) + 600 // 10 minutes
            };
            
            const response = await axios.post(quoteUrl, quoteRequest);
            
            if (!response.data || !response.data.quote) {
                console.log("⚠️ CoW Swap: No quote available");
                return null;
            }
            
            const quote = response.data.quote;
            
            return {
                to: userAddress, // CoW doesn't use direct contract calls
                data: "0x", // Order submission is separate
                value: "0",
                estimatedOutput: quote.buyAmount,
                gasEstimate: "0", // Gasless trades
                feeAmount: quote.feeAmount,
                validTo: quote.validTo,
                quoteId: response.data.id,
                isMEVProtected: true
            };
            
        } catch (error) {
            console.error(`❌ CoW Swap Error: ${error.message}`);
            if (error.response) {
                console.error(`Response: ${JSON.stringify(error.response.data)}`);
            }
            return null;
        }
    }
    
    /**
     * Get a quote without creating an order
     * @param {string} srcToken - Source token address
     * @param {string} destToken - Destination token address
     * @param {string} amount - Amount to swap (in wei as string)
     * @returns {Promise<object|null>} Quote data or null if failed
     */
    async getQuote(srcToken, destToken, amount) {
        try {
            const quoteUrl = `${this.apiUrl}/quote`;
            
            // For quote-only, we can use a dummy address
            const dummyAddress = "0x0000000000000000000000000000000000000001";
            
            const quoteRequest = {
                sellToken: srcToken,
                buyToken: destToken,
                sellAmountBeforeFee: amount,
                from: dummyAddress,
                receiver: dummyAddress,
                appData: this._getAppData(),
                kind: "sell",
                partiallyFillable: false,
                validTo: Math.floor(Date.now() / 1000) + 600
            };
            
            const response = await axios.post(quoteUrl, quoteRequest);
            
            if (!response.data || !response.data.quote) {
                return null;
            }
            
            const quote = response.data.quote;
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: quote.buyAmount,
                estimatedGas: "0", // Gasless
                feeAmount: quote.feeAmount,
                isMEVProtected: true
            };
            
        } catch (error) {
            console.error(`❌ CoW Swap Quote Error: ${error.message}`);
            return null;
        }
    }
}

module.exports = { CoWSwapManager };
