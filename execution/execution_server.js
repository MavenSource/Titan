#!/usr/bin/env node
/**
 * ================================================================================
 * TITAN EXECUTION SERVER - Direct Python-to-Node Communication
 * ================================================================================
 * Provides HTTP/WebSocket server for Python brain to submit trades directly
 * without Redis dependency. Handles both LIVE and PAPER execution modes.
 * ================================================================================
 */

require('dotenv').config();
const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const { ethers } = require('ethers');
const redis = require('redis');
const { GasManager } = require('./gas_manager');
const { BloxRouteManager } = require('./bloxroute_manager');
const { OmniSDKEngine } = require('./omniarb_sdk_engine');

const PORT = process.env.EXECUTION_PORT || 8545;
const EXECUTOR_ADDR = process.env.EXECUTOR_ADDRESS;
const PRIVATE_KEY = process.env.PRIVATE_KEY;
const EXECUTION_MODE = process.env.EXECUTION_MODE || 'PAPER';

// RPC Configuration
const RPC_MAP = {
    1: process.env.RPC_ETHEREUM,
    10: process.env.RPC_OPTIMISM,
    56: process.env.RPC_BSC,
    137: process.env.RPC_POLYGON,
    204: process.env.RPC_OPBNB,
    250: process.env.RPC_FANTOM,
    324: process.env.RPC_ZKSYNC,
    5000: process.env.RPC_MANTLE,
    8453: process.env.RPC_BASE,
    42161: process.env.RPC_ARBITRUM,
    42220: process.env.RPC_CELO,
    43114: process.env.RPC_AVALANCHE,
    59144: process.env.RPC_LINEA,
    81457: process.env.RPC_BLAST,
    534352: process.env.RPC_SCROLL
};

class ExecutionServer {
    constructor() {
        this.app = express();
        this.server = http.createServer(this.app);
        this.wss = new WebSocket.Server({ server: this.server });
        this.bloxRoute = new BloxRouteManager();
        this.providers = {};
        this.wallets = {};
        this.activeClients = new Set();
        
        // Redis client for metrics
        this.redisClient = null;
        this.initializeRedis();
        
        // Execution statistics
        this.stats = {
            total_signals: 0,
            executed: 0,
            failed: 0,
            paper_executed: 0,
            total_profit: 0,
            mode: EXECUTION_MODE
        };
        
        this.setupMiddleware();
        this.setupRoutes();
        this.setupWebSocket();
        this.initializeProviders();
    }
    
    async initializeRedis() {
        try {
            this.redisClient = redis.createClient({
                url: process.env.REDIS_URL || 'redis://localhost:6379'
            });
            
            this.redisClient.on('error', (err) => {
                console.error('❌ Redis error:', err.message);
            });
            
            await this.redisClient.connect();
            console.log('✅ Connected to Redis for metrics publishing');
        } catch (error) {
            console.warn('⚠️  Redis connection failed:', error.message);
            console.warn('⚠️  Continuing without metrics publishing');
            this.redisClient = null;
        }
    }
    
    publishMetric(channel, data) {
        if (this.redisClient && this.redisClient.isOpen) {
            try {
                this.redisClient.publish(channel, JSON.stringify(data));
            } catch (error) {
                console.error('Failed to publish metric:', error.message);
            }
        }
    }
    
    setupMiddleware() {
        this.app.use(express.json({ limit: '10mb' }));
        this.app.use((req, res, next) => {
            console.log(`[${new Date().toISOString()}] ${req.method} ${req.path}`);
            next();
        });
    }
    
    initializeProviders() {
        console.log('\n🔗 Initializing RPC Providers...');
        for (const [chainId, rpcUrl] of Object.entries(RPC_MAP)) {
            if (rpcUrl) {
                try {
                    this.providers[chainId] = new ethers.JsonRpcProvider(rpcUrl);
                    if (PRIVATE_KEY && PRIVATE_KEY !== 'your_private_key_here') {
                        this.wallets[chainId] = new ethers.Wallet(PRIVATE_KEY, this.providers[chainId]);
                    }
                    console.log(`  ✓ Chain ${chainId}: Connected`);
                } catch (error) {
                    console.error(`  ⚠️  Chain ${chainId}: Failed - ${error.message}`);
                }
            }
        }
        console.log(`✅ Initialized ${Object.keys(this.providers).length} chain providers\n`);
    }
    
