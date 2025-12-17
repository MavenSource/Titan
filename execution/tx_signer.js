/**
 * TITAN TRANSACTION SIGNER
 * =========================
 * 
 * Production-grade transaction signing with STRICT execution gating.
 * 
 * CRITICAL GUARANTEES:
 * - Only Polygon (chainId 137) transactions can be signed
 * - Ethereum (1) and Arbitrum (42161) are HARD-BLOCKED
 * - All other chains are rejected with explicit errors
 * - Execution mode validation (LIVE only)
 * 
 * This is the final execution gate before blockchain submission.
 */

const { ethers } = require('ethers');

// EXECUTION GATES
const EXECUTION_ENABLED_CHAINS = [137];  // Only Polygon
const CONFIGURED_CHAINS = [1, 137, 42161];  // Ethereum, Polygon, Arbitrum

const CHAIN_NAMES = {
    1: 'Ethereum',
    137: 'Polygon',
    42161: 'Arbitrum'
};

class TransactionSigner {
    /**
     * Sign a transaction with strict execution gating.
     * 
     * @param {Object} tx - Unsigned transaction object
     * @param {Object} wallet - ethers Wallet instance
     * @param {string} executionMode - PAPER or LIVE
     * 
     * @returns {Promise<string>} Signed transaction (raw hex)
     * @throws {Error} If execution is not allowed
     */
    static async signTransaction(tx, wallet, executionMode = 'PAPER') {
        // GATE 1: Execution mode check
        if (executionMode !== 'LIVE') {
            throw new Error(
                `Transaction signing blocked: Execution mode is ${executionMode}. ` +
                `Only LIVE mode can sign transactions.`
            );
        }
        
        // GATE 2: Chain validation
        if (!tx.chainId) {
            throw new Error('Transaction missing chainId - cannot validate execution permissions');
        }
        
        // GATE 3: Chain execution gate (CRITICAL)
        if (!EXECUTION_ENABLED_CHAINS.includes(tx.chainId)) {
            const chainName = CHAIN_NAMES[tx.chainId] || `Chain ${tx.chainId}`;
            
            // Different error messages for different chain states
            if (CONFIGURED_CHAINS.includes(tx.chainId)) {
                // Chain is configured but execution disabled
                throw new Error(
                    `[EXECUTION BLOCKED] ${chainName} (${tx.chainId}) execution is DISABLED. ` +
                    `Only Polygon (137) can execute transactions. ` +
                    `${chainName} is configured for RPC access only.`
                );
            } else {
                // Chain not configured at all
                throw new Error(
                    `[EXECUTION BLOCKED] Chain ${tx.chainId} is not configured for execution. ` +
                    `Only Polygon (137) is enabled for live execution.`
                );
            }
        }
        
        // GATE 4: Wallet validation
        if (!wallet || !wallet.signTransaction) {
            throw new Error('Invalid wallet instance provided');
        }
        
        // GATE 5: Transaction structure validation
        if (!tx.to || !ethers.isAddress(tx.to)) {
            throw new Error(`Invalid transaction recipient: ${tx.to}`);
        }
        
        if (!tx.data) {
            throw new Error('Transaction missing calldata');
        }
        
        // Log execution approval
        console.log(`✅ [TX SIGNER] Execution approved for Polygon (137)`);
        console.log(`   To: ${tx.to}`);
        console.log(`   Nonce: ${tx.nonce}`);
        console.log(`   Gas Limit: ${tx.gasLimit.toString()}`);
        
        try {
            // Sign transaction
            const signedTx = await wallet.signTransaction(tx);
            
            // Validate signed transaction
            if (!signedTx || !signedTx.startsWith('0x')) {
                throw new Error('Invalid signed transaction format');
            }
            
            console.log(`✅ [TX SIGNER] Transaction signed successfully`);
            
            return signedTx;
            
        } catch (error) {
            throw new Error(`Transaction signing failed: ${error.message}`);
        }
    }
    
    /**
     * Check if a chain is enabled for execution.
     * 
     * @param {number} chainId - Chain ID to check
     * @returns {boolean} True if execution is enabled
     */
    static isExecutionEnabled(chainId) {
        return EXECUTION_ENABLED_CHAINS.includes(chainId);
    }
    
    /**
     * Check if a chain is configured (but may not be execution-enabled).
     * 
     * @param {number} chainId - Chain ID to check
     * @returns {boolean} True if chain is configured
     */
    static isConfigured(chainId) {
        return CONFIGURED_CHAINS.includes(chainId);
    }
    
    /**
     * Get execution status for a chain.
     * 
     * @param {number} chainId - Chain ID
     * @returns {string} Status: ENABLED, CONFIGURED, or DISABLED
     */
    static getExecutionStatus(chainId) {
        if (EXECUTION_ENABLED_CHAINS.includes(chainId)) {
            return 'ENABLED';
        } else if (CONFIGURED_CHAINS.includes(chainId)) {
            return 'CONFIGURED';
        } else {
            return 'DISABLED';
        }
    }
    
    /**
     * Print execution configuration summary.
     */
    static printExecutionConfig() {
        console.log('');
        console.log('═══════════════════════════════════════════════════');
        console.log('  TRANSACTION SIGNING - EXECUTION GATES');
        console.log('═══════════════════════════════════════════════════');
        
        for (const [chainId, chainName] of Object.entries(CHAIN_NAMES)) {
            const status = this.getExecutionStatus(parseInt(chainId));
            let statusIcon;
            let statusText;
            
            if (status === 'ENABLED') {
                statusIcon = '🟢';
                statusText = 'LIVE EXECUTION ENABLED';
            } else if (status === 'CONFIGURED') {
                statusIcon = '🟡';
                statusText = 'CONFIGURED (Signing Blocked)';
            } else {
                statusIcon = '⚪';
                statusText = 'DISABLED';
            }
            
            console.log(`  ${statusIcon} ${chainName.padEnd(12)} (${chainId.toString().padStart(5)}): ${statusText}`);
        }
        
        console.log('═══════════════════════════════════════════════════');
        console.log('');
    }
}

module.exports = { TransactionSigner };
