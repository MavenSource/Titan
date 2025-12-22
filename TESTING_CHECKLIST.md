# Testing Checklist for Mainnet Safety Improvements

## Overview

This checklist covers all critical test scenarios for the mainnet safety improvements. Complete all tests on testnet before considering mainnet deployment.

> **📋 Master Validation:** This checklist is part of the comprehensive [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) system validation framework.
> 
> **📋 Related Documents:**
> - [GO_LIVE_CHECKLIST.md](GO_LIVE_CHECKLIST.md) - Full-scale deployment validation
> - [CHECKLIST_VALIDATION_SUMMARY.md](CHECKLIST_VALIDATION_SUMMARY.md) - Executive validation summary

---

## 1. Configuration & Startup Tests

### 1.1 Valid Configuration
- [ ] Start system with valid configuration
- [ ] Verify all RPC connections succeed
- [ ] Confirm Redis connection established
- [ ] Check all chains are reachable
- [ ] Verify wallet balance check works

### 1.2 Invalid Configuration
- [ ] Test with missing private key
- [ ] Test with invalid private key format
- [ ] Test with missing executor address
- [ ] Test with invalid executor address format
- [ ] Test with invalid MAX_BASE_FEE_GWEI
- [ ] Verify startup fails with clear error messages

### 1.3 Missing Dependencies
- [ ] Test with Redis not running
- [ ] Test with invalid RPC endpoints
- [ ] Verify retry logic activates
- [ ] Confirm graceful degradation works

**Expected Results:**
- Valid config: System starts successfully
- Invalid config: Clear error, system exits with code 1
- Missing deps: Retry logic attempts reconnection

---

## 2. Redis Communication Tests

### 2.1 Normal Operation
- [ ] Verify Brain can connect to Redis
- [ ] Verify Bot can subscribe to channel
- [ ] Test signal publishing from Brain
- [ ] Test signal reception in Bot
- [ ] Confirm signal parsing works

### 2.2 Connection Failures
- [ ] Stop Redis during operation
- [ ] Verify retry logic activates
- [ ] Confirm exponential backoff works
- [ ] Check max retry limit (5 attempts)
- [ ] Verify system doesn't crash

### 2.3 Reconnection
- [ ] Stop Redis, wait 30 seconds, restart
- [ ] Verify Brain reconnects automatically
- [ ] Verify Bot reconnects successfully
- [ ] Test signal flow after reconnection
- [ ] Confirm no message loss on critical signals

**Expected Results:**
- Normal: Seamless communication
- Failures: Retry with backoff, max 10 second delay
- Reconnection: Automatic recovery within 1 scan cycle

---

## 3. Gas Price Validation Tests

### 3.1 Normal Gas Prices
- [ ] Test with gas at 20 gwei
- [ ] Test with gas at 50 gwei
- [ ] Test with gas at 100 gwei
- [ ] Verify transactions execute normally
- [ ] Check gas costs are calculated correctly

### 3.2 High Gas Prices
- [ ] Simulate gas at 250 gwei
- [ ] Simulate gas at 500 gwei (ceiling)
- [ ] Simulate gas above 500 gwei
- [ ] Verify capping works in Brain
- [ ] Verify capping works in GasManager
- [ ] Confirm transactions rejected above ceiling

### 3.3 Gas Price Strategies
- [ ] Test 'SLOW' strategy (1 gwei priority)
- [ ] Test 'STANDARD' strategy (2 gwei priority)
- [ ] Test 'RAPID' strategy (5 gwei priority)
- [ ] Verify priority fees are capped correctly
- [ ] Check maxFeePerGas calculations

**Expected Results:**
- Normal: Appropriate fees calculated
- High: Capped at MAX_BASE_FEE_GWEI (500 gwei)
- Above ceiling: Transactions not submitted

---

## 4. Transaction Execution Tests

### 4.1 Valid Transactions
- [ ] Execute simple arbitrage on testnet
- [ ] Verify simulation passes
- [ ] Confirm transaction is submitted
- [ ] Check transaction gets confirmed
- [ ] Verify monitoring logs success
- [ ] Calculate actual profit vs expected

### 4.2 Invalid Transactions
- [ ] Test with zero address router
- [ ] Test with invalid token address
- [ ] Test with mismatched array lengths
- [ ] Test with unsupported protocol
- [ ] Verify all reject before submission

