/**
 * TITAN REAL-TIME MONITORING SERVER
 * 
 * Provides comprehensive system transparency with:
 * - Live WebSocket streaming of all system metrics
 * - HTTP REST API for historical data queries
 * - Real-time performance tracking
 * - Trade signal monitoring
 * - Error logging and alerting
 * - Network health tracking
 */

const express = require('express');
const http = require('http');
const WebSocket = require('ws');
const path = require('path');
const { createClient } = require('redis');

const app = express();
const server = http.createServer(app);
const wss = new WebSocket.Server({ server });

// System state
const systemState = {
    startTime: Date.now(),
    chains: {},
    opportunities: {
        detected: 0,
        simulated: 0,
        executed: 0,
        failed: 0,
        rejected: 0
    },
    profits: {
        total: 0,
        paper: 0,
        live: 0,
        byChain: {}
    },
    performance: {
        avgScanTime: 0,
        avgSimulationTime: 0,
        avgExecutionTime: 0,
        scansPerSecond: 0
    },
    errors: [],
    recentTrades: [],
    activeConnections: 0,
    mode: process.env.EXECUTION_MODE || 'paper'
};

// Redis client for data persistence
let redisClient;

async function initRedis() {
    try {
        redisClient = createClient({
            url: process.env.REDIS_URL || 'redis://localhost:6379'
        });
        
        redisClient.on('error', (err) => {
            console.error('❌ Redis error:', err.message);
        });
        
        await redisClient.connect();
        console.log('✅ Connected to Redis for metrics storage');
        
        // Subscribe to all monitoring channels
        const subscriber = redisClient.duplicate();
        await subscriber.connect();
        
        // Brain signals
        await subscriber.subscribe('trade_signals', (message) => {
            try {
                const signal = JSON.parse(message);
                handleTradeSignal(signal);
            } catch (e) {
                console.error('Error parsing trade signal:', e);
            }
        });
        
        // Execution updates
        await subscriber.subscribe('execution_updates', (message) => {
            try {
                const update = JSON.parse(message);
                handleExecutionUpdate(update);
            } catch (e) {
                console.error('Error parsing execution update:', e);
            }
        });
        
        // System metrics
        await subscriber.subscribe('system_metrics', (message) => {
            try {
                const metrics = JSON.parse(message);
                handleSystemMetrics(metrics);
            } catch (e) {
                console.error('Error parsing system metrics:', e);
            }
        });
        
        // Error reports
        await subscriber.subscribe('error_reports', (message) => {
            try {
                const error = JSON.parse(message);
                handleErrorReport(error);
            } catch (e) {
                console.error('Error parsing error report:', e);
            }
        });
        
        console.log('✅ Subscribed to monitoring channels');
        
    } catch (error) {
        console.error('❌ Redis initialization failed:', error.message);
        console.log('⚠️  Continuing without Redis persistence');
    }
}

// Handle trade signal detection
function handleTradeSignal(signal) {
    systemState.opportunities.detected++;
    
    const event = {
        type: 'OPPORTUNITY_DETECTED',
        timestamp: Date.now(),
        data: {
            chainId: signal.chainId,
            token: signal.token,
            expectedProfit: signal.profit,
            loanAmount: signal.loanAmount,
            route: signal.route
        }
    };
    
    broadcast(event);
    
    // Store recent opportunity
    systemState.recentTrades.unshift({
        ...event,
        status: 'detected'
    });
    
    if (systemState.recentTrades.length > 100) {
        systemState.recentTrades.pop();
    }
}

