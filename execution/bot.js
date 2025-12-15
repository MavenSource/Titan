require('dotenv').config();
const { ethers } = require('ethers');
const { createClient } = require('redis');
const { GasManager } = require('./gas_manager');
const { BloxRouteManager } = require('./bloxroute_manager');
const { AggregatorSelector } = require('./aggregator_selector');
const { OmniSDKEngine } = require('./omniarb_sdk_engine');
const { LifiExecutionEngine } = require('./lifi_manager');

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const EXECUTOR_ADDR = process.env.EXECUTOR_ADDRESS;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
// TITAN_EXECUTION_MODE takes precedence (set by orchestrator), fallback to EXECUTION_MODE (.env)
const EXECUTION_MODE = (process.env.TITAN_EXECUTION_MODE || process.env.EXECUTION_MODE || 'PAPER').toUpperCase();

const RPC_MAP = {
    1: process.env.RPC_ETHEREUM,
    137: process.env.RPC_POLYGON,
    42161: process.env.RPC_ARBITRUM,
    10: process.env.RPC_OPTIMISM,
    8453: process.env.RPC_BASE,
    56: process.env.RPC_BSC,
    43114: process.env.RPC_AVALANCHE,
    250: process.env.RPC_FANTOM,
    59144: process.env.RPC_LINEA,
    534352: process.env.RPC_SCROLL,
    5000: process.env.RPC_MANTLE,
    324: process.env.RPC_ZKSYNC,
    81457: process.env.RPC_BLAST,
    42220: process.env.RPC_CELO,
    204: process.env.RPC_OPBNB
};

class TitanBot {
    constructor() {
        this.redis = createClient({ url: REDIS_URL });
        this.bloxRoute = new BloxRouteManager();
        this.activeProviders = {};
        this.crossChainEnabled = this._parseBooleanEnv(process.env.ENABLE_CROSS_CHAIN);
        this.executionMode = EXECUTION_MODE;
        this.paperTrades = [];
        this.paperTradeCount = 0;
    }
    
    /**
     * Parse boolean environment variables safely
     * @param {string} value - Environment variable value
     * @returns {boolean} - Parsed boolean value
     */
    _parseBooleanEnv(value) {
        if (!value) return false;
        const normalized = value.toLowerCase().trim();
        return normalized === 'true' || normalized === '1' || normalized === 'yes';
    }

