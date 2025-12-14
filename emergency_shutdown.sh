#!/bin/bash

# ==============================================================================
# 🚨 APEX-OMEGA TITAN: EMERGENCY SHUTDOWN
# ==============================================================================
# Emergency shutdown script for immediate system halt
# Use this script when you need to stop all operations immediately
#
# Usage: ./emergency_shutdown.sh [reason]
# Example: ./emergency_shutdown.sh "Detected unusual activity"

# Colors
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m'

# Timestamp
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

# Reason for shutdown
REASON="${1:-Manual emergency shutdown}"

echo -e "${RED}======================================${NC}"
echo -e "${RED}   🚨 EMERGENCY SHUTDOWN INITIATED${NC}"
echo -e "${RED}======================================${NC}"
echo ""
echo -e "${YELLOW}Time:${NC} $TIMESTAMP"
echo -e "${YELLOW}Reason:${NC} $REASON"
echo ""

# Create shutdown log directory
mkdir -p logs
SHUTDOWN_LOG="logs/emergency_shutdown_$(date '+%Y%m%d_%H%M%S').log"

# Log function with current timestamp
log_action() {
    # Ensure logs directory exists before writing
    mkdir -p logs 2>/dev/null || true
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$SHUTDOWN_LOG" 2>/dev/null || echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

log_action "Emergency shutdown initiated: $REASON"

# Step 1: Stop main orchestrator process
echo -e "${YELLOW}[1/6]${NC} Stopping main orchestrator..."
if [ -f ".orchestrator.pid" ]; then
    ORCHESTRATOR_PID=$(cat .orchestrator.pid)
    if ps -p "$ORCHESTRATOR_PID" > /dev/null 2>&1; then
        kill -SIGTERM "$ORCHESTRATOR_PID" 2>/dev/null
        sleep 2
        if ps -p "$ORCHESTRATOR_PID" > /dev/null 2>&1; then
            kill -SIGKILL "$ORCHESTRATOR_PID" 2>/dev/null
            log_action "Orchestrator force-killed (PID: $ORCHESTRATOR_PID)"
            echo -e "${GREEN}[✓]${NC} Orchestrator stopped (force-killed)"
        else
            log_action "Orchestrator gracefully stopped (PID: $ORCHESTRATOR_PID)"
            echo -e "${GREEN}[✓]${NC} Orchestrator stopped gracefully"
        fi
        rm -f .orchestrator.pid
    else
        log_action "Orchestrator PID file found but process not running"
        echo -e "${YELLOW}[!]${NC} Orchestrator not running"
        rm -f .orchestrator.pid
    fi
else
    log_action "No orchestrator PID file found"
    echo -e "${YELLOW}[!]${NC} No orchestrator PID file found"
fi

# Step 2: Stop execution bot
echo -e "${YELLOW}[2/6]${NC} Stopping execution bot..."
if [ -f ".executor.pid" ]; then
    EXECUTOR_PID=$(cat .executor.pid)
    if ps -p "$EXECUTOR_PID" > /dev/null 2>&1; then
        kill -SIGTERM "$EXECUTOR_PID" 2>/dev/null
        sleep 2
        if ps -p "$EXECUTOR_PID" > /dev/null 2>&1; then
            kill -SIGKILL "$EXECUTOR_PID" 2>/dev/null
            log_action "Executor force-killed (PID: $EXECUTOR_PID)"
            echo -e "${GREEN}[✓]${NC} Executor stopped (force-killed)"
        else
            log_action "Executor gracefully stopped (PID: $EXECUTOR_PID)"
            echo -e "${GREEN}[✓]${NC} Executor stopped gracefully"
        fi
        rm -f .executor.pid
    else
        log_action "Executor PID file found but process not running"
        echo -e "${YELLOW}[!]${NC} Executor not running"
        rm -f .executor.pid
    fi
else
    log_action "No executor PID file found"
    echo -e "${YELLOW}[!]${NC} No executor PID file found"
fi

# Step 3: Kill any remaining Python processes (brain)
echo -e "${YELLOW}[3/6]${NC} Checking for orphaned brain processes..."
BRAIN_PIDS=$(pgrep -f "mainnet_orchestrator.py" 2>/dev/null)
if [ ! -z "$BRAIN_PIDS" ]; then
    while read -r pid; do
        kill -SIGTERM "$pid" 2>/dev/null
        log_action "Terminated brain process PID: $pid"
    done <<< "$BRAIN_PIDS"
    sleep 1
    # Force kill if still running
    BRAIN_PIDS=$(pgrep -f "mainnet_orchestrator.py" 2>/dev/null)
    if [ ! -z "$BRAIN_PIDS" ]; then
        while read -r pid; do
            kill -SIGKILL "$pid" 2>/dev/null
            log_action "Force-killed brain process PID: $pid"
        done <<< "$BRAIN_PIDS"
    fi
    echo -e "${GREEN}[✓]${NC} Brain processes terminated"
else
    log_action "No orphaned brain processes found"
    echo -e "${GREEN}[✓]${NC} No orphaned brain processes"
fi

# Step 4: Kill any remaining Node.js processes (bot)
echo -e "${YELLOW}[4/6]${NC} Checking for orphaned bot processes..."
BOT_PIDS=$(pgrep -f "execution/bot.js" 2>/dev/null)
if [ ! -z "$BOT_PIDS" ]; then
    while read -r pid; do
        kill -SIGTERM "$pid" 2>/dev/null
        log_action "Terminated bot process PID: $pid"
    done <<< "$BOT_PIDS"
    sleep 1
    # Force kill if still running
    BOT_PIDS=$(pgrep -f "execution/bot.js" 2>/dev/null)
    if [ ! -z "$BOT_PIDS" ]; then
        while read -r pid; do
            kill -SIGKILL "$pid" 2>/dev/null
            log_action "Force-killed bot process PID: $pid"
        done <<< "$BOT_PIDS"
    fi
    echo -e "${GREEN}[✓]${NC} Bot processes terminated"
else
    log_action "No orphaned bot processes found"
    echo -e "${GREEN}[✓]${NC} No orphaned bot processes"
fi

# Step 5: Clear Redis signals (optional - prevents auto-restart issues)
echo -e "${YELLOW}[5/6]${NC} Clearing Redis signal channels..."
if command -v redis-cli >/dev/null 2>&1; then
    if redis-cli ping >/dev/null 2>&1; then
        redis-cli DEL arbitrage_signals 2>/dev/null >/dev/null
        redis-cli DEL brain_status 2>/dev/null >/dev/null
        redis-cli DEL executor_status 2>/dev/null >/dev/null
        log_action "Redis signal channels cleared"
        echo -e "${GREEN}[✓]${NC} Redis channels cleared"
    else
        log_action "Redis not accessible"
        echo -e "${YELLOW}[!]${NC} Redis not accessible"
    fi
else
    log_action "redis-cli not found"
    echo -e "${YELLOW}[!]${NC} redis-cli not found"
fi

# Step 6: Create emergency marker file
echo -e "${YELLOW}[6/6]${NC} Creating emergency shutdown marker..."
MARKER_FILE=".emergency_shutdown"
cat > "$MARKER_FILE" << EOF
EMERGENCY SHUTDOWN
==================
Time: $TIMESTAMP
Reason: $REASON
Shutdown by: $USER
Hostname: $(hostname)

This file indicates the system was emergency-stopped.
Remove this file before restarting the system.
EOF

log_action "Emergency shutdown marker created: $MARKER_FILE"
echo -e "${GREEN}[✓]${NC} Emergency marker created"

echo ""
echo -e "${RED}======================================${NC}"
echo -e "${RED}   ✅ EMERGENCY SHUTDOWN COMPLETE${NC}"
echo -e "${RED}======================================${NC}"
echo ""
echo -e "${YELLOW}All system processes have been terminated.${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "  1. Review shutdown log: $SHUTDOWN_LOG"
echo "  2. Investigate reason for shutdown: $REASON"
echo "  3. Fix any issues before restarting"
echo "  4. Remove marker file: rm $MARKER_FILE"
echo "  5. Restart system: ./start.sh or make start"
echo ""
echo -e "${YELLOW}⚠️  Do NOT restart until you've addressed the shutdown reason!${NC}"
echo ""

log_action "Emergency shutdown completed successfully"

exit 0
