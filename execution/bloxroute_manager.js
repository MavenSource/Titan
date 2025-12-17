require('dotenv').config();
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * TITAN BLOXROUTE MEV MANAGER
 * ============================
 * 
 * Production-grade bloXroute integration for private transaction submission.
 * 
 * FEATURES:
 * - Polygon mainnet private bundle submission
 * - Merkle-rooted bundle integrity
 * - HMAC payload signing for authenticity
 * - Proper endpoint routing per chain
 * - Detailed submission logging
 */

// Chain-specific bloXroute endpoints
const BLOXROUTE_ENDPOINTS = {
    137: {  // Polygon
        hostname: 'polygon.blxrbdn.com',
        network: 'Polygon-Mainnet'
    },
    1: {  // Ethereum (for future use)
        hostname: 'virginia.eth.blxrbdn.com',
        network: 'Mainnet'
    },
    56: {  // BSC
        hostname: 'bsc.blxrbdn.com',
        network: 'BSC-Mainnet'
    }
};

class BloxRouteManager {
    constructor(chainId = 137) {
        this.chainId = chainId;
        this.authHeader = process.env.BLOXROUTE_AUTH;
        this.secret = process.env.BLOX_HASH_SECRET; // From secret_hash.txt
        
        // Get chain-specific endpoint
        this.endpoint = BLOXROUTE_ENDPOINTS[chainId] || BLOXROUTE_ENDPOINTS[137];
        
        // Load Certificates (optional but recommended)
        try {
            this.cert = fs.readFileSync(path.join(__dirname, '../certs/external_gateway_cert.pem'));
            this.key = fs.readFileSync(path.join(__dirname, '../certs/external_gateway_key.pem'));
            this.hasCerts = true;
        } catch (e) {
            console.warn("⚠️ BloxRoute Certs not found. Using auth header only.");
            this.hasCerts = false;
        }
    }

    /**
     * Signs payload using HMAC SHA256 for authentication.
     * 
     * @param {Object} payload - Bundle payload
     * @returns {string|null} HMAC signature or null
     */
    signPayload(payload) {
        if (!this.secret) return null;
        return crypto
            .createHmac('sha256', this.secret)
            .update(JSON.stringify(payload))
            .digest('hex');
    }

    /**
     * Submit a private bundle to bloXroute MEV relay.
     * 
     * @param {Array<string>} transactions - Array of signed raw transactions (hex strings)
     * @param {number} blockNumber - Current block number
     * @param {Object} options - Additional options
     * @param {string} options.merkleRoot - Optional Merkle root for bundle integrity
     * @param {boolean} options.avoidMempool - Prevent mempool inclusion (default: true)
     * 
     * @returns {Promise<Object>} bloXroute response
     */
    async submitBundle(transactions, blockNumber, options = {}) {
        const {
            merkleRoot = null,
            avoidMempool = true
        } = options;
        
        console.log("🚀 [BLOXROUTE] Submitting private bundle...");
        console.log(`   Chain: ${this.endpoint.network} (${this.chainId})`);
        console.log(`   Transactions: ${transactions.length}`);
        console.log(`   Target Block: ${blockNumber + 1}`);
        if (merkleRoot) {
            console.log(`   Merkle Root: ${merkleRoot}`);
        }

        // Build payload
        const params = {
            transaction: transactions,
            blockchain_network: this.endpoint.network,
            block_number: blockNumber + 1,  // Target next block
            avoid_mempool: avoidMempool
        };
        
        // Add Merkle root if provided
        if (merkleRoot) {
            params.merkle_root = merkleRoot;
        }
        
        const payload = {
            jsonrpc: "2.0",
            method: "blxr_submit_bundle",
            params: params,
            id: Date.now()
        };

        // Sign payload
        const signature = this.signPayload(payload);
        
        // Build headers
        const headers = {
            'Content-Type': 'application/json'
        };
        
        if (this.authHeader) {
            headers['Authorization'] = this.authHeader;
        }
        
        if (signature) {
            headers['X-Request-Signature'] = signature;
        }

        // Build HTTPS request options
        const options_https = {
            hostname: this.endpoint.hostname,
            port: 443,
            path: '/',
            method: 'POST',
            headers: headers,
            cert: this.hasCerts ? this.cert : undefined,
            key: this.hasCerts ? this.key : undefined,
            rejectUnauthorized: false
        };

        return new Promise((resolve, reject) => {
            const req = https.request(options_https, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        const response = JSON.parse(data);
                        
                        // Log response
                        if (response.result) {
                            console.log(`✅ [BLOXROUTE] Bundle submitted successfully`);
                            console.log(`   Bundle Hash: ${response.result.bundleHash || 'N/A'}`);
                        } else if (response.error) {
                            console.error(`❌ [BLOXROUTE] Submission failed: ${response.error.message}`);
                        }
                        
                        resolve(response);
                    } catch (parseError) {
                        console.warn(`⚠️ [BLOXROUTE] Non-JSON response: ${data}`);
                        resolve({ raw: data });
                    }
                });
            });
            
            req.on('error', (e) => {
                console.error(`❌ [BLOXROUTE] Request failed: ${e.message}`);
                reject(e);
            });
            
            req.write(JSON.stringify(payload));
            req.end();
        });
    }
    
    /**
     * Check if bloXroute is properly configured.
     * 
     * @returns {boolean} True if auth header is configured
     */
    isConfigured() {
        return !!this.authHeader;
    }
    
    /**
     * Get configuration status summary.
     * 
     * @returns {Object} Configuration status
     */
    getConfigStatus() {
        return {
            configured: this.isConfigured(),
            hasCerts: this.hasCerts,
            hasSecret: !!this.secret,
            endpoint: this.endpoint.hostname,
            network: this.endpoint.network
        };
    }
}

module.exports = { BloxRouteManager };