require('dotenv').config();
const { ethers } = require('ethers');
const { createClient } = require('redis');
const { GasManager } = require('./gas_manager');
const { BloxRouteManager } = require('./bloxroute_manager');
const { ParaSwapManager } = require('./paraswap_manager');
const { OmniSDKEngine } = require('./omniarb_sdk_engine');

const REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';
const EXECUTOR_ADDR = process.env.EXECUTOR_ADDRESS;
const PRIVATE_KEY = process.env.PRIVATE_KEY;

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
    }

    async init() {
        console.log("🤖 Titan Bot Starting...");
        
        // Validate configuration
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

    async executeTrade(signal) {
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
                if (signal.use_paraswap) {
                    const pm = new ParaSwapManager(chainId, provider);
                    const swap = await pm.getBestSwap(signal.token, signal.path[0], signal.amount, wallet.address);
                    if (!swap) {
                        console.log('🛑 ParaSwap route not available');
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
                
                // Estimate gas limit
                try {
                    const gasLimit = await gasMgr.estimateGasLimit(txRequest);
                    txRequest.gasLimit = gasLimit;
                    console.log(`   Estimated gas: ${gasLimit.toString()}`);
                } catch (e) {
                    console.error('⚠️ Gas estimation failed:', e.message);
                    // Use a safe default
                    txRequest.gasLimit = 500000n;
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