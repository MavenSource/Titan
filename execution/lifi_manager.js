require('dotenv').config();
const { createConfig, EVM, executeRoute, getRoutes, getStatus } = require('@lifi/sdk');
const { ethers } = require('ethers');

// === 1. SDK CONFIGURATION ===
// This maps your .env RPCs to the Li.Fi SDK Providers
// Supports intent-based bridging via Across, Stargate, and other protocols
const config = createConfig({
  integrator: 'Apex-Omega-Titan',
  apiKey: process.env.LIFI_API_KEY,
  providers: [
    EVM({
      getWalletClient: async (chainId) => {
        // Dynamic Wallet Switcher based on Chain ID
        let rpcUrl = '';
        switch (chainId) {
          case 1: rpcUrl = process.env.RPC_ETHEREUM; break;
          case 137: rpcUrl = process.env.RPC_POLYGON; break;
          case 42161: rpcUrl = process.env.RPC_ARBITRUM; break;
          case 10: rpcUrl = process.env.RPC_OPTIMISM; break;
          case 56: rpcUrl = process.env.RPC_BSC; break;
          case 43114: rpcUrl = process.env.RPC_AVALANCHE; break;
          case 8453: rpcUrl = process.env.RPC_BASE; break;
          case 250: rpcUrl = process.env.RPC_FANTOM; break;
          case 59144: rpcUrl = process.env.RPC_LINEA; break;
          case 534352: rpcUrl = process.env.RPC_SCROLL; break;
          case 5000: rpcUrl = process.env.RPC_MANTLE; break;
          case 324: rpcUrl = process.env.RPC_ZKSYNC; break;
          case 81457: rpcUrl = process.env.RPC_BLAST; break;
          case 42220: rpcUrl = process.env.RPC_CELO; break;
          case 204: rpcUrl = process.env.RPC_OPBNB; break;
          default: throw new Error(`Unsupported Chain: ${chainId}`);
        }
        
        if (!rpcUrl) {
          throw new Error(`No RPC URL configured for chain ${chainId}. Set the RPC_* environment variable for this chain in your .env file.`);
        }
        
        // Return a Viem-compatible wallet client (wrapped ethers for SDK compatibility)
        const provider = new ethers.JsonRpcProvider(rpcUrl);
        const signer = new ethers.Wallet(process.env.PRIVATE_KEY, provider);
        return signer;
      },
    }),
  ],
});

// === 2. EXECUTION ENGINE ===
class LifiExecutionEngine {
  
  /**
   * Finds the best route and executes it immediately.
   * Supports intent-based bridging for near-instant cross-chain transfers.
   * 
   * @param {number} fromChainId - Source Chain ID (e.g., 137 for Polygon)
   * @param {number} toChainId - Destination Chain ID (e.g., 42161 for Arbitrum)
   * @param {string} fromToken - Address of token to bridge from source chain
   * @param {string} toToken - Address of token to receive on destination chain
   * @param {string} amount - Raw amount in smallest unit (e.g., "1000000" for 1 USDC with 6 decimals)
   * @param {object} options - Optional configuration
   * @param {string} options.order - Route ordering: 'CHEAPEST', 'FASTEST', 'RECOMMENDED' (default: 'CHEAPEST')
   * @param {number} options.slippage - Max slippage tolerance (default: 0.005 = 0.5%)
   * @param {boolean} options.preferIntentBased - Prefer intent-based bridges like Across (default: true)
   * @returns {Promise<object>} Execution result with transaction hash and status
   */
  static async bridgeAssets(fromChainId, toChainId, fromToken, toToken, amount, options = {}) {
    const {
      order = 'CHEAPEST',
      slippage = 0.005,
      preferIntentBased = true
    } = options;

    console.log(`🌉 Li.Fi: Calculating best route from Chain ${fromChainId} to Chain ${toChainId}...`);
    console.log(`   Amount: ${amount} | Slippage: ${slippage * 100}%`);

    try {
      // A. Get Route (Quote) - Li.Fi automatically finds best option from 15+ bridges
      const routeResponse = await getRoutes({
        fromChainId,
        toChainId,
        fromTokenAddress: fromToken,
        toTokenAddress: toToken,
        fromAmount: amount,
        options: {
          integrator: 'Apex-Omega-Titan',
          order: order, // CHEAPEST = lowest fees, FASTEST = quickest bridge
          slippage: slippage,
          bridges: {
            allow: preferIntentBased ? ['across', 'stargate', 'hop'] : undefined, // Prioritize intent-based
          },
        },
      });

      const bestRoute = routeResponse.routes[0];
      if (!bestRoute) {
        console.log('❌ Li.Fi: No route found.');
        return { success: false, error: 'NO_ROUTE_AVAILABLE' };
      }

      // Log route details
      const bridgeName = bestRoute.steps[0].tool;
      const estimatedTime = bestRoute.steps[0].estimate.executionDuration || 'Unknown';
      const gasCostUSD = bestRoute.gasCostUSD || 0;
      const toAmountMin = bestRoute.toAmountMin;

      console.log(`✅ Route Found:`);
      console.log(`   Bridge: ${bridgeName}`);
      console.log(`   Estimated Time: ${estimatedTime}s`);
      console.log(`   Gas Cost: $${gasCostUSD}`);
      console.log(`   Min Output: ${toAmountMin}`);

      // B. Execute Route
      // The SDK handles: Token Approval → Swap (if needed) → Bridge Transaction
      console.log('🚀 Executing bridge transaction...');
      const executedRoute = await executeRoute(bestRoute, config);

      console.log('✅ Bridge Transaction Sent!');
      console.log(`   TX Hash: ${executedRoute.steps[0].transactionHash || 'Pending'}`);
      
      return {
        success: true,
        transactionHash: executedRoute.steps[0].transactionHash,
        route: bestRoute,
        bridgeName: bridgeName,
        estimatedTime: estimatedTime,
        gasCostUSD: gasCostUSD,
        status: 'PENDING'
      };

    } catch (error) {
      console.error('❌ Li.Fi Execution Failed:', error.message);
      return {
        success: false,
        error: error.message,
        code: error.code || 'UNKNOWN_ERROR'
      };
    }
  }

