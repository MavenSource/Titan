#!/bin/bash

# ==============================================================================
# 🚀 APEX-OMEGA TITAN: MAINNET SYSTEM LAUNCHER
# ==============================================================================
# Comprehensive mainnet orchestration with:
# - Real-time data ingestion
# - Real arbitrage calculations  
# - Paper execution OR live blockchain interaction (configurable)
# - Real-time ML model training
#
# Usage:
#   ./start_mainnet.sh paper  # Start in paper mode (simulated execution)
#   ./start_mainnet.sh live   # Start in live mode (real execution)
#   ./start_mainnet.sh        # Use mode from .env (default: paper)

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Parse mode argument
MODE="${1:-}"
if [ -z "$MODE" ]; then
    # Read from .env if no argument provided
    if [ -f ".env" ]; then
        MODE=$(grep "^EXECUTION_MODE=" .env | cut -d'=' -f2 | tr -d ' ' | tr '[:lower:]' '[:upper:]')
    fi
    MODE="${MODE:-PAPER}"
fi

MODE=$(echo "$MODE" | tr '[:lower:]' '[:upper:]')

# Validate mode
if [ "$MODE" != "PAPER" ] && [ "$MODE" != "LIVE" ]; then
    echo -e "${RED}❌ Invalid mode: $MODE${NC}"
    echo "Usage: $0 [paper|live]"
    exit 1
