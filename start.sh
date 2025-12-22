#!/bin/bash

# ==============================================================================
# 🚀 APEX-OMEGA TITAN: SYSTEM LAUNCHER (Linux/macOS)
# ==============================================================================
# Starts all Titan components in separate terminal sessions
# Run: chmod +x start.sh && ./start.sh

set -e

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}===================================================${NC}"
echo -e "${BLUE}   APEX-OMEGA TITAN: SYSTEM BOOT${NC}"
echo -e "${BLUE}===================================================${NC}"
echo ""

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}[!] .env file not found${NC}"
    echo "Please run setup.sh first or create .env from .env.example"
    exit 1
fi

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
echo -e "${GREEN}[1/3] Starting Titan Brain (AI Engine)...${NC}"
echo ""

# Detect terminal emulator and start processes
if command -v gnome-terminal >/dev/null 2>&1; then
    # GNOME Terminal (Ubuntu, Debian)
    gnome-terminal --title="Titan Brain" -- bash -c "cd offchain/brain && python3 ml/brain.py; exec bash"
    gnome-terminal --title="Titan Executor" -- bash -c "cd offchain/executor && node execution/bot.js; exec bash"
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
elif command -v konsole >/dev/null 2>&1; then
    # KDE Konsole
    konsole --new-tab --title "Titan Brain" -e bash -c "cd offchain/brain && python3 ml/brain.py; exec bash" &
    konsole --new-tab --title "Titan Executor" -e bash -c "cd offchain/executor && node execution/bot.js; exec bash" &
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
elif command -v xterm >/dev/null 2>&1; then
    # xterm (fallback)
    xterm -T "Titan Brain" -e "cd offchain/brain && python3 ml/brain.py; bash" &
    xterm -T "Titan Executor" -e "cd offchain/executor && node execution/bot.js; bash" &
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
elif command -v osascript >/dev/null 2>&1; then
    # macOS Terminal
    osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)/offchain/brain"' && python3 ml/brain.py"'
    osascript -e 'tell app "Terminal" to do script "cd '"$(pwd)/offchain/executor"' && node execution/bot.js"'
    echo -e "${GREEN}[✓] Components started in new terminals${NC}"
else
    # No terminal emulator detected, run in background
    echo -e "${YELLOW}[!] No terminal emulator detected${NC}"
    echo "Starting components in background..."
    mkdir -p logs
    cd offchain/brain && python3 ml/brain.py > ../../logs/brain.log 2>&1 &
    BRAIN_PID=$!
    cd ../executor && node execution/bot.js > ../../logs/bot.log 2>&1 &
    BOT_PID=$!
    cd ../..
    echo -e "${GREEN}[✓] Brain PID: $BRAIN_PID${NC}"
    echo -e "${GREEN}[✓] Executor PID: $BOT_PID${NC}"
    echo ""
    echo "View logs:"
    echo "  Brain: tail -f logs/brain.log"
    echo "  Bot: tail -f logs/bot.log"
    echo ""
    echo "Stop with: kill $BRAIN_PID $BOT_PID"
fi

echo ""
echo -e "${GREEN}===================================================${NC}"
echo -e "${GREEN}   ✅ TITAN SYSTEM ONLINE${NC}"
echo -e "${GREEN}===================================================${NC}"
echo ""
echo "Components running:"
echo "  • Titan Brain (Python AI Engine)"
echo "  • Titan Executor (Node.js Trading Bot)"
echo "  • Redis Message Queue"
echo ""
echo "To stop: Press Ctrl+C in each terminal or kill the processes"
echo ""
