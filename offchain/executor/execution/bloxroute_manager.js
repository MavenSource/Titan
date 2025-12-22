require('dotenv').config();
const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

class BloxRouteManager {
    constructor() {
        this.authHeader = process.env.BLOXROUTE_AUTH;
        this.secret = process.env.BLOX_HASH_SECRET; // From secret_hash.txt
        
        // Load Certificates
        try {
            this.cert = fs.readFileSync(path.join(__dirname, '../certs/external_gateway_cert.pem'));
            this.key = fs.readFileSync(path.join(__dirname, '../certs/external_gateway_key.pem'));
            this.hasCerts = true;
        } catch (e) {
            console.warn("⚠️ BloxRoute Certs not found. Running in Auth-Header Mode only.");
            this.hasCerts = false;
        }
    }

    /**
     * Signs payload using HMAC SHA256 (Logic from mev_module_merkle_blox.py)
     */
    signPayload(payload) {
        if (!this.secret) return null;
        return crypto
            .createHmac('sha256', this.secret)
            .update(JSON.stringify(payload))
            .digest('hex');
    }

    async submitBundle(transactions, blockNumber) {
        console.log("🚀 Submitting Private Bundle to BloxRoute...");

        const payload = {
            id: "1",
            jsonrpc: "2.0",
            method: "blxr_submit_bundle",
            params: {
                transaction: transactions, 
                block_number: "0x" + (blockNumber + 1).toString(16),
                min_timestamp: 0,
                max_timestamp: 0,
                mev_builders: { "all": "" }
            }
        };

        const signature = this.signPayload(payload);
        
        const headers = {
            'Content-Type': 'application/json',
            'Authorization': this.authHeader
        };
        
        if (signature) {
            headers['X-Request-Signature'] = signature;
        }

        const options = {
            hostname: 'virginia.eth.blxrbdn.com', 
            port: 443,
            path: '/',
            method: 'POST',
            headers: headers,
            cert: this.hasCerts ? this.cert : undefined,
            key: this.hasCerts ? this.key : undefined,
            rejectUnauthorized: false
        };

        return new Promise((resolve, reject) => {
            const req = https.request(options, (res) => {
                let data = '';
                res.on('data', (chunk) => data += chunk);
                res.on('end', () => {
                    try {
                        resolve(JSON.parse(data));
                    } catch {
                        resolve(data);
                    }
                });
            });
            req.on('error', (e) => reject(e));
            req.write(JSON.stringify(payload));
            req.end();
        });
    }
}

module.exports = { BloxRouteManager };