    async init() {
        console.log("🤖 Titan Bot Starting...");
        console.log(`📋 Execution Mode: ${this.executionMode}`);
        
        if (this.executionMode === 'PAPER') {
            console.log("📝 PAPER MODE: Trades will be simulated (no blockchain execution)");
            console.log("   • Real-time data: ✓");
            console.log("   • Real calculations: ✓");
            console.log("   • Execution: SIMULATED");
        } else {
            console.log("🔴 LIVE MODE: Real blockchain execution enabled");
            console.log("   ⚠️  WARNING: Real funds will be used!");
        }
        console.log("");
        
        // Validate configuration (only required for LIVE mode)
        if (this.executionMode === 'LIVE') {
            if (!PRIVATE_KEY || !/^0x[0-9a-fA-F]{64}$/.test(PRIVATE_KEY)) {
                console.error('❌ CRITICAL: Invalid private key format in .env');
                console.error('   Must be 64 hex characters with 0x prefix (e.g., 0x1234...)');
                process.exit(1);
            }
            
            if (!EXECUTOR_ADDR || !/^0x[0-9a-fA-F]{40}$/.test(EXECUTOR_ADDR)) {
                console.error('❌ CRITICAL: Invalid executor address format in .env');
                console.error('   Must be 40 hex characters with 0x prefix (e.g., 0xabcd...)');
                process.exit(1);
            }
        } else {
            console.log("ℹ️  Paper mode: Skipping wallet validation");
        }
        
        // Validate gas configuration
        const maxBaseFee = parseFloat(process.env.MAX_BASE_FEE_GWEI);
        if (isNaN(maxBaseFee) || maxBaseFee <= 0) {
            console.warn('⚠️ Invalid MAX_BASE_FEE_GWEI, using default 500 gwei');
        }
        
        // Connect to Redis with retry logic
        let retries = 0;
        const maxRetries = 5;
        
        while (retries < maxRetries) {
            try {
                await this.redis.connect();
                console.log("✅ Redis connected successfully");
                break;
            } catch (e) {
                retries++;
                console.error(`⚠️ Redis connection attempt ${retries} failed:`, e.message);
                
                if (retries >= maxRetries) {
                    console.error('❌ CRITICAL: Could not connect to Redis after maximum retries');
                    console.error('   Please ensure Redis is running on localhost:6379');
                    process.exit(1);
                }
                
                // Exponential backoff
                const delay = Math.min(1000 * Math.pow(2, retries), 10000);
                console.log(`   Retrying in ${delay}ms...`);
                await new Promise(resolve => setTimeout(resolve, delay));
            }
        }
        
        // Subscribe to trade signals with error handling
        try {
            await this.redis.subscribe('trade_signals', async (msg) => {
                try {
                    const signal = JSON.parse(msg);
                    await this.executeTrade(signal);
                } catch (parseError) {
                    console.error('❌ Failed to parse trade signal:', parseError.message);
                }
            });
            console.log("✅ Subscribed to 'trade_signals' channel");
            console.log("🚀 Titan Bot Online - Waiting for signals...\n");
        } catch (e) {
            console.error('❌ CRITICAL: Failed to subscribe to Redis channel:', e.message);
            process.exit(1);
        }
        
        // Set up graceful shutdown
        process.on('SIGINT', async () => {
            console.log('\n🛑 Shutting down gracefully...');
            try {
                await this.redis.quit();
                console.log('✅ Redis connection closed');
            } catch (e) {
                console.error('Error closing Redis:', e.message);
            }
            process.exit(0);
        });
        
        // Set up Redis error handler
        this.redis.on('error', (err) => {
            console.error('❌ Redis error:', err.message);
        });
        
        this.redis.on('reconnecting', () => {
            console.log('⚠️ Redis reconnecting...');
        });
    }