// Handle execution updates
function handleExecutionUpdate(update) {
    const { status, chainId, profit, txHash, error, gasUsed, simulationTime, executionTime } = update;
    
    if (status === 'simulated') {
        systemState.opportunities.simulated++;
        
        if (simulationTime) {
            updateAverage('avgSimulationTime', simulationTime);
        }
        
    } else if (status === 'executed') {
        systemState.opportunities.executed++;
        
        if (profit) {
            systemState.profits.total += profit;
            
            if (systemState.mode === 'paper') {
                systemState.profits.paper += profit;
            } else {
                systemState.profits.live += profit;
            }
            
            if (!systemState.profits.byChain[chainId]) {
                systemState.profits.byChain[chainId] = 0;
            }
            systemState.profits.byChain[chainId] += profit;
        }
        
        if (executionTime) {
            updateAverage('avgExecutionTime', executionTime);
        }
        
    } else if (status === 'failed') {
        systemState.opportunities.failed++;
        
    } else if (status === 'rejected') {
        systemState.opportunities.rejected++;
    }
    
    const event = {
        type: 'EXECUTION_UPDATE',
        timestamp: Date.now(),
        data: update
    };
    
    broadcast(event);
    
    // Update recent trades
    const recentTrade = systemState.recentTrades.find(t => 
        t.data.chainId === chainId && t.status === 'detected'
    );
    
    if (recentTrade) {
        recentTrade.status = status;
        recentTrade.txHash = txHash;
        recentTrade.profit = profit;
        recentTrade.gasUsed = gasUsed;
        recentTrade.error = error;
    }
}

// Handle system metrics updates
function handleSystemMetrics(metrics) {
    const { chainId, connected, blockNumber, gasPrice, scanTime, tokensTracked } = metrics;
    
    if (!systemState.chains[chainId]) {
        systemState.chains[chainId] = {};
    }
    
    systemState.chains[chainId] = {
        connected: connected !== undefined ? connected : systemState.chains[chainId].connected,
        blockNumber: blockNumber || systemState.chains[chainId].blockNumber,
        gasPrice: gasPrice || systemState.chains[chainId].gasPrice,
        lastUpdate: Date.now(),
        tokensTracked: tokensTracked || systemState.chains[chainId].tokensTracked
    };
    
    if (scanTime) {
        updateAverage('avgScanTime', scanTime);
        
        // Calculate scans per second
        const uptime = (Date.now() - systemState.startTime) / 1000;
        const totalScans = systemState.opportunities.detected;
        systemState.performance.scansPerSecond = totalScans / uptime;
    }
    
    const event = {
        type: 'CHAIN_UPDATE',
        timestamp: Date.now(),
        data: systemState.chains[chainId]
    };
    
    broadcast(event);
}

// Handle error reports
function handleErrorReport(error) {
    const errorEntry = {
        timestamp: Date.now(),
        level: error.level || 'error',
        component: error.component,
        message: error.message,
        details: error.details,
        chainId: error.chainId
    };
    
    systemState.errors.unshift(errorEntry);
    
    // Keep last 200 errors
    if (systemState.errors.length > 200) {
        systemState.errors.pop();
    }
    
    const event = {
        type: 'ERROR_REPORT',
        timestamp: Date.now(),
        data: errorEntry
    };
    
    broadcast(event);
}

// Update rolling average
function updateAverage(field, newValue) {
    const current = systemState.performance[field];
    const alpha = 0.1; // Smoothing factor
    systemState.performance[field] = current * (1 - alpha) + newValue * alpha;
}

// Broadcast to all connected WebSocket clients
function broadcast(message) {
    const payload = JSON.stringify(message);
    
    wss.clients.forEach((client) => {
        if (client.readyState === WebSocket.OPEN) {
            client.send(payload);
        }
    });
}

// WebSocket connection handler
wss.on('connection', (ws) => {
    systemState.activeConnections++;
    console.log(`📡 New monitoring client connected (Total: ${systemState.activeConnections})`);
    
    // Send initial state
    ws.send(JSON.stringify({
        type: 'INITIAL_STATE',
        timestamp: Date.now(),
        data: {
            ...systemState,
            uptime: Date.now() - systemState.startTime
        }
    }));
    
    ws.on('close', () => {
        systemState.activeConnections--;
        console.log(`📡 Client disconnected (Total: ${systemState.activeConnections})`);
    });
    
    ws.on('error', (error) => {
        console.error('WebSocket error:', error.message);
    });
});

// REST API Endpoints

app.use(express.json());
app.use(express.static(path.join(__dirname, 'dashboard')));

// Get current system state
app.get('/api/state', (req, res) => {
    res.json({
        ...systemState,
        uptime: Date.now() - systemState.startTime
    });
});