  /**
   * Get a quote for bridging without executing.
   * Useful for pre-validation and cost estimation.
   * 
   * @param {number} fromChainId - Source Chain ID
   * @param {number} toChainId - Destination Chain ID
   * @param {string} fromToken - Source token address
   * @param {string} toToken - Destination token address
   * @param {string} amount - Amount to bridge
   * @param {object} options - Optional configuration
   * @returns {Promise<object>} Quote with route details and cost estimates
   */
  static async getQuote(fromChainId, toChainId, fromToken, toToken, amount, options = {}) {
    const { order = 'CHEAPEST', slippage = 0.005 } = options;

    try {
      const routeResponse = await getRoutes({
        fromChainId,
        toChainId,
        fromTokenAddress: fromToken,
        toTokenAddress: toToken,
        fromAmount: amount,
        options: {
          integrator: 'Apex-Omega-Titan',
          order: order,
          slippage: slippage,
        },
      });

      const bestRoute = routeResponse.routes[0];
      if (!bestRoute) {
        return { success: false, error: 'NO_ROUTE_AVAILABLE' };
      }

      return {
        success: true,
        bridgeName: bestRoute.steps[0].tool,
        fromAmount: bestRoute.fromAmount,
        toAmount: bestRoute.toAmount,
        toAmountMin: bestRoute.toAmountMin,
        gasCostUSD: bestRoute.gasCostUSD,
        estimatedTime: bestRoute.steps[0].estimate.executionDuration,
        route: bestRoute
      };
    } catch (error) {
      console.error('❌ Li.Fi Quote Failed:', error.message);
      return { success: false, error: error.message };
    }
  }

  /**
   * Monitor the status of a bridge transaction.
   * 
   * @param {string} txHash - Transaction hash from source chain
   * @param {number} fromChain - Source chain ID
   * @param {number} toChain - Destination chain ID
   * @returns {Promise<object>} Status object with completion state
   */
  static async monitorTransaction(txHash, fromChain, toChain) {
    try {
      const status = await getStatus({
        txHash: txHash,
        bridge: 'auto', // Auto-detect bridge protocol
        fromChain: fromChain,
        toChain: toChain
      });

      return {
        success: true,
        status: status.status, // 'PENDING', 'DONE', 'FAILED'
        receiving: status.receiving,
        sending: status.sending,
        substatus: status.substatus
      };
    } catch (error) {
      console.error('❌ Status check failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Wait for bridge completion (polling).
   * 
   * @param {string} txHash - Transaction hash
   * @param {number} fromChain - Source chain ID
   * @param {number} toChain - Destination chain ID
   * @param {number} maxWaitTime - Maximum wait time in seconds (default: 600 = 10 minutes)
   * @param {number} pollInterval - Polling interval in seconds (default: 5)
   * @returns {Promise<object>} Final status
   */
  static async waitForCompletion(txHash, fromChain, toChain, maxWaitTime = 600, pollInterval = 5) {
    const startTime = Date.now();
    const maxTime = maxWaitTime * 1000;

    console.log(`⏳ Monitoring bridge transaction: ${txHash}`);

    while (Date.now() - startTime < maxTime) {
      const status = await this.monitorTransaction(txHash, fromChain, toChain);
      
      if (!status.success) {
        console.error('❌ Status check error:', status.error);
        await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
        continue;
      }

      if (status.status === 'DONE') {
        console.log('✅ Bridge completed successfully!');
        return { success: true, status: 'DONE', completedAt: new Date() };
      } else if (status.status === 'FAILED') {
        console.error('❌ Bridge failed!');
        return { success: false, status: 'FAILED', error: 'Bridge transaction failed' };
      }

      console.log(`   Status: ${status.status} - Waiting ${pollInterval}s...`);
      await new Promise(resolve => setTimeout(resolve, pollInterval * 1000));
    }

    console.warn('⚠️ Bridge monitoring timed out');
    return { success: false, status: 'TIMEOUT', error: 'Maximum wait time exceeded' };
  }
}

module.exports = { LifiExecutionEngine };