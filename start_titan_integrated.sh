#!/bin/bash
###################################################################
# TITAN INTEGRATED STARTUP (NO REDIS REQUIRED)
###################################################################
# Launches both Python brain and Node.js executor in parallel
# Signals flow via JSON files: signals/outgoing -> signals/processed
###################################################################

echo ""
echo "========================================================================"
echo "  TITAN ARBITRAGE SYSTEM - INTEGRATED STARTUP"
echo "========================================================================"
echo "  Mode: File-based signaling (No Redis required)"
echo "  Python Brain: Finds opportunities & writes signals"
echo "  Node.js Bot: Reads signals & executes (PAPER mode)"
echo "========================================================================"
echo ""

cd "$(dirname "$0")"

# Check dependencies
if ! command -v node &> /dev/null; then
    echo "[ERROR] Node.js not found in PATH"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python3 not found in PATH"
    echo "Please install Python 3.8+ from https://python.org/"
    exit 1
fi

# Install Node.js dependencies if needed
if [ ! -d "node_modules" ]; then
    echo "[SETUP] Installing Node.js dependencies..."
    npm install
    if [ $? -ne 0 ]; then
        echo "[ERROR] npm install failed"
        exit 1
    fi
fi

# Create signal directories
mkdir -p signals/outgoing
mkdir -p signals/processed

echo "[OK] Environment ready"
echo ""
echo "Starting both processes..."
echo "  - Python Brain: mainnet_orchestrator.py"
echo "  - Node.js Bot: execution/bot.js"
echo ""
echo "Press Ctrl+C to stop both processes"
echo ""

# Cleanup function
cleanup() {
    echo ""
    echo "========================================================================"
    echo "  Stopping processes..."
    echo "========================================================================"
    kill $PYTHON_PID 2>/dev/null
    kill $NODE_PID 2>/dev/null
    wait $PYTHON_PID 2>/dev/null
    wait $NODE_PID 2>/dev/null
    echo "System stopped"
    exit 0
}

# Trap Ctrl+C
trap cleanup SIGINT SIGTERM

# Start Python brain in background
python3 mainnet_orchestrator.py &
PYTHON_PID=$!
echo "[STARTED] Python Brain (PID: $PYTHON_PID)"

# Give Python a moment to initialize
sleep 2

# Start Node.js bot in background
node execution/bot.js &
NODE_PID=$!
echo "[STARTED] Node.js Bot (PID: $NODE_PID)"

echo ""
echo "Both processes running. Monitoring..."
echo ""

# Wait for both processes
wait $PYTHON_PID $NODE_PID
