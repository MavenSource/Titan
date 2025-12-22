# Off-Chain Components

This directory contains all off-chain logic for the Titan arbitrage system.

## Structure

- `brain/` - Python ML and arbitrage detection engine
  - `ml/` - Machine learning models and price oracles
  - `core/` - Core system configuration and token discovery
  - `routing/` - Bridge aggregation and cross-chain routing
  - `simulation/` - Historical simulation and backtesting
- `executor/` - JavaScript execution engine
  - `execution/` - Trade execution bot and aggregator integrations
  - `monitoring/` - MEV metrics and system monitoring

## Setup

### Python Brain Setup
```bash
cd brain
pip install -r requirements.txt
```

### JavaScript Executor Setup
```bash
cd executor
npm install
```

## Environment Configuration

Create a `.env` file in the `offchain/` directory with your configuration:
- RPC endpoints for all chains
- Private keys (for live trading)
- API keys for data providers
- Execution mode (PAPER or LIVE)

See `.env.example` for a complete list of required variables.

## Running the System

The brain (Python) and executor (JavaScript) communicate through the `../shared/signals/` directory. The brain detects arbitrage opportunities and writes signals, which the executor picks up and executes.