fi

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   APEX-OMEGA TITAN: MAINNET SYSTEM BOOT${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""
echo -e "${GREEN}   Execution Mode: $MODE${NC}"
if [ "$MODE" == "PAPER" ]; then
    echo -e "${GREEN}   📝 Paper trading (simulated execution)${NC}"
    echo -e "${GREEN}   • Real-time mainnet data: ✓${NC}"
    echo -e "${GREEN}   • Real arbitrage calculations: ✓${NC}"
    echo -e "${GREEN}   • Blockchain execution: SIMULATED${NC}"
    echo -e "${GREEN}   • ML model training: ✓${NC}"
else
    echo -e "${RED}   🔴 Live trading (real execution)${NC}"
    echo -e "${RED}   ⚠️  WARNING: Real funds will be used!${NC}"
    echo -e "${GREEN}   • Real-time mainnet data: ✓${NC}"
    echo -e "${GREEN}   • Real arbitrage calculations: ✓${NC}"
    echo -e "${RED}   • Blockchain execution: LIVE${NC}"
    echo -e "${GREEN}   • ML model training: ✓${NC}"
fi
echo -e "${BLUE}===================================================${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!] .env file not found${NC}"
    echo "Please run setup.sh first or create .env from .env.example"
    exit 1
fi

# Update EXECUTION_MODE in .env (portable for Linux and macOS)
if grep -q "^EXECUTION_MODE=" .env; then
    # Use perl for cross-platform compatibility
    perl -i -pe "s/^EXECUTION_MODE=.*/EXECUTION_MODE=$MODE/" .env 2>/dev/null || \
    # Fallback to temp file approach if perl not available
    (grep -v "^EXECUTION_MODE=" .env > .env.tmp && echo "EXECUTION_MODE=$MODE" >> .env.tmp && mv .env.tmp .env)
else
    echo "EXECUTION_MODE=$MODE" >> .env
fi

echo -e "${GREEN}[✓] Updated .env with EXECUTION_MODE=$MODE${NC}"
echo ""

# Check if Redis is running
if ! redis-cli ping >/dev/null 2>&1; then
    echo -e "${YELLOW}[!] Redis is not running${NC}"
    echo "Starting Redis..."
    if command -v redis-server >/dev/null 2>&1; then
        redis-server --daemonize yes
        sleep 2
        echo -e "${GREEN}[✓] Redis started${NC}"
    else
        echo "Please start Redis manually: redis-server"
        exit 1
    fi
else
    echo -e "${GREEN}[✓] Redis is running${NC}"
fi

echo ""
echo -e "${GREEN}[1/2] Starting Mainnet Orchestrator (Python)...${NC}"
echo -e "${GREEN}      - Real-time data ingestion${NC}"
echo -e "${GREEN}      - Arbitrage calculations${NC}"
echo -e "${GREEN}      - ML model training${NC}"
echo ""

echo -e "${GREEN}[2/2] Starting Execution Engine (Node.js)...${NC}"
if [ "$MODE" == "PAPER" ]; then
    echo -e "${GREEN}      - Paper trade execution${NC}"
else
    echo -e "${RED}      - Live blockchain execution${NC}"
fi
echo ""

# Create logs directory if it doesn't exist
mkdir -p logs

# Export mode for child processes
export EXECUTION_MODE=$MODE
export TITAN_EXECUTION_MODE=$MODE

# Detect terminal emulator and start processes
if command -v gnome-terminal >/dev/null 2>&1; then
    # GNOME Terminal (Ubuntu, Debian)
    gnome-terminal --title="Titan Orchestrator" -- bash -c "python3 mainnet_orchestrator.py; exec bash"
    gnome-terminal --title="Titan Executor" -- bash -c "node execution/bot.js; exec bash"
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
elif command -v konsole >/dev/null 2>&1; then
    # KDE Konsole
    konsole --new-tab --title "Titan Orchestrator" -e bash -c "python3 mainnet_orchestrator.py; exec bash" &
    konsole --new-tab --title "Titan Executor" -e bash -c "node execution/bot.js; exec bash" &
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
elif command -v xterm >/dev/null 2>&1; then
    # xterm (fallback)
    xterm -T "Titan Orchestrator" -e "python3 mainnet_orchestrator.py; bash" &
    xterm -T "Titan Executor" -e "node execution/bot.js; bash" &
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
elif command -v osascript >/dev/null 2>&1; then
    # macOS Terminal
    osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && python3 mainnet_orchestrator.py"'
    osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)"' && node execution/bot.js"'
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
else
    # No terminal emulator detected, run in background
    echo -e "${YELLOW}[!] No terminal emulator detected${NC}"
    echo "Starting components in background..."
    python3 mainnet_orchestrator.py > logs/orchestrator.log 2>&1 &
    ORCHESTRATOR_PID=$!
    node execution/bot.js > logs/executor.log 2>&1 &
    EXECUTOR_PID=$!
    echo -e "${GREEN}[✓] Orchestrator PID: $ORCHESTRATOR_PID${NC}"
    echo -e "${GREEN}[✓] Executor PID: $EXECUTOR_PID${NC}"
    echo ""
    echo "View logs:"
    echo "  Orchestrator: tail -f logs/orchestrator.log"
    echo "  Executor: tail -f logs/executor.log"
    echo ""
    echo "Stop with: kill $ORCHESTRATOR_PID $EXECUTOR_PID"
fi

echo ""
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}   ✅ TITAN MAINNET SYSTEM ONLINE${NC}"
echo -e "${GREEN}===================================================${NC}"
echo ""
echo "System Architecture:"
echo "  ┌─────────────────────────────────────────────────┐"
echo "  │   Real-Time Data → Orchestrator (Python)       │"
echo "  │   Arbitrage Calc → Brain + ProfitEngine        │"
if [ "$MODE" == "PAPER" ]; then
    echo "  │   Execution      → Paper Mode (Simulated)      │"
else
    echo "  │   Execution      → Live Mode (Real Blockchain) │"
fi
echo "  │   ML Training    → Real-time Updates           │"
echo "  └─────────────────────────────────────────────────┘"
echo ""
echo "Components running:"
echo "  • Mainnet Orchestrator (Python)"
echo "  • Execution Engine (Node.js)"
echo "  • Redis Message Queue"
echo ""
if [ "$MODE" == "PAPER" ]; then
    echo "📝 Running in PAPER mode - trades are simulated"
else
    echo "🔴 Running in LIVE mode - REAL FUNDS AT RISK"
fi
echo ""
echo "To stop: Press Ctrl+C in each terminal or kill the processes"
echo ""
