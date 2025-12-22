require('dotenv').config();
const { ethers } = require('ethers');

// ============================================================================
// 1. REAL-WORLD ABIS (NO PLACEHOLDERS)
// ============================================================================

// Uniswap V3 QuoterV2 (The standard for quoting V3 swaps)
const V3_QUOTER_ABI = [
    'function quoteExactInputSingle((address tokenIn, address tokenOut, uint256 amountIn, uint24 fee, uint160 sqrtPriceLimitX96)) external returns (uint256 amountOut, uint160 sqrtPriceX96After, uint32 initializedTicksCrossed, uint256 gasEstimate)'
];

// Uniswap V2 / Sushi / QuickSwap Pair (Reserves) & Router
const V2_ROUTER_ABI = [
    'function getAmountsOut(uint amountIn, address[] memory path) view returns (uint[] memory amounts)'
];

// Curve V1/V2 Registry & Pool
const CURVE_REGISTRY_ABI = [
    'function get_pool_from_lp_token(address lp_token) view returns (address)',
    'function find_pool_for_coins(address _from, address _to, uint256 i) view returns (address)'
];

const CURVE_POOL_ABI = [
    'function get_dy(int128 i, int128 j, uint256 dx) external view returns (uint256)',
    'function get_dy_underlying(int128 i, int128 j, uint256 dx) external view returns (uint256)',
    'function coins(uint256 i) external view returns (address)'
];

// Balancer V2 Vault (For queryBatchSwap if needed, though V3 uses different logic)
const BALANCER_VAULT_ABI = [
    'function queryBatchSwap(uint8 kind, (bytes32 poolId, uint256 assetInIndex, uint256 assetOutIndex, uint256 amount, bytes userData)[] swaps, address[] assets, (address sender, bool fromInternalBalance, address recipient, bool toInternalBalance) funds) external returns (int256[] assetDeltas)'
];

// ============================================================================
// 2. THE SIMULATION ENGINE CLASS
// ============================================================================

class OmniSDKEngine {
    /**
     * Initializes the engine with a direct RPC connection.
     * @param {number} chainId - The EIP-155 Chain ID (e.g., 137)
     * @param {string} rpcUrl - The secure HTTP RPC endpoint
     */
    constructor(chainId, rpcUrl) {
        if (!rpcUrl || !chainId) throw new Error("OmniSDKEngine: Missing ChainID or RPC URL.");
        
        this.chainId = chainId;
        this.provider = new ethers.JsonRpcProvider(rpcUrl);
        
        // Known Contract Registry (To be filled from config in prod)
        this.QUOTER_V3_ADDR = this._getV3QuoterAddress(chainId);
    }

    /**
     * Returns the correct Uniswap V3 Quoter address for the chain.
     */
    _getV3QuoterAddress(chainId) {
        const map = {
            1: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e", // Mainnet
            137: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e", // Polygon
            42161: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e", // Arbitrum
            10: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e" // Optimism
        };
        return map[chainId] || "0x61fFE014bA17989E743c5F6cB21bF9697530B21e"; // Default
    }

    // ============================================================================
    // 3. LIVE QUOTE VERIFICATION (PRE-TRADE)
    // ============================================================================

    /**
     * Queries the blockchain to see exactly what a swap would yield right now.
     * @param {string} protocol - "UNIV3", "UNIV2", "CURVE"
     * @param {string} routerAddress - The contract to query
     * @param {object} params - Swap parameters (tokenIn, tokenOut, fee, amount)
     * @returns {Promise<bigint>} The output amount in Wei
     */
    async getRealOnChainQuote(protocol, routerAddress, params) {
        try {
            if (protocol === 'UNIV3') {
                const quoter = new ethers.Contract(this.QUOTER_V3_ADDR, V3_QUOTER_ABI, this.provider);
                
                // callStatic simulates the transaction without mining it
                const quote = await quoter.quoteExactInputSingle.staticCall({
                    tokenIn: params.tokenIn,
                    tokenOut: params.tokenOut,
                    amountIn: params.amount,
                    fee: params.fee || 3000, // Default 0.3%
                    sqrtPriceLimitX96: 0 // No limit
                });
                
                // quoteExactInputSingle returns (amountOut, ...)
                return quote[0];
            }

            if (protocol === 'UNIV2') {
                const router = new ethers.Contract(routerAddress, V2_ROUTER_ABI, this.provider);
                const path = params.path || [params.tokenIn, params.tokenOut];
                const amounts = await router.getAmountsOut(params.amount, path);
                return amounts[amounts.length - 1];
            }

            if (protocol === 'CURVE') {
                // Curve logic requires pool address + indices (i, j)
                // If only router is provided, this is complex. 
                // Assuming we passed the Pool Address as 'routerAddress' for direct query.
                const pool = new ethers.Contract(routerAddress, CURVE_POOL_ABI, this.provider);
                
                // Try get_dy (Standard pools)
                try {
                    return await pool.get_dy(params.i, params.j, params.amount);
                } catch (e) {
                    // Fallback for older pools or underlying swaps
                    return await pool.get_dy_underlying(params.i, params.j, params.amount);
                }
            }

            return 0n;

        } catch (error) {
            console.warn(`⚠️ Quote Simulation Failed [${protocol}]: ${error.shortMessage || error.message}`);
            return 0n;
        }
    }

    // ============================================================================
    // 4. FULL TRANSACTION SIMULATION (THE SAFETY NET)
    // ============================================================================

    /**
     * Simulates the entire Flash Loan transaction via 'eth_call'.
     * This checks if the trade will REVERT due to slippage, lack of liquidity, or logic error.
     * * @param {object} txRequest - The populated transaction object { to, data, value, from, ... }
     * @returns {Promise<{success: boolean, gasUsed: bigint, error: string}>}
     */
    async simulateTransaction(txRequest) {
        console.log("🧪 Running Full System Simulation...");

        try {
            // 1. Prepare Call
            // We override the block number to 'latest' to simulate against pending state if supported
            const txObj = {
                to: txRequest.to,
                from: txRequest.from,
                data: txRequest.data,
                value: txRequest.value || "0x0"
            };

            // 2. Execute eth_call
            // If this throws, the transaction would have failed on-chain.
            const result = await this.provider.call(txObj);

            // 3. Estimate Gas (Double Check)
            // eth_estimateGas runs the code to calculate gas. If it fails, it throws.
            const gasEstimate = await this.provider.estimateGas(txObj);

            console.log(`✅ Simulation SUCCESS. Estimated Gas: ${gasEstimate.toString()}`);
            return { success: true, gasUsed: gasEstimate, error: null };

        } catch (error) {
            const reason = this._extractRevertReason(error);
            console.error(`🛑 Simulation REVERTED: ${reason}`);
            
            return { success: false, gasUsed: 0n, error: reason };
        }
    }

    /**
     * Utilities to parse cryptic EVM revert errors into readable text.
     */
    _extractRevertReason(error) {
        // Ethers v6 puts data in error.data or error.revert.args
        if (error.reason) return error.reason;
        
        // Decode Custom Error if possible
        if (error.data && error.data.startsWith('0x08c379a0')) { // Error(string)
            const abiCoder = new ethers.AbiCoder();
            return abiCoder.decode(['string'], '0x' + error.data.slice(10))[0];
        }
        
        return error.shortMessage || "Unknown Revert (Check Liquidity or Auth)";
    }
}

module.exports = { OmniSDKEngine };