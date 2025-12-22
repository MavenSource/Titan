require('dotenv').config();
const axios = require('axios');

/**
 * JupiterManager - Jupiter Aggregator Integration for Solana
 * Best-in-class routing for Solana ecosystem
 * Best for: Solana ecosystem arbitrage
 */
class JupiterManager {
    /**
     * Initialize Jupiter Manager
     * Note: Only works on Solana (chainId is ignored, kept for consistency)
     */
    constructor(chainId = null, provider = null) {
        this.apiUrl = "https://quote-api.jup.ag/v6";
        this.solanaRpcUrl = process.env.SOLANA_RPC_URL || "https://api.mainnet-beta.solana.com";
    }
    
    /**
     * Get the best swap quote from Jupiter
     * @param {string} srcToken - Source token mint address (Solana)
     * @param {string} destToken - Destination token mint address (Solana)
     * @param {string} amount - Amount to swap (in lamports/smallest unit)
     * @param {string} userAddress - User Solana wallet address
     * @param {number} slippageBps - Slippage in basis points (default: 100 = 1%)
     * @returns {Promise<object|null>} Swap data or null if failed
     */
    async getBestSwap(srcToken, destToken, amount, userAddress, slippageBps = 100) {
        try {
            // Step 1: Get Quote
            const quoteUrl = `${this.apiUrl}/quote`;
            const quoteParams = {
                inputMint: srcToken,
                outputMint: destToken,
                amount: amount,
                slippageBps: slippageBps,
                onlyDirectRoutes: false,
                asLegacyTransaction: false
            };
            
            const quoteResponse = await axios.get(quoteUrl, { params: quoteParams });
            
            if (!quoteResponse.data) {
                console.log("⚠️ Jupiter: No route found");
                return null;
            }
            
            const quote = quoteResponse.data;
            
            // Step 2: Get Swap Transaction
            const swapUrl = `${this.apiUrl}/swap`;
            const swapRequest = {
                quoteResponse: quote,
                userPublicKey: userAddress,
                wrapAndUnwrapSol: true,
                dynamicComputeUnitLimit: true,
                prioritizationFeeLamports: "auto"
            };
            
            const swapResponse = await axios.post(swapUrl, swapRequest);
            
            if (!swapResponse.data || !swapResponse.data.swapTransaction) {
                console.log("⚠️ Jupiter: Transaction building failed");
                return null;
            }
            
            return {
                swapTransaction: swapResponse.data.swapTransaction, // Base64 encoded transaction
                estimatedOutput: quote.outAmount,
                priceImpactPct: quote.priceImpactPct,
                routePlan: quote.routePlan || [],
                otherAmountThreshold: quote.otherAmountThreshold
            };
            
        } catch (error) {
            console.error(`❌ Jupiter Error: ${error.message}`);
            if (error.response) {
                console.error(`Response: ${JSON.stringify(error.response.data)}`);
            }
            return null;
        }
    }
    
    /**
     * Get a quote without building transaction
     * @param {string} srcToken - Source token mint address
     * @param {string} destToken - Destination token mint address
     * @param {string} amount - Amount to swap
     * @returns {Promise<object|null>} Quote data or null if failed
     */
    async getQuote(srcToken, destToken, amount) {
        try {
            const quoteUrl = `${this.apiUrl}/quote`;
            const quoteParams = {
                inputMint: srcToken,
                outputMint: destToken,
                amount: amount,
                slippageBps: 100,
                onlyDirectRoutes: false
            };
            
            const response = await axios.get(quoteUrl, { params: quoteParams });
            
            if (!response.data) {
                return null;
            }
            
            const quote = response.data;
            
            return {
                srcToken: srcToken,
                destToken: destToken,
                srcAmount: amount,
                destAmount: quote.outAmount,
                priceImpactPct: quote.priceImpactPct,
                routePlan: quote.routePlan || []
            };
            
        } catch (error) {
            console.error(`❌ Jupiter Quote Error: ${error.message}`);
            return null;
        }
    }
}

module.exports = { JupiterManager };