    /**
     * Execute a paper trade (simulation only, no blockchain interaction)
     */
    async executePaperTrade(signal) {
        const startTime = Date.now();
        
        try {
            // Validate signal
            if (!signal || !signal.chainId || !signal.token || !signal.amount) {
                console.error('❌ Invalid signal structure:', signal);
                return;
            }
            
            this.paperTradeCount++;
            const tradeId = `PAPER-${this.paperTradeCount}-${Date.now()}`;
            
            console.log(`\n📝 Paper Trade #${this.paperTradeCount} - ${new Date().toISOString()}`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`   Trade ID: ${tradeId}`);
            console.log(`   Chain: ${signal.chainId}`);
            console.log(`   Token: ${signal.token}`);
            console.log(`   Amount: ${signal.amount}`);
            console.log(`   Type: ${signal.type || 'INTRA_CHAIN'}`);
            console.log(`   Expected Profit: $${signal.metrics?.profit_usd?.toFixed(2) || 'N/A'}`);
            
            // Simulate execution delay (realistic timing)
            await new Promise(resolve => setTimeout(resolve, 100));
            
            // Record paper trade
            const paperTrade = {
                id: tradeId,
                timestamp: new Date().toISOString(),
                signal: signal,
                status: 'SIMULATED',
                duration_ms: Date.now() - startTime,
                mode: 'PAPER'
            };
            
            this.paperTrades.push(paperTrade);
            
            // Keep only last 100 paper trades in memory
            if (this.paperTrades.length > 100) {
                this.paperTrades.shift();
            }
            
            console.log(`   Status: ✅ SIMULATED`);
            console.log(`   Duration: ${paperTrade.duration_ms}ms`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
            
        } catch (e) {
            console.error('❌ Paper trade error:', e.message);
        }
    }

    async executeTrade(signal) {
        // Route to paper execution if in PAPER mode
        if (this.executionMode === 'PAPER') {
            return await this.executePaperTrade(signal);
        }
        
        // Otherwise, execute real trade (LIVE mode)
        const startTime = Date.now();
        let executionStatus = 'UNKNOWN';
        
        try {
            // Validate signal
            if (!signal || !signal.chainId || !signal.token || !signal.amount) {
                console.error('❌ Invalid signal structure:', signal);
                return;
            }
            
            const chainId = signal.chainId;
            
            // Validate RPC exists
            if (!RPC_MAP[chainId]) {
                console.error(`❌ No RPC configured for chain ${chainId}`);
                return;
            }
            
            // Validate credentials - check if it's a valid 64-character hex string
            if (!PRIVATE_KEY || PRIVATE_KEY.length < 64 || !/^0x[0-9a-fA-F]{64}$/.test(PRIVATE_KEY)) {
                console.error('❌ Invalid private key format - must be 64 hex characters with 0x prefix');
                return;
            }
            
            if (!EXECUTOR_ADDR || EXECUTOR_ADDR === '0xYOUR_DEPLOYED_CONTRACT_ADDRESS_HERE') {
                console.error('❌ Executor address not configured');
                return;
            }
            
            console.log(`\n🎯 Processing trade signal for chain ${chainId} at ${new Date().toISOString()}`);
            console.log(`   Token: ${signal.token}, Amount: ${signal.amount}`);
            console.log(`   Expected Profit: $${signal.metrics?.profit_usd || 'N/A'}`);
            console.log(`   Strategy Type: ${signal.strategy_type || 'SINGLE_CHAIN'}`);
            
            // Check if this is a cross-chain arbitrage signal
            if (signal.strategy_type === 'CROSS_CHAIN' && this.crossChainEnabled) {
                return await this.executeCrossChainArbitrage(signal);
            }
            
            const provider = new ethers.JsonRpcProvider(RPC_MAP[chainId]);
            const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
            const gasMgr = new GasManager(provider, chainId);
            const simulator = new OmniSDKEngine(chainId, RPC_MAP[chainId]);
            
            // Check wallet balance
            try {
                const balance = await provider.getBalance(wallet.address);
                if (balance === 0n) {
                    console.error('❌ Wallet has zero balance, cannot execute');
                    return;
                }
                console.log(`   Wallet balance: ${ethers.formatEther(balance)} native token`);
            } catch (e) {
                console.error('⚠️ Could not check wallet balance:', e.message);
            }
            
            // 1. Route construction with validation
            let routeData;
            try {
                // Use intelligent aggregator selection for DEX aggregation
                // Note: use_paraswap flag maintained for backward compatibility
                // Both flags route through the new multi-aggregator system
                if (signal.use_aggregator || signal.use_paraswap) {
                    const aggregatorSelector = new AggregatorSelector(chainId, provider);
                    
                    // Prepare trade object for aggregator
                    const trade = {
                        chainId: chainId,
                        token: signal.token,
                        destToken: signal.path[0],
                        amount: signal.amount,
                        userAddress: wallet.address,
                        valueUSD: signal.metrics?.profit_usd || 0,
                        priority: signal.ai_params?.priority > 50 ? 'SPEED' : 'STANDARD',
                        slippageBps: signal.slippageBps || 100
                    };
                    
                    // Try to get best route from aggregators
                    const swap = await aggregatorSelector.executeTrade(trade);
                    if (!swap) {
                        console.log('🛑 No aggregator route available');
                        return;
                    }
                    
                    routeData = ethers.AbiCoder.defaultAbiCoder().encode(
                        ["uint8[]", "address[]", "address[]", "bytes[]"],
                        [[4], [swap.to], [signal.path[0]], [swap.data]]
                    );
                } else {
                    // Validate routers are not zero addresses
                    for (const router of signal.routers) {
                        if (router === '0x0000000000000000000000000000000000000000') {
                            console.log('🛑 Invalid router address detected (zero address)');
                            return;
                        }
                    }
                    
                    routeData = ethers.AbiCoder.defaultAbiCoder().encode(
                        ["uint8[]", "address[]", "address[]", "bytes[]"],
                        [signal.protocols, signal.routers, signal.path, signal.extras]
                    );
                }
            } catch (e) {
                console.error('❌ Route construction failed:', e.message);
                return;
            }

            // 2. Build TX with validation
            let txRequest;
            try {
                const contract = new ethers.Contract(EXECUTOR_ADDR, ["function execute(uint8,address,uint256,bytes) external"], wallet);
                
                // Get gas fees with strategy based on signal priority
                const gasStrategy = signal.ai_params?.priority > 50 ? 'RAPID' : 'STANDARD';
                const fees = await gasMgr.getDynamicGasFees(gasStrategy);
                
                // Validate gas fees are reasonable (using same limit as GasManager)
                const MAX_GAS_FEE_GWEI = parseFloat(process.env.MAX_BASE_FEE_GWEI || '500');
                const maxFeeGwei = parseFloat(ethers.formatUnits(fees.maxFeePerGas || fees.gasPrice || 0n, 'gwei'));
                
                if (maxFeeGwei > MAX_GAS_FEE_GWEI) {
                    console.log(`🛑 Gas fees too high (${maxFeeGwei} gwei), aborting. Max allowed: ${MAX_GAS_FEE_GWEI} gwei`);
                    return;
                }
                
                txRequest = await contract.execute.populateTransaction(
                    1, signal.token, signal.amount, routeData, { ...fees }
                );
                
                // Create route info object for intelligent gas estimation
                const routeInfo = {
                    protocols: signal.protocols || [],
                    routerCount: (signal.routers || []).length,
                    hasAggregator: signal.use_aggregator || signal.use_paraswap || false
                };
                
                // Get gas limit with route-aware fallback
                const gasLimit = await gasMgr.estimateGasWithBuffer(txRequest, routeInfo);
                txRequest.gasLimit = gasLimit;
                
                // Calculate and log expected cost
                const gasPrice = fees.maxFeePerGas || fees.gasPrice;
                const estimatedCostUSD = gasMgr.estimateGasCostUSD(gasLimit, gasPrice);
                
                console.log(`   Gas limit: ${gasLimit.toString()}`);
                console.log(`   Estimated cost: $${estimatedCostUSD.toFixed(2)}`);
                
                // Profit check with gas costs
                const expectedProfit = signal.metrics?.profit_usd || 0;
                if (expectedProfit < estimatedCostUSD * 2) {
                    console.log(`⚠️ Profit margin too thin: $${expectedProfit} vs $${estimatedCostUSD.toFixed(2)} gas`);
                    return;
                }
                
            } catch (e) {
                console.error('❌ Transaction building failed:', e.message);
                return;
            }

            // 3. Simulate with retry
            let isSafe = false;
            try {
                isSafe = await simulator.simulateExecution(EXECUTOR_ADDR, txRequest.data, wallet.address);
                if (!isSafe) {
                    console.log('🛑 SIMULATION FAILED - Transaction would revert');
                    executionStatus = 'SIMULATION_FAILED';
                    return;
                }
                console.log('✅ Simulation passed');
            } catch (e) {
                console.error('❌ Simulation error:', e.message);
                executionStatus = 'SIMULATION_ERROR';
                return;
            }

            // 4. Execute with proper error handling
            executionStatus = 'EXECUTING';
            try {
                if (chainId === 137 || chainId === 56) {
                    // Use BloxRoute for MEV protection
                    try {
                        const signedTx = await wallet.signTransaction(txRequest);
                        const blockNumber = await provider.getBlockNumber();
                        const res = await this.bloxRoute.submitBundle([signedTx], blockNumber);
                        
                        if (res && res.result) {
                            console.log(`🚀 BloxRoute bundle submitted:`, res.result);
                            executionStatus = 'BLOXROUTE_SUBMITTED';
                        } else {
                            console.log('⚠️ BloxRoute submission uncertain, falling back to public mempool');
                            const tx = await wallet.sendTransaction(txRequest);
                            console.log(`✅ TX (fallback): ${tx.hash}`);
                            executionStatus = 'PUBLIC_MEMPOOL';
                            
                            // Monitor transaction
                            this._monitorTransaction(tx, provider, signal);
                        }
                    } catch (bloxError) {
                        console.error('⚠️ BloxRoute failed:', bloxError.message, '- Using public mempool');
                        const tx = await wallet.sendTransaction(txRequest);
                        console.log(`✅ TX (fallback): ${tx.hash}`);
                        executionStatus = 'PUBLIC_MEMPOOL';
                        
                        // Monitor transaction
                        this._monitorTransaction(tx, provider, signal);
                    }
                } else {
                    const tx = await wallet.sendTransaction(txRequest);
                    console.log(`✅ TX: ${tx.hash}`);
                    executionStatus = 'PUBLIC_MEMPOOL';
                    
                    // Monitor transaction
                    this._monitorTransaction(tx, provider, signal);
                }
            } catch (e) {
                console.error('❌ Transaction execution failed:', e.message);
                if (e.code === 'NONCE_EXPIRED' || e.code === 'REPLACEMENT_UNDERPRICED') {
                    console.log('⚠️ Nonce conflict detected, signal may be stale');
                    executionStatus = 'NONCE_CONFLICT';
                } else if (e.code === 'INSUFFICIENT_FUNDS') {
                    console.log('❌ Insufficient funds for transaction');
                    executionStatus = 'INSUFFICIENT_FUNDS';
                } else {
                    executionStatus = 'EXECUTION_FAILED';
                }
                return;
            }
            
        } catch (e) {
            console.error('❌ Unexpected error in executeTrade:', e);
            executionStatus = 'UNEXPECTED_ERROR';
        } finally {
            const duration = Date.now() - startTime;
            console.log(`⏱️ Execution completed in ${duration}ms with status: ${executionStatus}\n`);
        }
    }

    /**
     * Execute cross-chain arbitrage using Li.Fi for intent-based bridging.
     * 
     * Flow:
     * 1. Bridge assets from source chain to destination chain (via Li.Fi)
     * 2. Wait for bridge completion (intent-based = ~60s)
     * 3. Execute arbitrage trade on destination chain
     * 4. Optional: Bridge profits back or leave on destination chain
     */
    async executeCrossChainArbitrage(signal) {
        const startTime = Date.now();
        console.log('\n🌉 CROSS-CHAIN ARBITRAGE EXECUTION');
        console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
        
        try {
            // Validate cross-chain signal structure
            if (!signal.source_chain || !signal.dest_chain) {
                console.error('❌ Invalid cross-chain signal: missing source/dest chains');
                return;
            }

            const srcChain = signal.source_chain;
            const dstChain = signal.dest_chain;
            const token = signal.token;
            const amount = signal.amount;

            // Validate chain IDs
            if (!RPC_MAP[srcChain] || !RPC_MAP[dstChain]) {
                console.error(`❌ Unsupported chain ID: ${srcChain} or ${dstChain}`);
                return;
            }

            // Validate token address
            if (!token || !ethers.utils.isAddress(token)) {
                console.error(`❌ Invalid token address: ${token}`);
                return;
            }

            // Validate amount
            if (
                amount === undefined ||
                amount === null ||
                isNaN(amount) ||
                (typeof amount === 'string' && amount.trim() === '') ||
                BigInt(amount) <= 0n
            ) {
                console.error(`❌ Invalid amount: ${amount}`);
                return;
            }
            
            console.log(`   Source Chain: ${srcChain}`);
            console.log(`   Destination Chain: ${dstChain}`);
            console.log(`   Token: ${token}`);
            console.log(`   Amount: ${amount}`);
            console.log(`   Expected Bridge Time: ${signal.bridge_time || '60'}s`);
            console.log(`   Expected Profit: $${signal.metrics?.profit_usd || 'N/A'}`);
            
            // Step 1: Bridge assets using Li.Fi
            console.log('\n📤 Step 1: Initiating bridge transaction via Li.Fi...');
            const bridgeResult = await LifiExecutionEngine.bridgeAssets(
                srcChain,
                dstChain,
                token,
                signal.dest_token || token, // Use same token for arbitrage
                amount,
                {
                    order: 'FASTEST',      // Optimize for speed
                    slippage: 0.005,       // 0.5% slippage
                    preferIntentBased: true // Use Across/Stargate for speed
                }
            );
            
            if (!bridgeResult.success) {
                console.error(`❌ Bridge initiation failed: ${bridgeResult.error}`);
                return;
            }
            
            console.log(`✅ Bridge transaction submitted!`);
            console.log(`   TX Hash: ${bridgeResult.transactionHash}`);
            console.log(`   Bridge: ${bridgeResult.bridgeName}`);
            console.log(`   Est. Time: ${bridgeResult.estimatedTime}s`);
            console.log(`   Gas Cost: $${bridgeResult.gasCostUSD}`);
            
            // Step 2: Monitor bridge completion
            console.log(`\n⏳ Step 2: Monitoring bridge completion...`);
            const completionResult = await LifiExecutionEngine.waitForCompletion(
                bridgeResult.transactionHash,
                srcChain,
                dstChain,
                600,  // 10 minute max wait
                5     // Check every 5 seconds
            );
            
            if (!completionResult.success) {
                console.error(`❌ Bridge failed or timed out: ${completionResult.error}`);
                return;
            }
            
            console.log(`✅ Bridge completed successfully!`);
            console.log(`   Completion Time: ${completionResult.completedAt}`);
            
            // Step 3: Execute arbitrage trade on destination chain
            console.log(`\n💹 Step 3: Executing arbitrage trade on destination chain...`);
            
            // Create a new signal for destination chain execution
            const dstSignal = {
                ...signal,
                chainId: dstChain,
                token: signal.dest_token || token,
                strategy_type: 'SINGLE_CHAIN' // Execute as normal trade now
            };
            
            // Execute the trade on destination chain
            await this.executeTrade(dstSignal);
            
            const totalDuration = Date.now() - startTime;
            console.log('\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━');
            console.log(`✅ CROSS-CHAIN ARBITRAGE COMPLETED in ${totalDuration}ms`);
            console.log('━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n');
            
        } catch (error) {
            console.error('❌ Cross-chain arbitrage failed:', error.message);
            console.error(error.stack);
        }
    }
    
    async _monitorTransaction(tx, provider, signal) {
        try {
            console.log('⏳ Monitoring transaction...');
            const receipt = await tx.wait(1);
            
            if (receipt.status === 1) {
                console.log('✅ Transaction confirmed successfully');
                console.log(`   Gas used: ${receipt.gasUsed.toString()}`);
                console.log(`   Block: ${receipt.blockNumber}`);
                
                // Calculate actual profit (simplified)
                const gasUsed = receipt.gasUsed;
                const gasPrice = receipt.gasPrice || tx.maxFeePerGas;
                const gasCostWei = gasUsed * gasPrice;
                const gasCostEth = ethers.formatEther(gasCostWei);
                
                console.log(`   Gas cost: ${gasCostEth} ETH`);
                
                if (signal.metrics?.profit_usd) {
                    console.log(`   Expected profit: $${signal.metrics.profit_usd}`);
                }
            } else {
                console.log('❌ Transaction reverted on-chain');
            }
        } catch (e) {
            console.log('⚠️ Transaction monitoring failed:', e.message);
            console.log('   Transaction may still succeed, check explorer');
        }
    }
}

new TitanBot().init();