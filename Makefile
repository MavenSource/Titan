# ==============================================================================
# 🚀 APEX-OMEGA TITAN: BUILD AUTOMATION
# ==============================================================================
# Makefile for common operations
# Usage: make <target>

.PHONY: help install setup compile deploy test clean start stop health audit

# Default target
help:
	@echo "===================================================="
	@echo "   APEX-OMEGA TITAN: AVAILABLE COMMANDS"
	@echo "===================================================="
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup      - Run complete automated setup"
	@echo "  make install    - Install all dependencies"
	@echo "  make compile    - Compile smart contracts"
	@echo ""
	@echo "Deployment:"
	@echo "  make deploy-polygon   - Deploy to Polygon"
	@echo "  make deploy-arbitrum  - Deploy to Arbitrum"
	@echo "  make deploy-optimism  - Deploy to Optimism"
	@echo ""
	@echo "System Operations:"
	@echo "  make start      - Start all Titan components"
	@echo "  make start-mainnet        - Start mainnet system (use .env mode)"
	@echo "  make start-mainnet-paper  - Start mainnet in PAPER mode"
	@echo "  make start-mainnet-live   - Start mainnet in LIVE mode"
	@echo "  make stop       - Stop all Titan components"
	@echo "  make restart    - Restart the system"
	@echo "  make health     - Check system health"
	@echo "  make audit      - Run system audit"
	@echo ""
	@echo "Development:"
	@echo "  make test       - Run tests"
	@echo "  make clean      - Clean build artifacts"
	@echo "  make lint       - Run linters"
	@echo ""
	@echo "Monitoring:"
	@echo "  make logs-brain - View Brain logs"
	@echo "  make logs-bot   - View Bot logs"
	@echo ""

# Complete setup
setup:
	@echo "Running automated setup..."
	@chmod +x setup.sh
	@./setup.sh

# Install dependencies
install:
	@echo "Installing Node.js dependencies..."
	@npm install --legacy-peer-deps
	@echo "Installing Python dependencies..."
	@pip3 install -r requirements.txt
	@echo "✅ Dependencies installed"

# Compile smart contracts
compile:
	@echo "Compiling smart contracts..."
	@npx hardhat compile
	@echo "✅ Contracts compiled"

# Deploy targets
deploy-polygon:
	@echo "Deploying to Polygon..."
	@npx hardhat run scripts/deploy.js --network polygon

deploy-arbitrum:
	@echo "Deploying to Arbitrum..."
	@npx hardhat run scripts/deploy.js --network arbitrum

deploy-optimism:
	@echo "Deploying to Optimism..."
	@npx hardhat run scripts/deploy.js --network optimism

deploy-base:
	@echo "Deploying to Base..."
	@npx hardhat run scripts/deploy.js --network base

deploy-ethereum:
	@echo "Deploying to Ethereum..."
	@npx hardhat run scripts/deploy.js --network ethereum

# Start system
start:
	@echo "Starting Titan system..."
	@chmod +x start.sh
	@./start.sh

# Start mainnet system in paper mode
start-mainnet-paper:
	@echo "Starting Titan mainnet system in PAPER mode..."
	@chmod +x start_mainnet.sh
	@./start_mainnet.sh paper

# Start mainnet system in live mode
start-mainnet-live:
	@echo "Starting Titan mainnet system in LIVE mode..."
	@chmod +x start_mainnet.sh
	@./start_mainnet.sh live

# Start mainnet with mode from .env
start-mainnet:
	@echo "Starting Titan mainnet system..."
	@chmod +x start_mainnet.sh
	@./start_mainnet.sh

# Stop system
stop:
	@echo "Stopping Titan system..."
	@-pkill -f "python3 ml/brain.py" 2>/dev/null || true
	@-pkill -f "python3 mainnet_orchestrator.py" 2>/dev/null || true
	@-pkill -f "node execution/bot.js" 2>/dev/null || true
	@echo "✅ System stopped"

# Restart system
restart: stop
	@sleep 2
	@make start

# Health check
health:
	@chmod +x health-check.sh
	@./health-check.sh

# Run system audit
audit:
	@echo "Running system audit..."
	@python3 audit_system.py

# Run tests
test:
	@echo "Running tests..."
	@python3 test_phase1.py
	@echo "Tests completed"

# Clean build artifacts
clean:
	@echo "Cleaning build artifacts..."
	@rm -rf artifacts/
	@rm -rf cache/
	@rm -rf typechain/
	@rm -rf typechain-types/
	@rm -rf node_modules/.cache/
	@rm -rf __pycache__/
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "✅ Clean complete"

# Lint code
lint:
	@echo "Linting Solidity contracts..."
	@npx hardhat check || true
	@echo "Linting JavaScript..."
	@npx eslint execution/*.js scripts/*.js --fix || true
	@echo "Linting Python..."
	@python3 -m pylint core/ ml/ routing/ --exit-zero || true

# View logs
logs-brain:
	@tail -f logs/brain.log

logs-bot:
	@tail -f logs/bot.log

# Initialize new environment
init:
	@echo "Initializing new environment..."
	@test -f .env.example && cp .env.example .env || echo "❌ .env.example not found"
	@mkdir -p data logs certs
	@echo "✅ Environment initialized"
	@echo "⚠️  Edit .env file with your configuration"

# Check prerequisites
check-prereqs:
	@echo "Checking prerequisites..."
	@command -v node >/dev/null 2>&1 && echo "✅ Node.js installed" || echo "❌ Node.js not found"
	@command -v python3 >/dev/null 2>&1 && echo "✅ Python 3 installed" || echo "❌ Python 3 not found"
	@command -v pip3 >/dev/null 2>&1 && echo "✅ pip3 installed" || echo "❌ pip3 not found"
	@command -v redis-server >/dev/null 2>&1 && echo "✅ Redis installed" || echo "⚠️  Redis not found (optional)"
	@command -v git >/dev/null 2>&1 && echo "✅ Git installed" || echo "❌ Git not found"

# Quick build verification
verify:
	@chmod +x build.sh
	@./build.sh

# Full build
build:
	@chmod +x build.sh
	@./build.sh