// Get chain status
app.get('/api/chains', (req, res) => {
    res.json(systemState.chains);
});

// Get chain-specific status
app.get('/api/chains/:chainId', (req, res) => {
    const chainId = req.params.chainId;
    
    if (systemState.chains[chainId]) {
        res.json(systemState.chains[chainId]);
    } else {
        res.status(404).json({ error: 'Chain not found' });
    }
});

// Get opportunities summary
app.get('/api/opportunities', (req, res) => {
    res.json(systemState.opportunities);
});

// Get profit summary
app.get('/api/profits', (req, res) => {
    res.json(systemState.profits);
});

// Get performance metrics
app.get('/api/performance', (req, res) => {
    res.json({
        ...systemState.performance,
        uptime: Date.now() - systemState.startTime,
        scansPerSecond: systemState.performance.scansPerSecond.toFixed(2)
    });
});

// Get recent trades
app.get('/api/trades', (req, res) => {
    const limit = parseInt(req.query.limit) || 50;
    res.json(systemState.recentTrades.slice(0, limit));
});

// Get error logs
app.get('/api/errors', (req, res) => {
    const limit = parseInt(req.query.limit) || 50;
    const level = req.query.level;
    
    let errors = systemState.errors;
    
    if (level) {
        errors = errors.filter(e => e.level === level);
    }
    
    res.json(errors.slice(0, limit));
});

// Get health status
app.get('/api/health', (req, res) => {
    const uptime = Date.now() - systemState.startTime;
    const connectedChains = Object.values(systemState.chains).filter(c => c.connected).length;
    const totalChains = Object.keys(systemState.chains).length;
    
    const health = {
        status: connectedChains > 0 ? 'healthy' : 'degraded',
        uptime: uptime,
        mode: systemState.mode,
        chains: {
            connected: connectedChains,
            total: totalChains,
            percentage: totalChains > 0 ? ((connectedChains / totalChains) * 100).toFixed(1) : 0
        },
        opportunities: systemState.opportunities,
        profits: {
            total: systemState.profits.total.toFixed(2),
            mode: systemState.mode === 'paper' ? systemState.profits.paper.toFixed(2) : systemState.profits.live.toFixed(2)
        },
        performance: {
            avgScanTime: systemState.performance.avgScanTime.toFixed(2) + 'ms',
            avgSimulationTime: systemState.performance.avgSimulationTime.toFixed(2) + 'ms',
            avgExecutionTime: systemState.performance.avgExecutionTime.toFixed(2) + 'ms',
            scansPerSecond: systemState.performance.scansPerSecond.toFixed(2)
        },
        errors: {
            total: systemState.errors.length,
            recent: systemState.errors.slice(0, 5)
        },
        activeConnections: systemState.activeConnections,
        redis: redisClient ? (redisClient.isOpen ? 'connected' : 'disconnected') : 'not_configured'
    };
    
    res.json(health);
});

// Dashboard UI
app.get('/', (req, res) => {
    res.sendFile(path.join(__dirname, 'dashboard', 'index.html'));
});

// Start server
const PORT = process.env.MONITORING_PORT || 3000;

async function start() {
    await initRedis();
    
    server.listen(PORT, () => {
        console.log('\n' + '='.repeat(60));
        console.log('🔍 TITAN REAL-TIME MONITORING SERVER');
        console.log('='.repeat(60));
        console.log(`📊 Dashboard: http://localhost:${PORT}`);
        console.log(`🔌 WebSocket: ws://localhost:${PORT}`);
        console.log(`📡 API: http://localhost:${PORT}/api/health`);
        console.log(`⚙️  Mode: ${systemState.mode.toUpperCase()}`);
        console.log('='.repeat(60));
        console.log('✅ Monitoring system online. Waiting for data...\n');
    });
}

start().catch(error => {
    console.error('❌ Failed to start monitoring server:', error);
    process.exit(1);
});

// Graceful shutdown
process.on('SIGINT', async () => {
    console.log('\n⏹️  Shutting down monitoring server...');
    
    if (redisClient) {
        await redisClient.quit();
    }
    
    server.close(() => {
        console.log('✅ Monitoring server stopped');
        process.exit(0);
    });
});
