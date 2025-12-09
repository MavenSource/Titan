/**
 * 🎯 TITAN LIVE MONITORING DASHBOARD
 * Ultra-transparent real-time operations monitoring with interactive web UI
 * 
 * Features:
 * - Real-time WebSocket updates (sub-second latency)
 * - Live chain status across all 15 networks
 * - Opportunity feed with profit calculations
 * - Gas price tracking
 * - Execution statistics
 * - System health monitoring
 */

const express = require('express');
const WebSocket = require('ws');
const http = require('http');
const { ethers } = require('ethers');
require('dotenv').config();

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// Dashboard state
const dashboardState = {
    chains: {},
    opportunities: [],
    executions: {
        total: 0,
        paper: 0,
        live: 0,
        failed: 0,
        profit: 0
    },
    systemHealth: {
        uptime: Date.now(),
        mode: process.env.EXECUTION_MODE || 'paper',
        pythonConnected: false,
        executionServerConnected: false
    },
    gasPrices: {}
};

// Chain configurations
const CHAINS = {
    1: { name: 'Ethereum', symbol: 'ETH', color: '#627EEA' },
    137: { name: 'Polygon', symbol: 'MATIC', color: '#8247E5' },
    42161: { name: 'Arbitrum', symbol: 'ARB', color: '#28A0F0' },
    10: { name: 'Optimism', symbol: 'OP', color: '#FF0420' },
    8453: { name: 'Base', symbol: 'ETH', color: '#0052FF' },
    56: { name: 'BSC', symbol: 'BNB', color: '#F3BA2F' },
    43114: { name: 'Avalanche', symbol: 'AVAX', color: '#E84142' },
    250: { name: 'Fantom', symbol: 'FTM', color: '#1969FF' },
    59144: { name: 'Linea', symbol: 'ETH', color: '#61DFFF' },
    534352: { name: 'Scroll', symbol: 'ETH', color: '#FBC06B' },
    5000: { name: 'Mantle', symbol: 'MNT', color: '#000000' },
    324: { name: 'ZKsync', symbol: 'ETH', color: '#8C8DFC' },
    81457: { name: 'Blast', symbol: 'ETH', color: '#FCFC03' },
    42220: { name: 'Celo', symbol: 'CELO', color: '#FBCC5C' },
    204: { name: 'opBNB', symbol: 'BNB', color: '#F0B90B' }
};

// Initialize RPC providers for gas tracking
const providers = {};
const initializeProviders = () => {
    const rpcMap = {
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

    for (const [chainId, rpc] of Object.entries(rpcMap)) {
        if (rpc) {
            try {
                providers[chainId] = new ethers.JsonRpcProvider(rpc);
                dashboardState.chains[chainId] = {
                    ...CHAINS[chainId],
                    status: 'connected',
                    lastBlock: 0,
                    gasPrice: 0
                };
            } catch (err) {
                console.error(`Failed to initialize chain ${chainId}:`, err.message);
                dashboardState.chains[chainId] = {
                    ...CHAINS[chainId],
                    status: 'error',
                    error: err.message
                };
            }
        }
    }
};

// Update gas prices periodically
const updateGasPrices = async () => {
    for (const [chainId, provider] of Object.entries(providers)) {
        try {
            const feeData = await provider.getFeeData();
            const gasPriceGwei = parseFloat(ethers.formatUnits(feeData.gasPrice || feeData.maxFeePerGas, 'gwei'));
            
            dashboardState.gasPrices[chainId] = {
                gwei: gasPriceGwei.toFixed(2),
                timestamp: Date.now()
            };
            
            if (dashboardState.chains[chainId]) {
                dashboardState.chains[chainId].gasPrice = gasPriceGwei;
                dashboardState.chains[chainId].status = 'connected';
            }
        } catch (err) {
            if (dashboardState.chains[chainId]) {
                dashboardState.chains[chainId].status = 'error';
            }
        }
    }
    
    broadcast({ type: 'gas_update', data: dashboardState.gasPrices });
};

// Broadcast to all WebSocket clients
const broadcast = (data) => {
    const message = JSON.stringify(data);
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(message);
        }
    });
};

