# Full-Scale Transaction Flow Test

## Overview

The `test_full_scale_transaction.js` test validates the complete end-to-end transaction execution pipeline in the Titan system, covering all 7 critical stages from signal generation to bloXroute MEV relay submission.

## Test Flow

```
Signal → Chain Gate → TX Builder → Simulation → TX Signer → Merkle Bundle → bloXroute
```

### Stage Details

#### 1. **Signal Generation and Validation** 📡
- Creates a realistic trading signal matching bot.js structure
- Validates signal fields (chainId, token, amount)
- Verifies token address format
- Tests: Signal structure validation, address verification

#### 2. **Chain Execution Gate (3 Gates)** 🚧
- **Gate 1**: Validates Polygon (137) execution is ENABLED
- **Gate 2**: Validates Ethereum (1) execution is BLOCKED
- **Gate 3**: Validates Arbitrum (42161) execution is BLOCKED
- Tests: Chain execution permissions, security gates

#### 3. **Transaction Builder (32KB Calldata Limit)** 🔨
- Builds unsigned EIP-1559 transaction
- Validates calldata size ≤ 32KB (bloXroute requirement)
- Tests gas parameters and transaction structure
- Tests: Calldata limit enforcement, bloXroute compatibility

#### 4. **Transaction Simulation (Safety Validation)** 🔬
- Validates transaction structure for simulation
- Checks gas limit sufficiency
- Verifies target contract address
- Tests: Simulation readiness (dry-run mode)

#### 5. **Transaction Signing (3-Gate Integrity)** ✍️
- **Gate 1**: Blocks PAPER mode signing
- **Gate 2**: Blocks non-Polygon chain signing
- **Gate 3**: Allows Polygon LIVE mode signing
- Tests: Execution mode gating, chain gating, signing integrity

#### 6. **Merkle Bundle Construction (MEV Protection)** 🌳
- Builds Merkle tree from signed transactions
- Generates Merkle root for bundle integrity
- Creates and verifies Merkle proofs
- Tests: Bundle construction, proof verification, integrity

#### 7. **bloXroute Submission (MEV Relay)** 🚀
- Validates bloXroute configuration
- Prepares bundle submission payload
- Checks endpoint, network, authentication
- Tests: Submission readiness (dry-run mode, no actual submission)

## Running the Test

### Quick Run
```bash
npm run test:full-scale
```

### Direct Execution
```bash
node test_full_scale_transaction.js
```

### Alternative
```bash
./test_full_scale_transaction.js
```

## Test Output

The test produces detailed output for each stage:

```
╔════════════════════════════════════════════════════════════════╗
║       TITAN FULL-SCALE TRANSACTION FLOW TEST                   ║
║  Signal → Chain Gate → TX Builder → Simulation →               ║
║  TX Signer → Merkle Bundle → bloXroute                         ║
╚════════════════════════════════════════════════════════════════╝

📡 STAGE 1: SIGNAL GENERATION AND VALIDATION
✅ PASS: Signal generation and validation

🚧 STAGE 2: CHAIN EXECUTION GATE (3 Gates)
✅ PASS: Chain execution gates (3 gates validated)

🔨 STAGE 3: TRANSACTION BUILDER (32KB Max Calldata)
✅ PASS: Transaction builder (32KB validation)
✅ PASS: 32KB limit enforcement

🔬 STAGE 4: TRANSACTION SIMULATION (Safety Check)
✅ PASS: Transaction simulation readiness

✍️ STAGE 5: TRANSACTION SIGNING (3-Gate Integrity)
✅ PASS: Transaction signing (3 gates validated)

🌳 STAGE 6: MERKLE BUNDLE CONSTRUCTION (MEV Protection)
✅ PASS: Merkle bundle construction and verification

🚀 STAGE 7: BLOXROUTE SUBMISSION (MEV Relay)
✅ PASS: bloXroute submission readiness

═══════════════════════════════════════════════════════════════
✅ ALL TESTS PASSED - Full-scale transaction flow operational!
═══════════════════════════════════════════════════════════════
```

## Success Criteria

- **8/8 tests must pass** for full validation
- All security gates must function correctly
- All components must be properly integrated
- 100% success rate required

## Test Coverage

### Security Guarantees Verified ✓
- Only Polygon (137) can execute transactions
- Ethereum and Arbitrum execution blocked
- 32KB calldata limit enforced
- PAPER mode signing blocked
- Merkle bundle integrity verified
- bloXroute MEV protection enabled

### Components Tested
- `execution/tx_builder.js` - Transaction building
- `execution/tx_signer.js` - Transaction signing with gates
- `execution/merkle_builder.js` - Merkle tree construction
- `execution/bloxroute_manager.js` - MEV relay integration

### Test Modes

#### Dry-Run Mode (Default)
- No actual blockchain interaction
- No bloXroute submission
- Validates structure and logic only
- Safe for CI/CD pipelines

#### Production Validation
The test validates readiness for:
- Live transaction execution (Polygon only)
- bloXroute MEV bundle submission
- Multi-transaction bundle construction
- Full transaction pipeline operation

## Prerequisites

### Required
- Node.js ≥ 18.0.0
- npm dependencies installed (`npm install`)

### Optional (for bloXroute)
- `BLOXROUTE_AUTH` in `.env` for auth header
- bloXroute certificates in `certs/` directory
- `BLOX_HASH_SECRET` for HMAC signing

## Exit Codes

- `0` - All tests passed
- `1` - One or more tests failed

## Integration with CI/CD

This test can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run full-scale transaction test
  run: npm run test:full-scale
```

## Troubleshooting

### Common Issues

1. **Module not found errors**
   ```bash
   npm install
   ```

2. **bloXroute auth warnings**
   - Optional for testing
   - Add `BLOXROUTE_AUTH` to `.env` for production

3. **Test failures**
   - Check execution gates are properly configured
   - Verify transaction builder limits
   - Review error messages for specific failures

## Related Files

- `test_execution_system.js` - Component-level execution tests
- `execution/bot.js` - Production bot implementation
- `core/chain_registry.py` - Chain execution configuration

## Notes

- Test runs in **DRY-RUN mode** by default (no blockchain interaction)
- Actual bloXroute submission is **SKIPPED** (structure validation only)
- Transaction simulation uses mock data (no RPC calls)
- All security gates are tested with real logic
- Merkle proof verification uses actual cryptographic functions

## Maintenance

When updating the transaction pipeline:
1. Update corresponding test stages
2. Ensure all 8 tests still pass
3. Verify security guarantees remain intact
4. Update documentation if flow changes

## Contact

For issues or questions about this test:
- Review test output for specific failure details
- Check component files for implementation details
- Consult TITAN documentation for architecture overview
