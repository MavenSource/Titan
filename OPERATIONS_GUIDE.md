# APEX-OMEGA TITAN: Operations Guide

## Table of Contents

- [Overview](#overview)
- [Pre-Deployment Checklist](#pre-deployment-checklist)
- [Starting the System](#starting-the-system)
- [Monitoring Operations](#monitoring-operations)
- [Emergency Procedures](#emergency-procedures)
- [Troubleshooting](#troubleshooting)
- [Maintenance Tasks](#maintenance-tasks)
- [Performance Optimization](#performance-optimization)
- [Security Best Practices](#security-best-practices)

> **📋 Complete Validation Checklist:** See [VALIDATION_CHECKLIST.md](VALIDATION_CHECKLIST.md) for the master validation checklist covering all deployment readiness requirements.
>
> **📋 For Full-Scale Mainnet Deployment:** See [GO_LIVE_CHECKLIST.md](GO_LIVE_CHECKLIST.md) for a comprehensive validation of all requirements for running Titan at full scale with massive market coverage and production safeguards.

---

## Overview

This guide covers day-to-day operations of the APEX-OMEGA TITAN arbitrage system. It is designed for operators managing the system in production environments.

**Target Audience:** System operators, DevOps engineers, and trading desk personnel.

---

## Pre-Deployment Checklist

### ✅ Before First Deployment

- [ ] **System Requirements Met**
  - [ ] Node.js 18+ installed
  - [ ] Python 3.11+ installed
  - [ ] Redis server running
  - [ ] 4+ CPU cores, 8GB+ RAM
  - [ ] Stable internet (50+ Mbps)

- [ ] **Configuration Complete**
  - [ ] `.env` file configured with all required keys
  - [ ] Private key validated (64 hex characters, not placeholder)
  - [ ] RPC endpoints tested (Infura/Alchemy keys valid)
  - [ ] Li.Fi API key obtained and configured
  - [ ] Redis connection string correct

- [ ] **Dependencies Installed**
  - [ ] `npm install` completed successfully
  - [ ] `pip3 install -r requirements.txt` completed
  - [ ] `npx hardhat compile` succeeded
  - [ ] All health checks pass: `./health-check.sh`

- [ ] **Security Validation**
  - [ ] Private key stored securely (not in git)
  - [ ] Firewall configured (close unused ports)
  - [ ] SSH keys configured (disable password auth)
  - [ ] Server hardening applied

- [ ] **Testing Completed**
  - [ ] Testnet deployment successful
  - [ ] Paper trading mode tested
  - [ ] Emergency shutdown tested
  - [ ] Monitoring alerts tested

### ✅ Before Each Start

- [ ] Redis is running: `redis-cli ping`
- [ ] RPC endpoints accessible: `curl -X POST [RPC_URL]`
- [ ] Wallet has gas funds: Check balance on each chain
- [ ] No emergency shutdown marker: `ls .emergency_shutdown`
- [ ] Disk space available: `df -h` (at least 5GB free)
- [ ] System load acceptable: `uptime` (load < CPU cores)

---

## Starting the System

### Quick Start (Recommended)

```bash
# Ensure all prerequisites are met
./health-check.sh

# Start all components
./start.sh
# or
make start
```

### Manual Start (Advanced)

**Option 1: Foreground Mode (for debugging)**

```bash
# Terminal 1: Start Redis
redis-server

# Terminal 2: Start Brain (AI orchestrator)
python3 mainnet_orchestrator.py

# Terminal 3: Start Bot (execution engine)
node execution/bot.js
```

**Option 2: Background Mode (for production)**

```bash
# Start Redis as daemon
redis-server --daemonize yes

# Start Brain in background
nohup python3 mainnet_orchestrator.py > logs/brain.log 2>&1 &
echo $! > .orchestrator.pid

# Start Bot in background
nohup node execution/bot.js > logs/bot.log 2>&1 &
echo $! > .executor.pid
```

### Execution Modes

**Paper Trading Mode (Recommended for Testing)**

```bash
# Set in .env
EXECUTION_MODE=PAPER

# This mode:
# - Simulates all transactions
# - Does not spend real funds
# - Validates all logic
# - Provides realistic performance data
```

**Live Trading Mode (Production)**

```bash
# Set in .env
EXECUTION_MODE=LIVE

# This mode:
# - Executes real transactions
# - Spends real gas fees
# - Requires funded wallet
# - Use with extreme caution
```

### Verify Startup

```bash
# Check processes are running
ps aux | grep mainnet_orchestrator
ps aux | grep "node execution/bot.js"

# Check logs for errors
tail -f logs/brain.log
tail -f logs/bot.log

# Verify Redis connectivity
redis-cli PING
# Should return: PONG

# Check for opportunities being detected
redis-cli SUBSCRIBE arbitrage_signals
# Should see signals appearing
```

---

## Monitoring Operations

### Real-Time Monitoring

**Watch Logs in Real-Time:**

```bash
# Monitor brain (opportunity detection)
tail -f logs/brain.log

# Monitor bot (execution)
tail -f logs/bot.log

# Monitor both simultaneously
tail -f logs/brain.log logs/bot.log

# Filter for specific events
tail -f logs/bot.log | grep "PROFIT"
tail -f logs/bot.log | grep "ERROR"
```

### Key Metrics to Monitor

**1. Opportunity Detection Rate**
```bash
# Count opportunities per minute
grep "Opportunity found" logs/brain.log | tail -100 | wc -l
```

**Expected:** 5-15 opportunities per minute across all chains

**2. Execution Success Rate**
```bash
# Calculate success rate
ATTEMPTED=$(grep "Executing arbitrage" logs/bot.log | wc -l)
SUCCESSFUL=$(grep "Transaction confirmed" logs/bot.log | wc -l)
echo "Success Rate: $(($SUCCESSFUL * 100 / $ATTEMPTED))%"
```

**Expected:** 80-90% success rate

**3. Profitability**
```bash
# Sum daily profits
grep "Net profit" logs/bot.log | awk '{sum+=$NF} END {print "Total: $"sum}'
```

**Expected:** $200-$800 per day (moderate conditions)

**4. Gas Costs**
```bash
# Sum gas costs
grep "Gas cost" logs/bot.log | awk '{sum+=$NF} END {print "Total Gas: $"sum}'
```

**Expected:** $50-$150 per day

**5. Circuit Breaker Status**
```bash
# Check if circuit breaker has triggered
grep "Circuit breaker" logs/bot.log | tail -10
```

**Expected:** Rare triggers (0-3 per week)

### Automated Monitoring

**Set up cron job for health checks:**

```bash
# Edit crontab
crontab -e

# Add health check every 5 minutes
*/5 * * * * /path/to/Titan/health-check.sh > /tmp/health_check.log 2>&1

# Add profit summary every hour
0 * * * * grep "Net profit" /path/to/Titan/logs/bot.log | tail -50 >> /path/to/Titan/logs/hourly_summary.log
```

### Alert Thresholds

Configure alerts for:

| Metric | Warning | Critical |
|--------|---------|----------|
| System uptime | < 95% | < 90% |
| Success rate | < 75% | < 60% |
| Circuit breaker triggers | 2/hour | 5/hour |
| Consecutive failures | 5 | 10 |
| Gas price | > 300 gwei | > 500 gwei |
| Profit/loss ratio | < 2.0 | < 1.0 (losing) |
| Redis disconnects | 2/hour | 5/hour |
| RPC failures | 10/hour | 25/hour |

---

## Emergency Procedures

### Emergency Shutdown

**Immediate Stop (All Operations)**

```bash
# Run emergency shutdown script
./emergency_shutdown.sh "Reason for shutdown"

# Example reasons:
./emergency_shutdown.sh "Unusual transaction activity"
./emergency_shutdown.sh "Gas costs exceeding profit"
./emergency_shutdown.sh "Smart contract interaction failed"
./emergency_shutdown.sh "System maintenance required"
```

**What Emergency Shutdown Does:**

1. ✅ Terminates brain (orchestrator) gracefully
2. ✅ Terminates bot (executor) gracefully
3. ✅ Force-kills any orphaned processes
4. ✅ Clears Redis signal channels
5. ✅ Creates shutdown log
6. ✅ Marks system as emergency-stopped

**After Emergency Shutdown:**

```bash
# 1. Review shutdown log
cat logs/emergency_shutdown_*.log

# 2. Investigate the issue
tail -100 logs/brain.log
tail -100 logs/bot.log

# 3. Fix any problems

# 4. Remove emergency marker
rm .emergency_shutdown

# 5. Restart system
./start.sh
```

### Graceful Shutdown

**For planned maintenance:**

```bash
# Send SIGTERM to processes (allows cleanup)
kill -SIGTERM $(cat .orchestrator.pid)
kill -SIGTERM $(cat .executor.pid)

# Wait for graceful shutdown (up to 30 seconds)
sleep 10

# Verify processes stopped
ps -p $(cat .orchestrator.pid) 2>/dev/null && echo "Still running"
```

### Circuit Breaker Activation

**The system has automatic circuit breakers:**

- **Trigger:** 10 consecutive failed transactions
- **Action:** Automatically stops execution for 60 seconds
- **Recovery:** Automatic after cooldown period

**Manual Circuit Breaker Reset:**

```bash
# Clear circuit breaker state in Redis
redis-cli DEL circuit_breaker_count
redis-cli DEL circuit_breaker_timestamp

# Restart bot
kill -SIGTERM $(cat .executor.pid)
sleep 2
node execution/bot.js &
echo $! > .executor.pid
```

### Loss Prevention

**If system is losing money:**

1. **Immediate:** Run emergency shutdown
2. **Check:** Review last 50 transactions
3. **Analyze:** Calculate profit/loss ratio
4. **Identify:** Find pattern in losing trades
5. **Fix:** Adjust MIN_PROFIT_USD or disable problematic chains
6. **Test:** Run in paper mode first

```bash
# Quick profit/loss check
grep -E "Net profit|Net loss" logs/bot.log | tail -50

# Calculate last 24h performance
grep "$(date -d '1 day ago' '+%Y-%m-%d')" logs/bot.log | grep "Net profit" | awk '{sum+=$NF} END {print "24h Profit: $"sum}'
```

---

## Troubleshooting

### Common Issues

#### Issue: "Redis connection refused"

**Symptoms:**
```
Error: Redis connection refused
Brain unable to connect to Redis
```

**Solution:**
```bash
# Check if Redis is running
ps aux | grep redis-server

# If not running, start it
redis-server --daemonize yes

# Test connection
redis-cli PING

# Restart brain
kill -SIGTERM $(cat .orchestrator.pid)
python3 mainnet_orchestrator.py &
echo $! > .orchestrator.pid
```

#### Issue: "RPC endpoint not responding"

**Symptoms:**
```
Failed to connect to RPC endpoint
Timeout connecting to https://polygon-rpc.com
```

**Solution:**
```bash
# Test RPC endpoint
curl -X POST https://polygon-rpc.com \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'

# If timeout, switch to backup RPC in .env
# Update RPC_POLYGON to use Alchemy or Infura

# Restart system to pick up new config
./emergency_shutdown.sh "Switching RPC provider"
rm .emergency_shutdown
./start.sh
```

#### Issue: "Insufficient funds for gas"

**Symptoms:**
```
Error: insufficient funds for gas * price + value
Wallet balance too low
```

**Solution:**
```bash
# Check wallet balance on each chain
# Add this to a script: check_balances.sh

# For now, manually check:
# 1. Go to block explorer (polygonscan.com)
# 2. Enter your EXECUTOR_ADDRESS
# 3. Check MATIC balance
# 4. Repeat for each chain you're trading on

# Add funds to wallet
# Transfer native tokens (MATIC, ETH, etc.) to your address
```

#### Issue: "Circuit breaker activated"

**Symptoms:**
```
Circuit breaker activated after 10 consecutive failures
Execution paused for cooldown period
```

**Solution:**
```bash
# This is NORMAL and PROTECTIVE

# Check why transactions are failing
tail -100 logs/bot.log | grep "Failed"

# Common reasons:
# - Gas price too high (> MAX_BASE_FEE_GWEI)
# - Insufficient profit after gas
# - Slippage exceeded tolerance
# - MEV bots frontrunning

# Wait for cooldown (60 seconds) - system will auto-resume
# Or manually reset if issue is resolved
redis-cli DEL circuit_breaker_count
```

#### Issue: "No opportunities being detected"

**Symptoms:**
```
Brain running but no signals published
Redis channel empty
0 opportunities in last hour
```

**Solution:**
```bash
# Check market conditions (low volatility = fewer opportunities)

# Verify brain is scanning
tail -f logs/brain.log | grep "Scanning"

# Check if profit threshold is too high
grep "MIN_PROFIT_USD" .env
# Try lowering to 3.00 temporarily

# Verify RPC connections are working
grep "Connected to" logs/brain.log

# Check for errors in brain
grep "ERROR" logs/brain.log | tail -20
```

### Performance Issues

#### Issue: "Slow execution (> 20 seconds per trade)"

**Diagnosis:**
```bash
# Check system load
uptime

# Check network latency
ping -c 10 8.8.8.8

# Check RPC latency
time curl -X POST [YOUR_RPC_URL] -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

**Solutions:**
- Use faster RPC provider (Alchemy > Infura > Public)
- Reduce number of chains being scanned
- Increase server resources (CPU/RAM)
- Move server closer to RPC provider (same region)

#### Issue: "High gas costs eating profits"

**Symptoms:**
```
Gas costs: $250/day
Net profit: $150/day
Profit/loss ratio: 0.6 (losing money)
```

**Solutions:**
```bash
# 1. Increase MIN_PROFIT_USD to account for gas
# In .env, set:
MIN_PROFIT_USD=10.00

# 2. Focus on low-gas chains
# Disable Ethereum mainnet, use L2s only
# Comment out Ethereum in brain.py

# 3. Lower MAX_BASE_FEE_GWEI
# In .env, set:
MAX_BASE_FEE_GWEI=100

# 4. Use BloxRoute for MEV protection
# Reduces gas competition
BLOXROUTE_AUTH_HEADER="your-auth-token"
```

---

## Maintenance Tasks

### Daily Tasks

**Morning Checklist (5 minutes):**

```bash
# 1. Check system is running
ps aux | grep -E "mainnet_orchestrator|bot.js"

# 2. Review overnight performance
grep "$(date '+%Y-%m-%d')" logs/bot.log | grep "Net profit" | tail -20

# 3. Check for errors
grep "ERROR" logs/brain.log | tail -10
grep "ERROR" logs/bot.log | tail -10

# 4. Verify gas balance
# Check balances on block explorers

# 5. Check circuit breaker status
grep "Circuit breaker" logs/bot.log | grep "$(date '+%Y-%m-%d')"
```

**Evening Review (10 minutes):**

```bash
# Calculate daily profit
./calculate_daily_profit.sh  # Create this script

# Review success rate
EXECUTED=$(grep "$(date '+%Y-%m-%d')" logs/bot.log | grep "Executing" | wc -l)
SUCCEEDED=$(grep "$(date '+%Y-%m-%d')" logs/bot.log | grep "confirmed" | wc -l)
echo "Today: $SUCCEEDED/$EXECUTED = $((SUCCEEDED*100/EXECUTED))%"

# Check for anomalies
# - Unusual profit amounts
# - High failure rates
# - Gas price spikes
# - Circuit breaker triggers
```

### Weekly Tasks

**Sunday Maintenance (30 minutes):**

```bash
# 1. Rotate logs
cd logs
for log in *.log; do
    mv $log $log.$(date '+%Y%m%d')
    gzip $log.$(date '+%Y%m%d')
done

# 2. Clean old logs (keep 30 days)
find logs -name "*.gz" -mtime +30 -delete

# 3. Update dependencies
npm outdated
# Review and update if necessary

# 4. Backup configuration
cp .env .env.backup.$(date '+%Y%m%d')

# 5. Review performance metrics
# Create weekly report

# 6. Update documentation
# Note any operational changes
```

### Monthly Tasks

**First of Month (1 hour):**

```bash
# 1. Full system update
git pull origin main
npm install
pip3 install -r requirements.txt --upgrade
npx hardhat compile

# 2. Security audit
# - Review access logs
# - Check for unauthorized access
# - Verify private key security
# - Update firewall rules

# 3. Performance analysis
# - Calculate monthly ROI
# - Analyze most profitable chains
# - Review most profitable strategies
# - Identify optimization opportunities

# 4. Cost analysis
# - Total gas costs
# - Infrastructure costs
# - ROI calculation
# - Adjust strategy if needed

# 5. Test emergency procedures
./emergency_shutdown.sh "Monthly test"
rm .emergency_shutdown
./start.sh

# 6. Update documentation
# Document any operational changes
```

---

## Performance Optimization

### Optimize for Speed

**1. RPC Provider Selection:**
- Use paid tiers (Alchemy Growth, Infura Team)
- Select region closest to your server
- Use WebSocket connections where available
- Enable request caching

**2. Redis Optimization:**
```bash
# In redis.conf
maxmemory 2gb
maxmemory-policy allkeys-lru
save ""  # Disable persistence for speed
```

**3. System Tuning:**
```bash
# Increase file descriptors
ulimit -n 65536

# Use faster DNS
# Add to /etc/resolv.conf
nameserver 1.1.1.1
nameserver 8.8.8.8
```

### Optimize for Profitability

**1. Chain Selection:**
```python
# Focus on high-opportunity, low-gas chains
# Recommended: Polygon, Arbitrum, Base, Optimism
# Avoid: Ethereum mainnet (unless large opportunities)
```

**2. Profit Threshold Tuning:**
```bash
# Start conservative
MIN_PROFIT_USD=10.00

# After 1 week of stable operation
MIN_PROFIT_USD=7.00

# After 1 month with >90% success rate
MIN_PROFIT_USD=5.00
```

**3. Gas Strategy:**
```bash
# Use RAPID only for high-profit opportunities
# Use STANDARD for most trades
# Use SLOW for overnight/low-competition periods

# Consider time-of-day strategies:
# - US market hours: STANDARD
# - Asia market hours: SLOW
# - Europe market hours: RAPID
```

---

## Security Best Practices

### Operational Security

**1. Private Key Protection:**
```bash
# Never commit .env to git
grep "PRIVATE_KEY" .gitignore  # Should be listed

# Use environment variables instead of .env for production
export PRIVATE_KEY="0x..."

# Restrict .env file permissions
chmod 600 .env

# Store backup securely (encrypted, offline)
```

**2. Access Control:**
```bash
# Use SSH keys only
# Disable password authentication in /etc/ssh/sshd_config
PasswordAuthentication no

# Use firewall (ufw)
ufw allow 22/tcp  # SSH
ufw allow 6379/tcp  # Redis (if remote)
ufw enable

# Use fail2ban for brute force protection
apt install fail2ban
```

**3. Monitoring for Security Events:**
```bash
# Alert on unusual activity
# - Transactions to unknown addresses
# - Gas costs exceeding threshold
# - Rapid balance changes
# - Failed authentication attempts

# Monitor logs for security indicators
grep -i "unauthorized\|failed\|denied" logs/*.log
```

**4. Regular Security Audits:**
```bash
# Monthly security checklist
- [ ] Review server access logs
- [ ] Check for unauthorized processes
- [ ] Verify firewall rules
- [ ] Update system packages
- [ ] Scan for vulnerabilities
- [ ] Review smart contract interactions
- [ ] Verify wallet balance matches expectations
```

### Disaster Recovery

**1. Backup Strategy:**
```bash
# What to backup:
- Configuration files (.env, .env.example)
- Private keys (offline, encrypted)
- Historical logs (compressed)
- Performance data
- Documentation

# Backup schedule:
# Daily: Logs
# Weekly: Configuration
# Monthly: Full system backup

# Example backup script
tar -czf backup_$(date +%Y%m%d).tar.gz \
    .env \
    logs/ \
    data/ \
    --exclude=node_modules \
    --exclude=.git
```

**2. Recovery Procedures:**

**Scenario: Server failure**
```bash
# 1. Provision new server
# 2. Install dependencies (Node.js, Python, Redis)
# 3. Clone repository
# 4. Restore .env from backup
# 5. Run health-check.sh
# 6. Start system in paper mode first
# 7. Verify functionality
# 8. Switch to live mode
```

**Scenario: Private key compromise**
```bash
# 1. IMMEDIATE: Emergency shutdown
./emergency_shutdown.sh "Private key compromised"

# 2. Create new wallet
# Generate new private key securely

# 3. Transfer all funds to new wallet
# Use separate secure computer

# 4. Update .env with new private key

# 5. Deploy new smart contract instance

# 6. Test thoroughly on testnet

# 7. Gradually resume operations
```

---

## Support and Resources

### Documentation
- [README.md](README.md) - System overview
- [GO_LIVE_CHECKLIST.md](GO_LIVE_CHECKLIST.md) - **Full-scale mainnet deployment validation**
- [QUICKSTART.md](QUICKSTART.md) - Quick setup guide
- [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md) - Security features
- [TESTING_CHECKLIST.md](TESTING_CHECKLIST.md) - Test procedures

### Logs Location
- Brain logs: `logs/brain.log`
- Bot logs: `logs/bot.log`
- Emergency shutdowns: `logs/emergency_shutdown_*.log`

### Common Commands Reference

```bash
# System Status
ps aux | grep -E "mainnet_orchestrator|bot.js"
./health-check.sh

# Start/Stop
./start.sh
./emergency_shutdown.sh "reason"

# Monitoring
tail -f logs/brain.log
tail -f logs/bot.log
redis-cli MONITOR

# Maintenance
npm install
pip3 install -r requirements.txt
npx hardhat compile

# Testing
./test_mainnet_modes.py
node execution/bot.js --dry-run
```

---

## Appendix: Graduated Deployment Plan

### Phase 1: Limited Deployment (Week 1-2)

**Configuration:**
```bash
EXECUTION_MODE=LIVE
MIN_PROFIT_USD=10.00
MAX_BASE_FEE_GWEI=200
ENABLE_CROSS_CHAIN_ARBITRAGE=false  # Single chain only
```

**Capital:** $5,000 - $10,000  
**Chains:** Polygon only  
**Monitoring:** 24/7 manual monitoring  
**Expected:** $50-150/day profit

**Success Criteria:**
- 85%+ success rate
- Positive ROI (profit > gas costs)
- No circuit breaker triggers
- System uptime > 95%

### Phase 2: Moderate Deployment (Week 3-4)

**Configuration:**
```bash
EXECUTION_MODE=LIVE
MIN_PROFIT_USD=7.00
MAX_BASE_FEE_GWEI=300
ENABLE_CROSS_CHAIN_ARBITRAGE=true
```

**Capital:** $20,000 - $50,000  
**Chains:** Polygon, Arbitrum, Optimism, Base  
**Monitoring:** Automated alerts + daily review  
**Expected:** $200-500/day profit

**Success Criteria:**
- 80%+ success rate
- ROI > 500%
- < 5 circuit breaker triggers/week
- System uptime > 98%

### Phase 3: Full Deployment (Month 2+)

**Configuration:**
```bash
EXECUTION_MODE=LIVE
MIN_PROFIT_USD=5.00
MAX_BASE_FEE_GWEI=500
ENABLE_CROSS_CHAIN_ARBITRAGE=true
GAS_STRATEGY=STANDARD
```

**Capital:** $50,000+  
**Chains:** All supported chains  
**Monitoring:** Full automation  
**Expected:** $500-1,500/day profit

**Success Criteria:**
- Sustained profitability
- Minimal operator intervention
- Automated recovery from failures
- Continuous optimization

---

**Last Updated:** 2025-12-14  
**Version:** 1.0.0  
**Maintained By:** Titan Operations Team
