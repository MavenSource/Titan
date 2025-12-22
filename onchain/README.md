# On-Chain Smart Contracts

This directory contains all Solidity smart contracts for the Titan arbitrage system.

## Structure
- `contracts/` - Solidity smart contracts and interfaces
- `scripts/` - Deployment and utility scripts
- `test/` - Contract tests
- `hardhat.config.js` - Hardhat configuration

## Build & Deploy

```bash
# Install dependencies
npm install

# Compile contracts
npx hardhat compile

# Deploy to a network
npx hardhat run scripts/deploy.js --network polygon
```

## Configuration

The Hardhat configuration loads environment variables from `../offchain/.env`. Make sure to configure your RPC endpoints and private keys there.

## Artifacts

Compiled contract artifacts are stored in `./artifacts/` and should be copied to `../shared/abi/` for use by off-chain components.
