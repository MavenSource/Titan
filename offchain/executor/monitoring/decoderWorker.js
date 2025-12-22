const { parentPort, workerData } = require('worker_threads');
const { ethers } = require('ethers');

// Target Routers (Uniswap V2/V3, Sushi, etc.)
// In prod, load this from core/config.py
const TARGETS = new Set([
    "0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D".toLowerCase(), // UniV2
    "0xE592427A0AEce92De3Edee1F18E0157C05861564".toLowerCase(), // UniV3
    "0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506".toLowerCase()  // Sushi
]);

// Initialize Provider for this thread
const RPC_URL = process.env[`RPC_${workerData.chainId === 1 ? 'ETHEREUM' : 'POLYGON'}`];
const provider = new ethers.JsonRpcProvider(RPC_URL);

parentPort.on('message', async (msg) => {
    if (msg.type === 'TX') {
        try {
            // 1. Fetch Transaction
            const tx = await provider.getTransaction(msg.hash);
            
            // 2. Filter: Is it interacting with a Router we care about?
            if (tx && tx.to && TARGETS.has(tx.to.toLowerCase())) {
                
                // 3. Decode: Is it a Swap? (Method ID check)
                // 0x38ed1739 = swapExactTokensForTokens
                // 0x5c11d795 = swapExactTokensForTokensSupportingFeeOnTransferTokens
                // 0x414bf389 = exactInputSingle (V3)
                const method = tx.data.substring(0, 10);
                
                if (['0x38ed1739', '0x5c11d795', '0x414bf389'].includes(method)) {
                    // 4. Alert Main Thread
                    parentPort.postMessage({
                        type: 'OPPORTUNITY',
                        router: tx.to,
                        hash: tx.hash
                    });
                }
            }
        } catch (e) {
            // Ignore fetch errors (tx might be mined already)
        }
    }
});