### 4.3 Simulation Failures
- [ ] Force simulation to fail
- [ ] Verify transaction is NOT submitted
- [ ] Check appropriate error is logged
- [ ] Confirm no gas is wasted
- [ ] Test consecutive_failures counter

### 4.4 Execution Errors
- [ ] Test with insufficient wallet balance
- [ ] Test with nonce conflict
- [ ] Test with gas estimation failure
- [ ] Test with network timeout
- [ ] Verify proper error classification

**Expected Results:**
- Valid: Successful execution and confirmation
- Invalid: Rejected during validation
- Simulation fail: Not submitted
- Execution errors: Proper classification and logging

---

## 5. Slippage & Profit Validation Tests

### 5.1 Slippage Limits
- [ ] Test AI recommends 50 bps slippage (valid)
- [ ] Test AI recommends 100 bps slippage (max valid)
- [ ] Test AI recommends 150 bps slippage (too high)
- [ ] Verify capping to MAX_SLIPPAGE_BPS (100)
- [ ] Confirm warning is logged for capped values

### 5.2 Profit Threshold
- [ ] Test opportunity with $10 profit (valid)
- [ ] Test opportunity with $5 profit (minimum valid)
- [ ] Test opportunity with $3 profit (too low)
- [ ] Verify rejection below MIN_PROFIT_THRESHOLD_USD
- [ ] Check debug logging for rejected trades

### 5.3 Profit Calculations
- [ ] Verify gross spread calculation
- [ ] Check gas cost calculation accuracy
- [ ] Validate bridge fee deduction
- [ ] Confirm net profit formula
- [ ] Compare expected vs actual profits

**Expected Results:**
- Slippage: Capped at 1% maximum
- Profit: Minimum $5 enforced
- Calculations: Accurate within 5%

---

## 6. Bridge Route Validation Tests

### 6.1 Valid Routes
- [ ] Test USDC bridge Polygon → Arbitrum
- [ ] Test WETH bridge Ethereum → Optimism
- [ ] Verify route availability check
- [ ] Check bridge fee calculation
- [ ] Confirm quote structure validation

### 6.2 Invalid Routes
- [ ] Test bridge with unavailable route
- [ ] Test with missing bridge quote fields
- [ ] Test with excessive bridge fee (>5%)
- [ ] Test with zero address token
- [ ] Verify rejection before execution

### 6.3 Chain Compatibility
- [ ] Test Curve on Arbitrum (not available)
- [ ] Test Uniswap on BSC (not available)
- [ ] Verify zero address checking works
- [ ] Confirm fallback to available DEXs

**Expected Results:**
- Valid: Routes executed successfully
- Invalid: Rejected with clear reason
- Compatibility: Zero addresses detected and skipped

---

## 7. Circuit Breaker Tests

### 7.1 Normal Operation
- [ ] Execute 5 successful trades
- [ ] Verify consecutive_failures stays at 0
- [ ] Confirm no circuit breaker triggers

### 7.2 Failure Scenarios
- [ ] Force 5 consecutive failures
- [ ] Verify counter increments correctly
- [ ] Force 10 consecutive failures
- [ ] Confirm circuit breaker triggers
- [ ] Check 60-second cooldown activates
- [ ] Verify counter resets after cooldown

### 7.3 Recovery
- [ ] Trigger circuit breaker
- [ ] Wait for cooldown
- [ ] Execute successful trade
- [ ] Verify counter resets to 0
- [ ] Confirm normal operation resumes

**Expected Results:**
- Normal: No triggering
- Failures: Triggers at 10 consecutive
- Recovery: Resets after cooldown + success

---

## 8. Smart Contract Safety Tests

### 8.1 Valid Swaps
- [ ] Test Uniswap V3 swap (fee 500)
- [ ] Test Curve swap (valid indices)
- [ ] Test 2-hop route
- [ ] Test 5-hop route (maximum)
- [ ] Verify all execute successfully

### 8.2 Invalid Parameters
- [ ] Test invalid Uniswap fee (e.g., 250)
- [ ] Test Curve index out of range (e.g., 10)
- [ ] Test same token Curve swap (i == j)
- [ ] Test zero address router
- [ ] Test 6-hop route (too long)
- [ ] Verify all revert with clear errors

