# 🚀 Titan Installation Quick Reference

One-page reference for installing and running Titan.

## Single Command Installation

### Linux / macOS

```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_PRIVATE_KEY \
  --mode paper \
  --network polygon
```

### Windows

```batch
install_and_run_titan.bat
```

## Installation Options

| Option | Description | Default |
|--------|-------------|---------|
| `--wallet-key <KEY>` | Wallet private key (0x + 64 hex) | (prompted) |
| `--wallet-address <ADDR>` | Wallet address | (derived) |
| `--mode <paper\|live>` | Execution mode | `paper` |
| `--network <network>` | Deploy network | `polygon` |
| `--infura-key <KEY>` | Infura API key | (none) |
| `--alchemy-key <KEY>` | Alchemy API key | (none) |
| `--lifi-key <KEY>` | Li.Fi API key | (none) |
| `--skip-redis` | Skip Redis setup | false |
| `--help` | Show help | - |

## What Gets Installed

1. ✅ Node.js dependencies (ethers, hardhat, etc.)
   - Uses Yarn if available (recommended for better dependency resolution)
   - Falls back to npm with --legacy-peer-deps
2. ✅ Python dependencies (web3, pandas, etc.)
3. ✅ Rust components (rustworkx graph library)
4. ✅ Redis message queue (optional)
5. ✅ Smart contracts (compiled and deployed)
6. ✅ Wallet configuration (gas, signing, profits)
7. ✅ System launch (orchestrator + executor)

## Using Yarn (Recommended)

For better dependency conflict resolution:

```bash
# Install Yarn globally
npm install -g yarn

# Script will auto-detect and use Yarn
./install_and_run_titan.sh --wallet-key 0xYOUR_KEY

# Or use yarn setup directly
yarn install
yarn setup:yarn
```

**Benefits:**
- Better dependency resolution
- Faster installation
- No --legacy-peer-deps needed
- Deterministic installs

## After Installation

### Monitor Logs
```bash
tail -f logs/orchestrator.log  # Python ML engine
tail -f logs/executor.log      # Node.js execution
```

### Check Status
```bash
redis-cli ping                 # Check Redis
ps aux | grep -E "python.*orchestrator|node.*bot"  # Check processes
cat logs/installation_summary.txt  # View summary
```

### Stop System
```bash
# Find PIDs from launch output, then:
kill <ORCHESTRATOR_PID> <EXECUTOR_PID>

# Or:
pkill -f mainnet_orchestrator.py
pkill -f "node execution/bot.js"
```

### Restart System
```bash
./start_mainnet.sh paper  # Paper mode
./start_mainnet.sh live   # Live mode
```

## Modes

### Paper Mode (Safe)
- Real data, simulated execution
- No blockchain transactions
- No funds required (except for deployment)

### Live Mode (Production)
- Real data, real execution
- Live blockchain transactions
- ⚠️ **REAL FUNDS AT RISK**

## Supported Networks

- `polygon` (recommended for testing)
- `ethereum`, `arbitrum`, `optimism`, `base`
- `bsc`, `avalanche`, `fantom`, `linea`
- `scroll`, `mantle`, `zksync`, `blast`
- `celo`, `opbnb`

## Common Examples

### Basic Paper Trading
```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_KEY \
  --mode paper
```

### With API Keys
```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_KEY \
  --mode paper \
  --infura-key YOUR_INFURA_KEY \
  --alchemy-key YOUR_ALCHEMY_KEY \
  --lifi-key YOUR_LIFI_KEY
```

### Deploy to Arbitrum
```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_KEY \
  --mode paper \
  --network arbitrum
```

### Skip Redis
```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_KEY \
  --mode paper \
  --skip-redis
```

### Live Trading (Advanced)
```bash
./install_and_run_titan.sh \
  --wallet-key 0xYOUR_KEY \
  --mode live \
  --network polygon \
  --infura-key YOUR_INFURA_KEY \
  --alchemy-key YOUR_ALCHEMY_KEY
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Node.js not found | Install from https://nodejs.org/ |
| Python not found | Install from https://python.org/ |
| Redis failed | Use `--skip-redis` flag |
| Deployment failed | Check wallet has funds for gas |
| Invalid key format | Key must be 0x + 64 hex chars |
| Permission denied | Run `chmod +x install_and_run_titan.sh` |

## Getting Help

- **Full Guide**: [FULL_INSTALLATION_GUIDE.md](FULL_INSTALLATION_GUIDE.md)
- **Quick Start**: [QUICKSTART.md](QUICKSTART.md)
- **Installation**: [INSTALL.md](INSTALL.md)
- **Security**: [SECURITY_SUMMARY.md](SECURITY_SUMMARY.md)

## API Keys

Get free API keys from:
- **Infura**: https://infura.io/
- **Alchemy**: https://alchemy.com/
- **Li.Fi**: https://li.fi/

## Security Checklist

- ✅ Use dedicated wallet (not main wallet)
- ✅ Start with paper mode
- ✅ Test on testnet first
- ✅ Never commit .env file
- ✅ Keep private key secure
- ✅ Fund with small amounts initially
- ✅ Monitor logs regularly

## System Requirements

- **Node.js**: 18+
- **Python**: 3.11+
- **RAM**: 4GB+ (8GB recommended)
- **Disk**: 10GB free space
- **Network**: Broadband internet

## Next Steps

1. ✅ Run installation script
2. Monitor logs for opportunities
3. Tune parameters in `.env`
4. Deploy to additional networks
5. Scale to live trading (when ready)

---

**Ready to start? Run the installation script!** 🚀