// WebSocket connection handler
wss.on('connection', (ws) => {
    console.log('📊 Dashboard client connected');
    
    // Send initial state
    ws.send(JSON.stringify({
        type: 'init',
        data: dashboardState
    }));
    
    ws.on('close', () => {
        console.log('📊 Dashboard client disconnected');
    });
});

// API Endpoints
app.get('/api/state', (req, res) => {
    res.json(dashboardState);
});

app.get('/api/opportunities', (req, res) => {
    res.json(dashboardState.opportunities);
});

app.get('/api/executions', (req, res) => {
    res.json(dashboardState.executions);
});

// Add opportunity (called by Python brain or execution server)
app.post('/api/opportunity', express.json(), (req, res) => {
    const opportunity = {
        id: Date.now(),
        timestamp: new Date().toISOString(),
        ...req.body
    };
    
    dashboardState.opportunities.unshift(opportunity);
    if (dashboardState.opportunities.length > 100) {
        dashboardState.opportunities.pop();
    }
    
    broadcast({ type: 'opportunity', data: opportunity });
    res.json({ success: true });
});

// Add execution result
app.post('/api/execution', express.json(), (req, res) => {
    const execution = req.body;
    
    dashboardState.executions.total++;
    if (execution.mode === 'PAPER') {
        dashboardState.executions.paper++;
    } else if (execution.mode === 'LIVE') {
        dashboardState.executions.live++;
    }
    
    if (execution.status === 'failed') {
        dashboardState.executions.failed++;
    } else if (execution.profit) {
        dashboardState.executions.profit += parseFloat(execution.profit);
    }
    
    broadcast({ type: 'execution', data: execution });
    res.json({ success: true });
});