### 8.3 Safety Checks
- [ ] Test swap that returns zero
- [ ] Test route that loses >50%
- [ ] Test with empty arrays
- [ ] Test with mismatched array lengths
- [ ] Verify all trigger appropriate reverts

### 8.4 Deadline Tests
- [ ] Execute normal swap within deadline
- [ ] Simulate delayed execution past deadline
- [ ] Test setSwapDeadline() function
- [ ] Try invalid deadlines (<60s, >600s)
- [ ] Verify range validation works

**Expected Results:**
- Valid: Successful execution
- Invalid: Revert with descriptive error
- Safety: Caught before completion
- Deadline: Enforced correctly

---

## 9. Nonce Management Tests

### 9.1 Normal Operation
- [ ] Execute 3 transactions sequentially
- [ ] Verify nonces increment correctly
- [ ] Check no gaps in nonce sequence
- [ ] Confirm all transactions confirm

### 9.2 Concurrent Transactions
- [ ] Submit 3 transactions simultaneously
- [ ] Verify each gets unique nonce
- [ ] Check all transactions execute
- [ ] Confirm no nonce conflicts

### 9.3 Nonce Conflicts
- [ ] Simulate NONCE_EXPIRED error
- [ ] Test REPLACEMENT_UNDERPRICED scenario
- [ ] Verify proper error detection
- [ ] Test sync_with_chain() recovery
- [ ] Confirm successful retry

### 9.4 Chain Synchronization
- [ ] Create nonce mismatch artificially
- [ ] Call sync_with_chain()
- [ ] Verify nonce cache updated
- [ ] Check pending nonces cleared
- [ ] Confirm normal operation resumes

**Expected Results:**
- Normal: Sequential nonce assignment
- Concurrent: Unique nonces per transaction
- Conflicts: Detected and logged
- Sync: Successful recovery

---

## 10. MEV Protection Tests

### 10.1 BloxRoute Submission
- [ ] Test on Polygon with valid auth
- [ ] Test on BSC with valid auth
- [ ] Verify bundle submission succeeds
- [ ] Check bundle ID is returned
- [ ] Confirm transaction included

### 10.2 BloxRoute Failures
- [ ] Test with invalid auth
- [ ] Test with network error
- [ ] Verify fallback to public mempool
- [ ] Confirm transaction still executes
- [ ] Check proper logging of fallback

### 10.3 Public Mempool
- [ ] Test on Ethereum (no BloxRoute)
- [ ] Test on Optimism (no BloxRoute)
- [ ] Verify direct submission works
- [ ] Confirm transaction monitoring active

**Expected Results:**
- BloxRoute: Used on Polygon/BSC when configured
- Failures: Graceful fallback to public mempool
- Public: Direct submission on other chains

---

## 11. Monitoring & Logging Tests

### 11.1 Normal Logging
- [ ] Check debug logs are detailed
- [ ] Verify info logs are clear
- [ ] Confirm warning logs on issues
- [ ] Check error logs on failures
- [ ] Verify timestamps are correct

### 11.2 Transaction Monitoring
- [ ] Execute transaction
- [ ] Verify monitoring starts automatically
- [ ] Check confirmation logging
- [ ] Verify gas cost calculation
- [ ] Confirm profit comparison logged

### 11.3 Status Tracking
- [ ] Check execution status logging
- [ ] Verify duration measurements
- [ ] Confirm status codes are correct
- [ ] Check error classification

**Expected Results:**
- Comprehensive logs at all levels
- Clear, actionable error messages
- Accurate timing and status tracking

---

## 12. Performance & Load Tests

### 12.1 Opportunity Scanning
- [ ] Scan 100+ opportunities
- [ ] Verify parallel evaluation works
- [ ] Check no deadlocks occur
- [ ] Monitor memory usage
- [ ] Confirm scan completes <5 seconds

### 12.2 High Frequency
- [ ] Execute 10 trades in 1 minute
- [ ] Verify no nonce conflicts
- [ ] Check gas estimation stays accurate
- [ ] Monitor for memory leaks
- [ ] Confirm consistent performance

### 12.3 Long Running
- [ ] Run system for 1 hour continuously
- [ ] Execute 20+ trades
- [ ] Monitor resource usage
- [ ] Check for degradation
- [ ] Verify no crashes or hangs

