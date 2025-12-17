/**
 * TITAN TRANSACTION BUILDER
 * ==========================
 * 
 * Production-grade EIP-1559 transaction construction with safety guarantees:
 * 
 * - 32KB calldata size enforcement
 * - Chain-scoped transaction building
 * - Gas estimation with safety margins
 * - No signing (separation of concerns)
 * 
 * This module builds unsigned transaction objects.
 * Signing is handled by tx_signer.js with execution gating.
 */

const { ethers } = require('ethers');

// CONSTANTS
const MAX_CALLDATA_BYTES = 32000;  // 32KB limit for bloXroute and general safety
const GAS_BUFFER_MULTIPLIER = 1.15; // 15% safety margin on gas estimates

class TransactionBuilder {
    /**
     * Build an unsigned EIP-1559 transaction.
     * 
     * @param {Object} params - Transaction parameters
     * @param {number} params.chainId - Chain ID (137 for Polygon, etc.)
     * @param {string} params.to - Contract address
     * @param {string} params.data - Encoded calldata (hex string)
     * @param {string|bigint} params.value - Native token value (default: 0)
     * @param {bigint} params.gasLimit - Gas limit
     * @param {bigint} params.maxFeePerGas - Max fee per gas (EIP-1559)
     * @param {bigint} params.maxPriorityFeePerGas - Max priority fee (EIP-1559)
     * @param {number} params.nonce - Transaction nonce
     * 
     * @returns {Object} Unsigned transaction object
     * @throws {Error} If calldata exceeds 32KB or validation fails
     */
    static buildTransaction({
        chainId,
        to,
        data,
        value = 0,
        gasLimit,
        maxFeePerGas,
        maxPriorityFeePerGas,
        nonce
    }) {
        // Validate required fields
        if (!chainId) {
            throw new Error('chainId is required');
        }
        if (!to || !ethers.isAddress(to)) {
            throw new Error(`Invalid 'to' address: ${to}`);
        }
        if (!data) {
            throw new Error('data (calldata) is required');
        }
        
        // Validate calldata size (CRITICAL)
        const calldataBytes = ethers.getBytes(data).length;
        if (calldataBytes > MAX_CALLDATA_BYTES) {
            throw new Error(
                `Calldata size ${calldataBytes} bytes exceeds 32KB limit (${MAX_CALLDATA_BYTES} bytes)`
            );
        }
        
        // Validate gas parameters
        if (!gasLimit || gasLimit <= 0n) {
            throw new Error('gasLimit must be positive');
        }
        if (!maxFeePerGas || maxFeePerGas <= 0n) {
            throw new Error('maxFeePerGas must be positive');
        }
        if (!maxPriorityFeePerGas || maxPriorityFeePerGas <= 0n) {
            throw new Error('maxPriorityFeePerGas must be positive');
        }
        if (maxPriorityFeePerGas > maxFeePerGas) {
            throw new Error('maxPriorityFeePerGas cannot exceed maxFeePerGas');
        }
        
        // Validate nonce
        if (nonce === undefined || nonce === null || nonce < 0) {
            throw new Error('nonce must be non-negative');
        }
        
        // Build EIP-1559 transaction
        const tx = {
            type: 2,  // EIP-1559
            chainId,
            to,
            data,
            value: BigInt(value),
            gasLimit,
            maxFeePerGas,
            maxPriorityFeePerGas,
            nonce
        };
        
        return tx;
    }
    
    /**
     * Estimate gas limit with safety buffer.
     * 
     * @param {Object} provider - ethers provider
     * @param {Object} tx - Transaction object
     * @param {number} bufferMultiplier - Safety margin multiplier (default: 1.15)
     * 
     * @returns {Promise<bigint>} Estimated gas limit with buffer
     */
    static async estimateGasWithBuffer(provider, tx, bufferMultiplier = GAS_BUFFER_MULTIPLIER) {
        try {
            const estimatedGas = await provider.estimateGas(tx);
            const bufferedGas = (estimatedGas * BigInt(Math.floor(bufferMultiplier * 100))) / 100n;
            
            return bufferedGas;
        } catch (error) {
            throw new Error(`Gas estimation failed: ${error.message}`);
        }
    }
    
    /**
     * Validate transaction size is suitable for bloXroute submission.
     * 
     * bloXroute has strict size limits for bundle submission.
     * This validates the transaction meets those requirements.
     * 
     * @param {Object} tx - Transaction object
     * @returns {boolean} True if transaction is bloXroute-compatible
     */
    static isBloxRouteCompatible(tx) {
        if (!tx || !tx.data) {
            return false;
        }
        
        const calldataBytes = ethers.getBytes(tx.data).length;
        
        // bloXroute bundle size limits
        const BLOXROUTE_MAX_CALLDATA = 32000;  // 32KB
        
        return calldataBytes <= BLOXROUTE_MAX_CALLDATA;
    }
    
    /**
     * Calculate transaction size metrics.
     * 
     * @param {Object} tx - Transaction object
     * @returns {Object} Size metrics
     */
    static getTransactionMetrics(tx) {
        const calldataBytes = tx.data ? ethers.getBytes(tx.data).length : 0;
        
        return {
            calldataBytes,
            calldataSizeKB: (calldataBytes / 1024).toFixed(2),
            isWithinLimit: calldataBytes <= MAX_CALLDATA_BYTES,
            isBloxRouteCompatible: this.isBloxRouteCompatible(tx)
        };
    }
}

module.exports = { TransactionBuilder, MAX_CALLDATA_BYTES };
