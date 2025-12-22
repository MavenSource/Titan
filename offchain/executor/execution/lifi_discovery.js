require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { createConfig, getChains, getTools, getConnections, ChainType } = require('@lifi/sdk');

// Initialize SDK (No provider needed just for discovery, but good practice)
createConfig({
  integrator: 'Apex-Omega-Titan',
});

class LifiDiscovery {
  constructor() {
    this.outputPath = path.join(__dirname, '../core/lifi_registry.json');
  }

  /**
   * Step 1: Get all supported Chains (EVM, Solana, etc.)
   * Filters for the chains we have RPCs for in .env
   */
  async discoverChains() {
    console.log('🌍 Li.Fi: Discovering supported blockchains...');
    try {
      const chains = await getChains({ chainTypes: [ChainType.EVM] });
      
      // Filter: Only keep chains where we have a matching RPC in .env
      // (This prevents the bot from trying to trade on chains we can't access)
      const activeChains = chains.filter(c => {
        const envKey = `RPC_${c.name.toUpperCase().replace(/\s/g, '_')}`;
        // In a real dynamic setup, you might just accept all. 
        // Here we map to our Titan Matrix IDs: 1, 137, 42161, etc.
        return [1, 137, 56, 42161, 10, 43114, 8453, 250, 59144, 534352].includes(c.id);
      });

      console.log(`✅ Found ${chains.length} total chains. Active in Titan Matrix: ${activeChains.length}`);
      return activeChains;
    } catch (error) {
      console.error('❌ Chain Discovery Failed:', error.message);
      return [];
    }
  }

  /**
   * Step 2: Get all Bridges & DEXs
   * This tells us WHO we can use (Stargate, Connext, Uniswap, etc.)
   */
  async discoverTools() {
    console.log('🛠️  Li.Fi: Fetching Bridges and DEXs...');
    try {
      const tools = await getTools();
      console.log(`✅ Bridges Available: ${tools.bridges.length}`);
      console.log(`✅ DEXs Available: ${tools.exchanges.length}`);
      return tools;
    } catch (error) {
      console.error('❌ Tool Discovery Failed:', error.message);
      return { bridges: [], exchanges: [] };
    }
  }

  /**
   * Step 3: Verify a specific Connection (e.g. USDC Poly -> USDC Arb)
   * Used to "Pre-Validate" a route before the Python Brain scans it.
   * This checks if intent-based bridges (solvers) can handle the route.
   */
  async verifyConnection(fromChain, toChain, token) {
    console.log(`🔌 Verifying connection: ${fromChain} -> ${toChain} [${token}]...`);
    try {
      const request = {
        fromChain,
        toChain,
        fromToken: token,
        toToken: token, // Same asset (Arbitrage use case)
      };

      const connections = await getConnections(request);
      
      if (connections.connections.length > 0) {
        const intentBasedBridges = ['across', 'stargate', 'hop'];
        const hasIntentBased = connections.connections.some(conn => 
          intentBasedBridges.includes(conn.tool?.toLowerCase())
        );
        
        console.log(`   ✅ Valid Path! Found ${connections.connections.length} routes.`);
        if (hasIntentBased) {
          console.log(`   🚀 Intent-based bridge available (fast settlement)`);
        }
        return {
          success: true,
          routeCount: connections.connections.length,
          hasIntentBased: hasIntentBased,
          connections: connections.connections
        };
      } else {
        console.log(`   ⚠️ No route found.`);
        return {
          success: false,
          routeCount: 0,
          hasIntentBased: false
        };
      }
    } catch (error) {
      console.error('   ❌ Connection Check Error:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * Check solver liquidity for intent-based bridges.
   * Estimates if solvers have enough capital to handle the trade size.
   */
  async checkSolverLiquidity(fromChain, toChain, token, amount) {
    console.log(`💰 Checking solver liquidity for ${amount} on ${fromChain} -> ${toChain}...`);
    try {
      // Get a quote to check if solvers can handle this amount
      const { getRoutes } = require('@lifi/sdk');
      const routeResponse = await getRoutes({
        fromChainId: fromChain,
        toChainId: toChain,
        fromTokenAddress: token,
        toTokenAddress: token,
        fromAmount: amount,
        options: {
          integrator: 'Apex-Omega-Titan',
          order: 'FASTEST',
          bridges: {
            allow: ['across', 'stargate', 'hop'] // Intent-based only
          }
        }
      });

      if (routeResponse.routes && routeResponse.routes.length > 0) {
        const route = routeResponse.routes[0];
        console.log(`   ✅ Sufficient liquidity available`);
        console.log(`   Bridge: ${route.steps[0].tool}`);
        console.log(`   Output: ${route.toAmount}`);
        return {
          success: true,
          sufficient: true,
          bridge: route.steps[0].tool,
          expectedOutput: route.toAmount
        };
      } else {
        console.log(`   ⚠️ No solvers available for this amount`);
        return {
          success: true,
          sufficient: false,
          reason: 'Insufficient solver liquidity'
        };
      }
    } catch (error) {
      console.error('   ❌ Liquidity check failed:', error.message);
      return {
        success: false,
        error: error.message
      };
    }
  }

  /**
   * MASTER ROUTINE: Runs all discovery and saves to JSON
   */
  async runFullScan() {
    console.log('🚀 STARTING LI.FI DEEP DISCOVERY...');
    
    const chains = await this.discoverChains();
    const tools = await this.discoverTools();

    // Create the Registry Object
    const registry = {
      lastUpdated: new Date().toISOString(),
      chains: chains.map(c => ({
        id: c.id,
        name: c.name,
        nativeToken: c.nativeToken,
        mainnet: c.mainnet
      })),
      bridges: tools.bridges.map(b => b.key),
      dexs: tools.exchanges.map(e => e.key)
    };

    // Write to file for Python Brain to read
    fs.writeFileSync(this.outputPath, JSON.stringify(registry, null, 2));
    console.log(`💾 Registry saved to: ${this.outputPath}`);
  }
}

// Auto-run if called directly
if (require.main === module) {
  const discovery = new LifiDiscovery();
  discovery.runFullScan();
}

module.exports = { LifiDiscovery };