**Expected Results:**
- Fast scanning (<5s per cycle)
- No conflicts in high frequency
- Stable long-term operation

---

## 13. Integration Tests

### 13.1 End-to-End Flow
- [ ] Brain detects opportunity
- [ ] Profit validation passes
- [ ] Signal broadcast to Redis
- [ ] Bot receives signal
- [ ] Simulation executes
- [ ] Transaction submits
- [ ] Confirmation received
- [ ] Profit realized

### 13.2 Multi-Chain Operation
- [ ] Test on Polygon
- [ ] Test on Arbitrum
- [ ] Test on Ethereum
- [ ] Test on Base
- [ ] Verify all chains work independently

### 13.3 Cross-Chain Bridge
- [ ] Detect cross-chain opportunity
- [ ] Get bridge quote from Li.Fi
- [ ] Validate bridge feasibility
- [ ] (Manual) Execute bridge transaction
- [ ] Verify arrival on destination chain

**Expected Results:**
- Seamless end-to-end execution
- All chains operational
- Bridge integration functional

---

## 14. Failure Recovery Tests

### 14.1 Graceful Shutdown
- [ ] Send SIGINT to bot
- [ ] Verify Redis connection closes
- [ ] Check no transactions left pending
- [ ] Confirm clean exit

### 14.2 Ungraceful Shutdown
- [ ] Kill -9 the bot process
- [ ] Restart the system
- [ ] Verify nonce synchronization
- [ ] Check no duplicate transactions
- [ ] Confirm recovery is clean

### 14.3 Network Interruptions
- [ ] Disconnect network during scan
- [ ] Reconnect after 30 seconds
- [ ] Verify retry logic activates
- [ ] Check recovery succeeds
- [ ] Confirm normal operation resumes

**Expected Results:**
- Graceful: Clean shutdown
- Ungraceful: Successful recovery
- Network: Automatic reconnection

---

## Acceptance Criteria

For testnet approval, the system must:

✅ **Configuration:** All invalid configs rejected with clear errors  
✅ **Redis:** Survives disconnection and reconnects automatically  
✅ **Gas Prices:** Properly capped at configured maximum  
✅ **Transactions:** Valid transactions execute, invalid rejected  
✅ **Slippage:** AI recommendations properly validated and capped  
✅ **Profit:** Minimum threshold enforced consistently  
✅ **Circuit Breaker:** Triggers after 10 failures, recovers correctly  
✅ **Smart Contract:** All safety checks working  
✅ **Nonces:** No conflicts in concurrent scenarios  
✅ **MEV:** BloxRoute fallback works correctly  
✅ **Monitoring:** Comprehensive logging present  
✅ **Performance:** Handles 10+ trades/minute without issues  
✅ **Recovery:** Survives all failure scenarios  

---

## Mainnet Readiness Checklist

Before mainnet deployment with real funds:

- [ ] All testnet tests pass
- [ ] Professional security audit completed
- [ ] Economic analysis validated
- [ ] Legal compliance reviewed
- [ ] Monitoring systems deployed
- [ ] Alert systems configured
- [ ] Emergency shutdown procedure tested
- [ ] Team trained on operations
- [ ] Documentation complete
- [ ] Insurance/risk management in place

---

## Test Execution Log

| Test Category | Status | Date | Tester | Notes |
|--------------|--------|------|--------|-------|
| Configuration | ⏳ Pending | - | - | - |
| Redis Comm | ⏳ Pending | - | - | - |
| Gas Prices | ⏳ Pending | - | - | - |
| Transactions | ⏳ Pending | - | - | - |
| Slippage | ⏳ Pending | - | - | - |
| Bridge Routes | ⏳ Pending | - | - | - |
| Circuit Breaker | ⏳ Pending | - | - | - |
| Smart Contract | ⏳ Pending | - | - | - |
| Nonce Mgmt | ⏳ Pending | - | - | - |
| MEV Protection | ⏳ Pending | - | - | - |
| Monitoring | ⏳ Pending | - | - | - |
| Performance | ⏳ Pending | - | - | - |
| Integration | ⏳ Pending | - | - | - |
| Recovery | ⏳ Pending | - | - | - |

---

**Status Legend:**
- ⏳ Pending
- 🔄 In Progress
- ✅ Passed
- ❌ Failed
- ⚠️ Partial

**Last Updated:** 2025-12-09