    setupRoutes() {
        // Health check
        this.app.get('/health', (req, res) => {
            res.json({
                status: 'healthy',
                mode: EXECUTION_MODE,
                chains: Object.keys(this.providers).length,
                uptime: process.uptime(),
                stats: this.stats
            });
        });
        
        // Execute trade signal (HTTP endpoint)
        this.app.post('/execute', async (req, res) => {
            try {
                const signal = req.body;
                console.log(`\n📡 Received trade signal for chain ${signal.chainId}`);
                
                const result = await this.executeTradeSignal(signal);
                res.json(result);
            } catch (error) {
                console.error('❌ Execution error:', error);
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });
        
        // Batch execute multiple signals
        this.app.post('/execute/batch', async (req, res) => {
            try {
                const signals = req.body.signals || [];
                console.log(`\n📦 Received ${signals.length} trade signals`);
                
                const results = await Promise.all(
                    signals.map(signal => this.executeTradeSignal(signal))
                );
                
                res.json({
                    total: signals.length,
                    succeeded: results.filter(r => r.success).length,
                    failed: results.filter(r => !r.success).length,
                    results
                });
            } catch (error) {
                console.error('❌ Batch execution error:', error);
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });
        
        // Get execution statistics
        this.app.get('/stats', (req, res) => {
            res.json({
                ...this.stats,
                connected_clients: this.activeClients.size,
                providers: Object.keys(this.providers).length
            });
        });
        
        // Simulate trade without execution
        this.app.post('/simulate', async (req, res) => {
            try {
                const signal = req.body;
                const chainId = signal.chainId;
                
                if (!this.providers[chainId]) {
                    return res.status(400).json({
                        success: false,
                        error: `Chain ${chainId} not configured`
                    });
                }
                
                const simulator = new OmniSDKEngine(chainId, RPC_MAP[chainId]);
                const routeData = this.buildRouteData(signal);
                
                // Build transaction for simulation
                const iface = new ethers.Interface([
                    "function execute(uint8,address,uint256,bytes) external"
                ]);
                const txData = iface.encodeFunctionData("execute", [
                    signal.flashSource || 1,
                    signal.token,
                    signal.amount,
                    routeData
                ]);
                
                const walletAddr = this.wallets[chainId]?.address || ethers.ZeroAddress;
                const result = await simulator.simulateTransaction(
                    EXECUTOR_ADDR,
                    txData,
                    walletAddr
                );
                
                res.json({
                    success: result.success,
                    simulation: result,
                    estimated_profit: signal.expected_profit
                });
            } catch (error) {
                console.error('❌ Simulation error:', error);
                res.status(500).json({
                    success: false,
                    error: error.message
                });
            }
        });
    }
    
    setupWebSocket() {
        this.wss.on('connection', (ws) => {
            console.log('🔌 WebSocket client connected');
            this.activeClients.add(ws);
            
            // Send welcome message
            ws.send(JSON.stringify({
                type: 'connected',
                mode: EXECUTION_MODE,
                stats: this.stats
            }));
            
            ws.on('message', async (message) => {
                try {
                    const data = JSON.parse(message);
                    
                    if (data.type === 'execute') {
                        const result = await this.executeTradeSignal(data.signal);
                        ws.send(JSON.stringify({
                            type: 'execution_result',
                            result
                        }));
                    } else if (data.type === 'ping') {
                        ws.send(JSON.stringify({ type: 'pong' }));
                    }
                } catch (error) {
                    ws.send(JSON.stringify({
                        type: 'error',
                        error: error.message
                    }));
                }
            });
            
            ws.on('close', () => {
                console.log('🔌 WebSocket client disconnected');
                this.activeClients.delete(ws);
            });
        });
    }
    
    buildRouteData(signal) {
        // Build route data for OmniArbExecutor
        return ethers.AbiCoder.defaultAbiCoder().encode(
            ["uint8[]", "address[]", "address[]", "bytes[]"],
            [
                signal.protocols || [],
                signal.routers || [],
                signal.path || [],
                signal.extras || []
            ]
        );
    }
    
    async executeTradeSignal(signal) {
        this.stats.total_signals++;
        const chainId = signal.chainId;
        
        console.log(`\n${'='.repeat(80)}`);
        console.log(`📊 TRADE SIGNAL #${this.stats.total_signals}`);
        console.log(`${'='.repeat(80)}`);
        console.log(`  Chain: ${chainId}`);
        console.log(`  Mode: ${EXECUTION_MODE}`);
        console.log(`  Token: ${signal.token}`);
        console.log(`  Amount: ${signal.amount}`);
        console.log(`  Expected Profit: ${signal.expected_profit} USD`);
        console.log(`  Flash Source: ${signal.flashSource === 1 ? 'Balancer V3' : 'Aave V3'}`);
        
        // Validate chain availability
        if (!this.providers[chainId]) {
            console.log(`❌ Chain ${chainId} not configured`);
            this.stats.failed++;
            return {
                success: false,
                error: `Chain ${chainId} not configured`,
                mode: EXECUTION_MODE
            };
        }
        
        try {
            const provider = this.providers[chainId];
            const wallet = this.wallets[chainId];
            
            // Check if wallet is available for LIVE mode
            if (EXECUTION_MODE === 'LIVE' && !wallet) {
                throw new Error('No wallet configured for LIVE execution');
            }
            
            // Build route data
            const routeData = this.buildRouteData(signal);
            
            // Gas management
            const gasMgr = new GasManager(provider, chainId);
            const fees = await gasMgr.getDynamicGasFees('RAPID');
            console.log(`  ⛽ Gas: ${fees.maxFeePerGas ? ethers.formatUnits(fees.maxFeePerGas, 'gwei') + ' gwei' : 'legacy'}`);
            
            // Simulate transaction
            console.log(`  🔬 Simulating transaction...`);
            const simulator = new OmniSDKEngine(chainId, RPC_MAP[chainId]);
            
            const iface = new ethers.Interface([
                "function execute(uint8,address,uint256,bytes) external"
            ]);
            const txData = iface.encodeFunctionData("execute", [
                signal.flashSource || 1,
                signal.token,
                signal.amount,
                routeData
            ]);
            
            const walletAddr = wallet?.address || ethers.ZeroAddress;
            const simResult = await simulator.simulateTransaction(
                EXECUTOR_ADDR || ethers.ZeroAddress,
                txData,
                walletAddr
            );
            
            if (!simResult.success) {
                console.log(`  ❌ Simulation failed: ${simResult.error || 'Unknown error'}`);
                this.stats.failed++;
                return {
                    success: false,
                    error: 'Simulation failed',
                    simulation: simResult,
                    mode: EXECUTION_MODE
                };
            }
            
            console.log(`  ✅ Simulation successful`);
            console.log(`  💰 Estimated Gas: ${simResult.gasUsed || 'N/A'}`);
            
            // Execute based on mode
            if (EXECUTION_MODE === 'PAPER') {
                // Paper trading - just log and record
                console.log(`  📝 PAPER EXECUTION - No real transaction sent`);
                this.stats.paper_executed++;
                this.stats.total_profit += parseFloat(signal.expected_profit || 0);
                
                // Broadcast to WebSocket clients
                this.broadcastToClients({
                    type: 'paper_execution',
                    signal,
                    simulation: simResult,
                    timestamp: new Date().toISOString()
                });
                
                return {
                    success: true,
                    mode: 'PAPER',
                    simulation: simResult,
                    expected_profit: signal.expected_profit,
                    timestamp: new Date().toISOString()
                };
                
            } else if (EXECUTION_MODE === 'LIVE') {
                // Live execution - send real transaction
                console.log(`  🚀 LIVE EXECUTION - Sending transaction...`);
                
                const contract = new ethers.Contract(
                    EXECUTOR_ADDR,
                    ["function execute(uint8,address,uint256,bytes) external"],
                    wallet
                );
                
                const txRequest = await contract.execute.populateTransaction(
                    signal.flashSource || 1,
                    signal.token,
                    signal.amount,
                    routeData,
                    { ...fees }
                );
                
                let txHash;
                
                // Use BloxRoute for private execution on supported chains
                if ((chainId === 137 || chainId === 56) && this.bloxRoute) {
                    console.log(`  🔒 Using BloxRoute for private execution...`);
                    const signedTx = await wallet.signTransaction(txRequest);
                    const blockNumber = await provider.getBlockNumber();
                    const bloxResult = await this.bloxRoute.submitBundle([signedTx], blockNumber);
                    txHash = bloxResult.txHash || 'pending';
                    console.log(`  ✅ BloxRoute submission: ${txHash}`);
                } else {
                    // Public execution
                    const tx = await wallet.sendTransaction(txRequest);
                    txHash = tx.hash;
                    console.log(`  ✅ Transaction sent: ${txHash}`);
                    
                    // Wait for confirmation
                    console.log(`  ⏳ Waiting for confirmation...`);
                    const receipt = await tx.wait(1);
                    console.log(`  ✅ Confirmed in block ${receipt.blockNumber}`);
                }
                
                this.stats.executed++;
                this.stats.total_profit += parseFloat(signal.expected_profit || 0);
                
                // Broadcast to WebSocket clients
                this.broadcastToClients({
                    type: 'live_execution',
                    signal,
                    txHash,
                    timestamp: new Date().toISOString()
                });
                
                return {
                    success: true,
                    mode: 'LIVE',
                    txHash,
                    chainId,
                    expected_profit: signal.expected_profit,
                    timestamp: new Date().toISOString()
                };
            }
            
        } catch (error) {
            console.error(`  ❌ Execution failed: ${error.message}`);
            this.stats.failed++;
            
            return {
                success: false,
                error: error.message,
                mode: EXECUTION_MODE
            };
        }
    }
    
    broadcastToClients(message) {
        const data = JSON.stringify(message);
        this.activeClients.forEach(client => {
            if (client.readyState === WebSocket.OPEN) {
                client.send(data);
            }
        });
    }
    
    start() {
        this.server.listen(PORT, () => {
            console.log('\n' + '='.repeat(80));
            console.log('🚀 TITAN EXECUTION SERVER ONLINE');
            console.log('='.repeat(80));
            console.log(`  Mode: ${EXECUTION_MODE}`);
            console.log(`  HTTP: http://localhost:${PORT}`);
            console.log(`  WebSocket: ws://localhost:${PORT}`);
            console.log(`  Chains: ${Object.keys(this.providers).length} configured`);
            console.log(`  Executor: ${EXECUTOR_ADDR || 'NOT SET'}`);
            console.log('='.repeat(80));
            console.log('\n📡 Endpoints:');
            console.log('  POST /execute        - Execute single trade signal');
            console.log('  POST /execute/batch  - Execute multiple signals');
            console.log('  POST /simulate       - Simulate trade without execution');
            console.log('  GET  /health         - Server health check');
            console.log('  GET  /stats          - Execution statistics');
            console.log('  WS   /               - WebSocket for real-time updates');
            console.log('\n✅ Ready to receive trade signals from Python brain\n');
        });
    }
}

// Start server
const server = new ExecutionServer();
server.start();

// Graceful shutdown
process.on('SIGINT', () => {
    console.log('\n\n🛑 Shutting down execution server...');
    console.log('📊 Final Statistics:');
    console.log(`  Total Signals: ${server.stats.total_signals}`);
    console.log(`  Executed: ${server.stats.executed}`);
    console.log(`  Paper: ${server.stats.paper_executed}`);
    console.log(`  Failed: ${server.stats.failed}`);
    console.log(`  Total Profit: $${server.stats.total_profit.toFixed(2)}`);
    process.exit(0);
});