// Serve HTML dashboard
app.get('/', (req, res) => {
    res.send(`
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎯 TITAN Live Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #0a0e27 0%, #1a1f3a 100%);
            color: #e0e0e0;
            padding: 20px;
        }
        .header {
            text-align: center;
            padding: 30px;
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            margin-bottom: 30px;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .header h1 {
            font-size: 3em;
            background: linear-gradient(45deg, #00d4ff, #7b2cbf);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        .status-badge {
            display: inline-block;
            padding: 8px 20px;
            border-radius: 20px;
            font-size: 0.9em;
            font-weight: bold;
            margin: 5px;
        }
        .status-paper { background: #2196F3; color: white; }
        .status-live { background: #FF5722; color: white; animation: pulse 2s infinite; }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }
        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 15px;
            padding: 25px;
            border: 1px solid rgba(255,255,255,0.1);
            backdrop-filter: blur(10px);
        }
        .card h2 {
            font-size: 1.3em;
            margin-bottom: 20px;
            color: #00d4ff;
            border-bottom: 2px solid rgba(0,212,255,0.3);
            padding-bottom: 10px;
        }
        .metric {
            display: flex;
            justify-content: space-between;
            padding: 12px 0;
            border-bottom: 1px solid rgba(255,255,255,0.05);
        }
        .metric:last-child { border-bottom: none; }
        .metric-label { color: #999; }
        .metric-value { 
            font-weight: bold;
            font-size: 1.2em;
        }
        .profit { color: #4CAF50; }
        .loss { color: #F44336; }
        .chain-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
            gap: 15px;
        }
        .chain-item {
            background: rgba(255,255,255,0.03);
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            border: 2px solid rgba(255,255,255,0.1);
            transition: all 0.3s;
        }
        .chain-item:hover {
            transform: translateY(-5px);
            border-color: #00d4ff;
        }
        .chain-status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            display: inline-block;
            margin-right: 8px;
        }
        .status-connected { background: #4CAF50; animation: glow 2s infinite; }
        .status-error { background: #F44336; }
        @keyframes glow {
            0%, 100% { box-shadow: 0 0 5px #4CAF50; }
            50% { box-shadow: 0 0 20px #4CAF50; }
        }
        .opportunities {
            max-height: 400px;
            overflow-y: auto;
        }
        .opportunity-item {
            background: rgba(255,255,255,0.03);
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            border-left: 4px solid #00d4ff;
        }
        .timestamp {
            font-size: 0.85em;
            color: #666;
        }
        .live-indicator {
            position: fixed;
            top: 20px;
            right: 20px;
            background: #4CAF50;
            color: white;
            padding: 10px 20px;
            border-radius: 25px;
            font-weight: bold;
            animation: pulse 2s infinite;
            z-index: 1000;
        }
        .update-time {
            text-align: center;
            color: #666;
            font-size: 0.9em;
            margin-top: 20px;
        }
    </style>
</head>
<body>
    <div class="live-indicator">🟢 LIVE</div>
    
    <div class="header">
        <h1>🎯 TITAN ARBITRAGE MONITOR</h1>
        <div id="systemStatus"></div>
    </div>

    <div class="grid">
        <div class="card">
            <h2>📊 Execution Stats</h2>
            <div class="metric">
                <span class="metric-label">Total Signals</span>
                <span class="metric-value" id="totalSignals">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Paper Executions</span>
                <span class="metric-value" id="paperExec">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Live Executions</span>
                <span class="metric-value" id="liveExec">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Failed</span>
                <span class="metric-value loss" id="failedExec">0</span>
            </div>
            <div class="metric">
                <span class="metric-label">Total Profit</span>
                <span class="metric-value profit" id="totalProfit">$0.00</span>
            </div>
        </div>

        <div class="card">
            <h2>⛽ Live Gas Prices</h2>
            <div id="gasPrices">Fetching...</div>
        </div>

        <div class="card">
            <h2>🔧 System Health</h2>
            <div class="metric">
                <span class="metric-label">Uptime</span>
                <span class="metric-value" id="uptime">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Mode</span>
                <span class="metric-value" id="mode">-</span>
            </div>
            <div class="metric">
                <span class="metric-label">Chains Active</span>
                <span class="metric-value" id="chainsActive">0</span>
            </div>
        </div>
    </div>

    <div class="card">
        <h2>🌐 Chain Status (15 Networks)</h2>
        <div class="chain-grid" id="chainGrid"></div>
    </div>

    <div class="card">
        <h2>💎 Recent Opportunities</h2>
        <div class="opportunities" id="opportunities">
            <p style="text-align: center; color: #666; padding: 20px;">Waiting for opportunities...</p>
        </div>
    </div>

    <div class="update-time">Last Update: <span id="lastUpdate">-</span></div>

    <script>
        const ws = new WebSocket('ws://' + window.location.host);
        let state = {};

        ws.onopen = () => {
            console.log('🟢 Connected to dashboard');
        };

        ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            
            if (message.type === 'init') {
                state = message.data;
                updateDashboard();
            } else if (message.type === 'gas_update') {
                state.gasPrices = message.data;
                updateGasPrices();
            } else if (message.type === 'opportunity') {
                addOpportunity(message.data);
            } else if (message.type === 'execution') {
                updateExecutionStats(message.data);
            }
            
            document.getElementById('lastUpdate').textContent = new Date().toLocaleTimeString();
        };

        function updateDashboard() {
            // System status
            const mode = state.systemHealth.mode.toUpperCase();
            document.getElementById('systemStatus').innerHTML = 
                \`<span class="status-badge status-\${mode.toLowerCase()}">\${mode} MODE</span>\`;
            
            // Execution stats
            document.getElementById('totalSignals').textContent = state.executions.total;
            document.getElementById('paperExec').textContent = state.executions.paper;
            document.getElementById('liveExec').textContent = state.executions.live;
            document.getElementById('failedExec').textContent = state.executions.failed;
            document.getElementById('totalProfit').textContent = '$' + state.executions.profit.toFixed(2);
            
            // System health
            const uptime = Math.floor((Date.now() - state.systemHealth.uptime) / 1000);
            const hours = Math.floor(uptime / 3600);
            const minutes = Math.floor((uptime % 3600) / 60);
            document.getElementById('uptime').textContent = \`\${hours}h \${minutes}m\`;
            document.getElementById('mode').textContent = mode;
            
            // Chains
            const chains = Object.keys(state.chains).length;
            document.getElementById('chainsActive').textContent = chains;
            
            // Chain grid
            const chainGrid = document.getElementById('chainGrid');
            chainGrid.innerHTML = '';
            Object.entries(state.chains).forEach(([id, chain]) => {
                const div = document.createElement('div');
                div.className = 'chain-item';
                div.innerHTML = \`
                    <div><span class="chain-status status-\${chain.status}"></span>\${chain.name}</div>
                    <div style="font-size: 0.9em; color: #666; margin-top: 5px;">
                        \${chain.gasPrice ? chain.gasPrice.toFixed(2) + ' gwei' : '-'}
                    </div>
                \`;
                chainGrid.appendChild(div);
            });
            
            updateGasPrices();
        }

        function updateGasPrices() {
            const container = document.getElementById('gasPrices');
            if (!state.gasPrices || Object.keys(state.gasPrices).length === 0) {
                container.innerHTML = '<p style="color: #666;">Fetching gas prices...</p>';
                return;
            }
            
            container.innerHTML = '';
            Object.entries(state.gasPrices).forEach(([chainId, data]) => {
                const chain = state.chains[chainId];
                if (chain) {
                    const div = document.createElement('div');
                    div.className = 'metric';
                    div.innerHTML = \`
                        <span class="metric-label">\${chain.name}</span>
                        <span class="metric-value">\${data.gwei} gwei</span>
                    \`;
                    container.appendChild(div);
                }
            });
        }

        function addOpportunity(opp) {
            const container = document.getElementById('opportunities');
            if (container.textContent.includes('Waiting')) {
                container.innerHTML = '';
            }
            
            const div = document.createElement('div');
            div.className = 'opportunity-item';
            div.innerHTML = \`
                <div style="display: flex; justify-content: space-between; margin-bottom: 8px;">
                    <strong>\${opp.token || 'Unknown Token'}</strong>
                    <span class="profit">\${opp.profit ? '+$' + parseFloat(opp.profit).toFixed(2) : '-'}</span>
                </div>
                <div style="font-size: 0.9em; color: #999;">
                    Chain: \${opp.chain || opp.chainId || '-'} | 
                    Type: \${opp.type || 'Arbitrage'} |
                    <span class="timestamp">\${new Date(opp.timestamp).toLocaleTimeString()}</span>
                </div>
            \`;
            
            container.insertBefore(div, container.firstChild);
            
            // Keep only last 50
            while (container.children.length > 50) {
                container.removeChild(container.lastChild);
            }
        }

        function updateExecutionStats(exec) {
            state.executions.total++;
            if (exec.mode === 'PAPER') state.executions.paper++;
            else if (exec.mode === 'LIVE') state.executions.live++;
            if (exec.status === 'failed') state.executions.failed++;
            if (exec.profit) state.executions.profit += parseFloat(exec.profit);
            
            document.getElementById('totalSignals').textContent = state.executions.total;
            document.getElementById('paperExec').textContent = state.executions.paper;
            document.getElementById('liveExec').textContent = state.executions.live;
            document.getElementById('failedExec').textContent = state.executions.failed;
            document.getElementById('totalProfit').textContent = '$' + state.executions.profit.toFixed(2);
        }

        // Auto-refresh every 30 seconds
        setInterval(() => {
            fetch('/api/state')
                .then(r => r.json())
                .then(data => {
                    state = data;
                    updateDashboard();
                });
        }, 30000);
    </script>
</body>
</html>
    `);
});

// Initialize and start
const PORT = process.env.DASHBOARD_PORT || 3000;

initializeProviders();

// Update gas prices every 15 seconds
setInterval(updateGasPrices, 15000);
updateGasPrices();

server.listen(PORT, () => {
    console.log('');
    console.log('='.repeat(80));
    console.log('🎯 TITAN LIVE MONITORING DASHBOARD');
    console.log('='.repeat(80));
    console.log(`  Dashboard URL: http://localhost:${PORT}`);
    console.log(`  WebSocket:     ws://localhost:${PORT}`);
    console.log(`  Mode:          ${dashboardState.systemHealth.mode.toUpperCase()}`);
    console.log(`  Chains:        ${Object.keys(dashboardState.chains).length} networks`);
    console.log('='.repeat(80));
    console.log('');
    console.log('📊 Real-time monitoring active:');
    console.log('   ✓ Chain status tracking');
    console.log('   ✓ Gas price updates (15s interval)');
    console.log('   ✓ Opportunity feed');
    console.log('   ✓ Execution statistics');
    console.log('   ✓ WebSocket live updates');
    console.log('');
    console.log(`🌐 Open http://localhost:${PORT} in your browser`);
    console.log('');
});
