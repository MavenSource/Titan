# Monitoring and Alerting System Guide
## APEX-OMEGA TITAN Arbitrage System

**Last Updated:** 2025-12-14  
**Version:** 1.0.0  

---

## Table of Contents

- [Overview](#overview)
- [Key Metrics](#key-metrics)
- [Alert Thresholds](#alert-thresholds)
- [Monitoring Setup](#monitoring-setup)
- [Alert Configuration](#alert-configuration)
- [Dashboard Examples](#dashboard-examples)
- [Log Analysis](#log-analysis)
- [Troubleshooting](#troubleshooting)

---

## Overview

Effective monitoring is critical for successful autonomous operation of the Titan system. This guide covers:

- **What to monitor:** Key metrics and indicators
- **When to alert:** Threshold-based alerting
- **How to respond:** Response procedures
- **Tools to use:** Monitoring stack recommendations

---

## Key Metrics

### 1. System Health Metrics

#### System Uptime
- **Description:** Percentage of time system is operational
- **Target:** > 99%
- **Warning:** < 95%
- **Critical:** < 90%
- **Check Method:**
  ```bash
  # Check if processes are running
  ps aux | grep -E "mainnet_orchestrator|bot.js" | wc -l
  # Should return: 2
  ```

#### Component Status
- **Brain (Orchestrator):** Should be running continuously
- **Bot (Executor):** Should be running continuously  
- **Redis:** Should respond to PING
- **RPC Endpoints:** Should respond within 2 seconds

**Check Script:**
```bash
#!/bin/bash
# check_components.sh

# Check Brain
if pgrep -f "mainnet_orchestrator.py" > /dev/null; then
    echo "✅ Brain: Running"
else
    echo "❌ Brain: Down"
fi

# Check Bot
if pgrep -f "execution/bot.js" > /dev/null; then
    echo "✅ Bot: Running"
else
    echo "❌ Bot: Down"
fi

# Check Redis
if redis-cli ping > /dev/null 2>&1; then
    echo "✅ Redis: Running"
else
    echo "❌ Redis: Down"
fi
```

### 2. Performance Metrics

#### Opportunity Detection Rate
- **Description:** Opportunities detected per minute
- **Expected:** 5-15/minute
- **Warning:** < 2/minute
- **Critical:** 0/minute for > 10 minutes

**Query:**
```bash
# Count opportunities in last hour
grep "Opportunity found" logs/brain.log | grep "$(date '+%Y-%m-%d %H')" | wc -l
```

#### Transaction Success Rate
- **Description:** Percentage of executed transactions that succeed
- **Target:** > 85%
- **Warning:** < 75%
- **Critical:** < 60%

**Query:**
```bash
# Calculate success rate for today
ATTEMPTED=$(grep "Executing arbitrage" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
SUCCESSFUL=$(grep "Transaction confirmed" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
if [ $ATTEMPTED -gt 0 ]; then
    echo "Success Rate: $(($SUCCESSFUL * 100 / $ATTEMPTED))%"
fi
```

#### Average Execution Time
- **Description:** Time from opportunity detection to transaction confirmation
- **Target:** < 15 seconds
- **Warning:** > 20 seconds
- **Critical:** > 30 seconds

**Query:**
```bash
# Extract execution times from logs
grep "Execution time:" logs/bot.log | awk '{print $NF}' | awk '{sum+=$1; count++} END {print "Avg:", sum/count, "seconds"}'
```

### 3. Financial Metrics

#### Daily Net Profit
- **Description:** Total profit minus gas costs per day
- **Target:** > $200
- **Warning:** < $50
- **Critical:** < $0 (losing money)

**Query:**
```bash
# Sum profits for today
grep "Net profit" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1)} END {print "Daily Profit: $"sum}'
```

#### Profit per Trade
- **Description:** Average net profit per successful trade
- **Target:** > $10
- **Warning:** < $5
- **Critical:** < $2

**Query:**
```bash
# Average profit per trade
grep "Net profit" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1); count++} END {print "Avg Profit: $"sum/count}'
```

#### Gas Cost Efficiency
- **Description:** Ratio of profit to gas costs
- **Target:** > 5x
- **Warning:** < 3x
- **Critical:** < 1.5x

**Query:**
```bash
# Calculate profit/gas ratio
PROFIT=$(grep "Net profit" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1)} END {print sum}')
GAS=$(grep "Gas cost" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1)} END {print sum}')
echo "Profit/Gas Ratio: $(echo "$PROFIT / $GAS" | bc -l)x"
```

#### Wallet Balance
- **Description:** Native token balance for gas on each chain
- **Target:** > $100 per chain
- **Warning:** < $50 per chain
- **Critical:** < $20 per chain

**Manual Check:** Use block explorers or:
```bash
# Check balances using RPC
curl -X POST $RPC_POLYGON \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_getBalance","params":["'$EXECUTOR_ADDRESS'","latest"],"id":1}' | jq
```

### 4. Safety Metrics

#### Circuit Breaker Activations
- **Description:** Number of times circuit breaker has triggered
- **Expected:** 0-2 per day
- **Warning:** 5 per day
- **Critical:** 10 per day

**Query:**
```bash
# Count circuit breaker triggers
grep "Circuit breaker activated" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l
```

#### Consecutive Failures
- **Description:** Number of failed transactions in a row
- **Expected:** 0-3
- **Warning:** 5-7
- **Critical:** 10+ (should trigger circuit breaker)

**Query:**
```bash
# Check current consecutive failure count
grep "Consecutive failures" logs/bot.log | tail -1 | awk '{print $NF}'
```

#### Gas Price Events
- **Description:** Times gas price exceeded ceiling
- **Expected:** 0-5 per day
- **Warning:** 10 per day
- **Critical:** 20 per day

**Query:**
```bash
# Count gas price ceiling events
grep "Gas price too high" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l
```

### 5. Infrastructure Metrics

#### Redis Connectivity
- **Description:** Redis connection status and latency
- **Target:** < 5ms latency, 100% uptime
- **Warning:** > 20ms latency or disconnects
- **Critical:** Cannot connect

**Check:**
```bash
# Test Redis latency
redis-cli --latency-history
```

#### RPC Response Time
- **Description:** Time for RPC to respond to requests
- **Target:** < 200ms
- **Warning:** > 500ms
- **Critical:** > 2000ms or timeout

**Check:**
```bash
# Test RPC latency
time curl -X POST $RPC_POLYGON \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}'
```

#### Disk Space
- **Description:** Available disk space for logs
- **Target:** > 5GB free
- **Warning:** < 2GB free
- **Critical:** < 500MB free

**Check:**
```bash
df -h | grep "/$"
```

#### Memory Usage
- **Description:** RAM usage by system processes
- **Target:** < 80%
- **Warning:** > 90%
- **Critical:** > 95%

**Check:**
```bash
free -m | awk 'NR==2{printf "Memory Usage: %.2f%%\n", $3*100/$2 }'
```

---

## Alert Thresholds

### Priority Levels

| Priority | Response Time | Action Required |
|----------|---------------|-----------------|
| **INFO** | Review daily | Monitor trend |
| **WARNING** | Review within 1 hour | Investigate cause |
| **CRITICAL** | Immediate (< 5 min) | Emergency response |

### Threshold Matrix

| Metric | INFO | WARNING | CRITICAL |
|--------|------|---------|----------|
| **System Uptime** | 99%+ | < 95% | < 90% |
| **Success Rate** | 85%+ | < 75% | < 60% |
| **Daily Profit** | $200+ | < $50 | < $0 |
| **Circuit Breaker** | 0-2/day | 5/day | 10/day |
| **Gas Price** | < 200 gwei | > 300 gwei | > 500 gwei |
| **Wallet Balance** | $100+ | < $50 | < $20 |
| **Redis Latency** | < 5ms | > 20ms | Cannot connect |
| **RPC Latency** | < 200ms | > 500ms | > 2000ms |
| **Disk Space** | 5GB+ | < 2GB | < 500MB |
| **Memory Usage** | < 80% | > 90% | > 95% |

---

## Monitoring Setup

### Option 1: Simple Script-Based Monitoring

**Create monitoring script:**

```bash
#!/bin/bash
# monitor.sh - Simple monitoring script

LOG_FILE="logs/monitoring_$(date '+%Y%m%d').log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check system health
check_health() {
    log "=== Health Check ==="
    
    # Components
    if pgrep -f "mainnet_orchestrator.py" > /dev/null; then
        log "✅ Brain: Running"
    else
        log "❌ CRITICAL: Brain is down!"
        # Alert mechanism here
    fi
    
    if pgrep -f "execution/bot.js" > /dev/null; then
        log "✅ Bot: Running"
    else
        log "❌ CRITICAL: Bot is down!"
        # Alert mechanism here
    fi
    
    # Redis
    if redis-cli ping > /dev/null 2>&1; then
        log "✅ Redis: Running"
    else
        log "❌ CRITICAL: Redis is down!"
        # Alert mechanism here
    fi
}

# Check performance
check_performance() {
    log "=== Performance Check ==="
    
    # Opportunities in last 10 minutes
    OPP=$(grep "Opportunity found" logs/brain.log | tail -100 | wc -l)
    log "Opportunities (last 100 lines): $OPP"
    
    if [ $OPP -lt 10 ]; then
        log "⚠️  WARNING: Low opportunity detection rate"
    fi
    
    # Success rate
    ATTEMPTED=$(grep "Executing arbitrage" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
    SUCCESSFUL=$(grep "Transaction confirmed" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
    
    if [ $ATTEMPTED -gt 0 ]; then
        SUCCESS_RATE=$(($SUCCESSFUL * 100 / $ATTEMPTED))
        log "Success Rate Today: $SUCCESS_RATE%"
        
        if [ $SUCCESS_RATE -lt 60 ]; then
            log "❌ CRITICAL: Success rate below 60%"
        elif [ $SUCCESS_RATE -lt 75 ]; then
            log "⚠️  WARNING: Success rate below 75%"
        fi
    fi
}

# Check financials
check_financials() {
    log "=== Financial Check ==="
    
    # Daily profit
    PROFIT=$(grep "Net profit" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1)} END {print sum}')
    log "Daily Profit: \$$PROFIT"
    
    # Gas costs
    GAS=$(grep "Gas cost" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1)} END {print sum}')
    log "Daily Gas Cost: \$$GAS"
    
    # Check if profitable
    if (( $(echo "$PROFIT < 0" | bc -l) )); then
        log "❌ CRITICAL: System is losing money!"
    elif (( $(echo "$PROFIT < 50" | bc -l) )); then
        log "⚠️  WARNING: Low daily profit"
    fi
}

# Check safety
check_safety() {
    log "=== Safety Check ==="
    
    # Circuit breaker
    CB_COUNT=$(grep "Circuit breaker activated" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
    log "Circuit Breaker Triggers Today: $CB_COUNT"
    
    if [ $CB_COUNT -gt 10 ]; then
        log "❌ CRITICAL: Excessive circuit breaker triggers"
    elif [ $CB_COUNT -gt 5 ]; then
        log "⚠️  WARNING: High circuit breaker trigger rate"
    fi
}

# Main monitoring loop
while true; do
    check_health
    check_performance
    check_financials
    check_safety
    
    log "=== Check Complete ==="
    log ""
    
    # Run every 5 minutes
    sleep 300
done
```

**Run monitoring:**
```bash
chmod +x monitor.sh
nohup ./monitor.sh > /dev/null 2>&1 &
echo $! > .monitor.pid
```

### Option 2: Advanced Monitoring with Prometheus/Grafana

**Install Prometheus and Grafana:**
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.45.0/prometheus-2.45.0.linux-amd64.tar.gz
tar xvfz prometheus-*.tar.gz
cd prometheus-*

# Install Grafana
sudo apt-get install -y adduser libfontconfig1
wget https://dl.grafana.com/oss/release/grafana_10.0.0_amd64.deb
sudo dpkg -i grafana_10.0.0_amd64.deb
```

**Create metrics exporter for Titan:**
```javascript
// metrics_exporter.js
const express = require('express');
const client = require('prom-client');
const fs = require('fs');

const app = express();
const register = new client.Registry();

// Create metrics
const transactionTotal = new client.Counter({
    name: 'titan_transactions_total',
    help: 'Total number of transactions',
    labelNames: ['status'],
    registers: [register]
});

const profitGauge = new client.Gauge({
    name: 'titan_profit_usd',
    help: 'Current daily profit in USD',
    registers: [register]
});

const gasGauge = new client.Gauge({
    name: 'titan_gas_cost_usd',
    help: 'Current daily gas cost in USD',
    registers: [register]
});

// Update metrics from logs
function updateMetrics() {
    // Parse logs and update metrics
    // Implementation depends on log format
}

setInterval(updateMetrics, 30000);  // Update every 30 seconds

app.get('/metrics', (req, res) => {
    res.set('Content-Type', register.contentType);
    res.end(register.metrics());
});

app.listen(9090, () => {
    console.log('Metrics server listening on port 9090');
});
```

---

## Alert Configuration

### Email Alerts

**Using mailx:**
```bash
# Install mailx
sudo apt-get install mailutils

# Send alert
send_alert() {
    SUBJECT="$1"
    BODY="$2"
    echo "$BODY" | mail -s "$SUBJECT" your-email@example.com
}

# Example usage
if [ $SUCCESS_RATE -lt 60 ]; then
    send_alert "CRITICAL: Titan Success Rate Low" "Success rate: $SUCCESS_RATE%"
fi
```

### Slack Alerts

**Using webhook:**
```bash
# Set Slack webhook URL
SLACK_WEBHOOK="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"

# Send alert function
send_slack_alert() {
    MESSAGE="$1"
    curl -X POST -H 'Content-type: application/json' \
        --data "{\"text\":\"$MESSAGE\"}" \
        "$SLACK_WEBHOOK"
}

# Example usage
send_slack_alert "⚠️ WARNING: Circuit breaker activated 5 times today"
```

### SMS Alerts (Twilio)

**Using Twilio API:**
```bash
# Twilio credentials
TWILIO_ACCOUNT_SID="your_account_sid"
TWILIO_AUTH_TOKEN="your_auth_token"
TWILIO_FROM="+1234567890"
TWILIO_TO="+0987654321"

# Send SMS
send_sms_alert() {
    MESSAGE="$1"
    curl -X POST "https://api.twilio.com/2010-04-01/Accounts/$TWILIO_ACCOUNT_SID/Messages.json" \
        --data-urlencode "From=$TWILIO_FROM" \
        --data-urlencode "To=$TWILIO_TO" \
        --data-urlencode "Body=$MESSAGE" \
        -u "$TWILIO_ACCOUNT_SID:$TWILIO_AUTH_TOKEN"
}

# Example usage (for critical alerts only)
if [ $PROFIT -lt 0 ]; then
    send_sms_alert "CRITICAL: Titan is losing money. Daily P/L: \$$PROFIT"
fi
```

---

## Dashboard Examples

### Terminal Dashboard (Simple)

```bash
#!/bin/bash
# dashboard.sh - Simple terminal dashboard

while true; do
    clear
    echo "===================================="
    echo "  TITAN MONITORING DASHBOARD"
    echo "===================================="
    echo ""
    date
    echo ""
    
    # System Status
    echo "SYSTEM STATUS:"
    if pgrep -f "mainnet_orchestrator.py" > /dev/null; then
        echo "  Brain: ✅ Running"
    else
        echo "  Brain: ❌ Down"
    fi
    
    if pgrep -f "execution/bot.js" > /dev/null; then
        echo "  Bot: ✅ Running"
    else
        echo "  Bot: ❌ Down"
    fi
    
    if redis-cli ping > /dev/null 2>&1; then
        echo "  Redis: ✅ Running"
    else
        echo "  Redis: ❌ Down"
    fi
    
    echo ""
    echo "TODAY'S PERFORMANCE:"
    
    # Calculate stats
    ATTEMPTED=$(grep "Executing" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
    SUCCESSFUL=$(grep "confirmed" logs/bot.log | grep "$(date '+%Y-%m-%d')" | wc -l)
    PROFIT=$(grep "Net profit" logs/bot.log | grep "$(date '+%Y-%m-%d')" | awk '{sum+=$(NF-1)} END {print sum}')
    
    echo "  Transactions: $SUCCESSFUL / $ATTEMPTED"
    if [ $ATTEMPTED -gt 0 ]; then
        echo "  Success Rate: $(($SUCCESSFUL * 100 / $ATTEMPTED))%"
    fi
    echo "  Profit: \$$PROFIT"
    
    echo ""
    echo "RECENT ACTIVITY (last 10 lines):"
    tail -10 logs/bot.log | sed 's/^/  /'
    
    echo ""
    echo "===================================="
    
    sleep 10
done
```

**Run dashboard:**
```bash
chmod +x dashboard.sh
./dashboard.sh
```

---

## Log Analysis

### Log Parsing Scripts

**Extract today's profits:**
```bash
# profits_today.sh
grep "Net profit" logs/bot.log | grep "$(date '+%Y-%m-%d')" | \
    awk '{print $1, $2, $NF}' | \
    awk '{sum+=$NF; count++; print} END {print "\nTotal:", sum, "Count:", count, "Average:", sum/count}'
```

**Find errors:**
```bash
# errors_today.sh
grep -i "error\|failed\|exception" logs/*.log | grep "$(date '+%Y-%m-%d')"
```

**Analyze gas costs:**
```bash
# gas_analysis.sh
grep "Gas cost" logs/bot.log | grep "$(date '+%Y-%m-%d')" | \
    awk '{sum+=$NF; count++; if($NF>max) max=$NF; if(count==1 || $NF<min) min=$NF} \
    END {print "Total:", sum, "Count:", count, "Avg:", sum/count, "Min:", min, "Max:", max}'
```

---

## Troubleshooting

### Alert Fatigue

**Problem:** Too many alerts

**Solution:**
1. Increase alert thresholds initially
2. Use WARNING vs CRITICAL properly
3. Aggregate similar alerts (e.g., hourly summary)
4. Add cooldown periods between alerts

### False Positives

**Problem:** Alerts for non-issues

**Solution:**
1. Tune thresholds based on normal behavior
2. Add context to alerts (recent trends)
3. Use multiple conditions (AND logic)
4. Implement grace periods

### Missed Alerts

**Problem:** Critical issues not detected

**Solution:**
1. Lower critical thresholds
2. Add redundant monitoring
3. Monitor the monitoring system itself
4. Test alert delivery regularly

---

## Best Practices

1. **Start Conservative:** Use stricter thresholds initially
2. **Tune Over Time:** Adjust based on actual performance
3. **Test Alerts:** Regularly test alert delivery
4. **Document Response:** Create runbooks for each alert type
5. **Review Regularly:** Weekly review of monitoring effectiveness
6. **Automate Where Possible:** Reduce manual monitoring burden
7. **Keep It Simple:** Don't over-complicate initially

---

**Last Updated:** 2025-12-14  
**Next Review:** After Phase 1 deployment
