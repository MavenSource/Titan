import WebSocket from 'ws';
import { Worker } from 'worker_threads';
import path from 'path';
import dotenv from 'dotenv';

dotenv.config();

const CHAINS = [
    { id: 137, name: 'POLY', ws: process.env.WSS_POLYGON },
    { id: 1, name: 'ETH', ws: process.env.WSS_ETHEREUM }
];

export class MempoolHound {
    private workers: Map<number, Worker> = new Map();

    constructor() {
        console.log("🐶 Mempool Hound: Initializing...");
        this.initializeWorkers();
        this.initializeWebsockets();
    }

    private initializeWorkers() {
        CHAINS.forEach(chain => {
            const worker = new Worker(path.join(__dirname, './decoderWorker.js'), {
                workerData: { chainId: chain.id }
            });
            this.workers.set(chain.id, worker);
        });
    }

    private initializeWebsockets() {
        CHAINS.forEach(chain => {
            if (!chain.ws) return;
            const ws = new WebSocket(chain.ws);
            
            ws.on('open', () => {
                console.log(`👂 Listening on ${chain.name}...`);
                ws.send(JSON.stringify({
                    jsonrpc: "2.0",
                    id: 1,
                    method: "eth_subscribe",
                    params: ["newPendingTransactions"]
                }));
            });

            ws.on('message', (data: string) => {
                const res = JSON.parse(data);
                if (res.params?.result) {
                    this.workers.get(chain.id)?.postMessage({ type: 'TX', hash: res.params.result });
                }
            });
        });
    }
}

new MempoolHound();