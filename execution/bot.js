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
    137: process.env.RPC_POLYGON,
    1: process.env.RPC_ETHEREUM
    // ... Add all 10 chains
};

class TitanBot {
    constructor() {
        this.redis = createClient({ url: REDIS_URL });
        this.bloxRoute = new BloxRouteManager();
        this.activeProviders = {};
    }

    async init() {
        console.log("🤖 Titan Bot Online.");
        await this.redis.connect();
        await this.redis.subscribe('trade_signals', (msg) => this.executeTrade(JSON.parse(msg)));
    }

    async executeTrade(signal) {
        const chainId = signal.chainId;
        const provider = new ethers.JsonRpcProvider(RPC_MAP[chainId]);
        const wallet = new ethers.Wallet(PRIVATE_KEY, provider);
        const gasMgr = new GasManager(provider, chainId);
        const simulator = new OmniSDKEngine(chainId, RPC_MAP[chainId]);
        
        // 1. Route
        let routeData;
        if (signal.use_paraswap) {
            const pm = new ParaSwapManager(chainId, provider);
            const swap = await pm.getBestSwap(signal.token, signal.path[0], signal.amount, wallet.address);
            if (!swap) return;
            routeData = ethers.AbiCoder.defaultAbiCoder().encode(
                ["uint8[]", "address[]", "address[]", "bytes[]"],
                [[4], [swap.to], [signal.path[0]], [swap.data]]
            );
        } else {
            routeData = ethers.AbiCoder.defaultAbiCoder().encode(
                ["uint8[]", "address[]", "address[]", "bytes[]"],
                [signal.protocols, signal.routers, signal.path, signal.extras]
            );
        }

        // 2. Build TX
        const contract = new ethers.Contract(EXECUTOR_ADDR, ["function execute(uint8,address,uint256,bytes) external"], wallet);
        const fees = await gasMgr.getDynamicGasFees('RAPID');
        
        const txRequest = await contract.execute.populateTransaction(
            1, signal.token, signal.amount, routeData, { ...fees }
        );

        // 3. Simulate
        const isSafe = await simulator.simulateExecution(EXECUTOR_ADDR, txRequest.data, wallet.address);
        if (!isSafe) return console.log("🛑 SIMULATION FAILED");

        // 4. Execute (Private)
        if (chainId === 137 || chainId === 56) {
            const signedTx = await wallet.signTransaction(txRequest);
            const res = await this.bloxRoute.submitBundle([signedTx], await provider.getBlockNumber());
            console.log(`🚀 BloxRoute:`, res);
        } else {
            const tx = await wallet.sendTransaction(txRequest);
            console.log(`✅ TX: ${tx.hash}`);
        }
    }
}

new TitanBot().init();