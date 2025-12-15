require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

// Helper function to get accounts array (empty if no valid private key)
const getAccounts = () => {
  const pk = process.env.PRIVATE_KEY;
  // Check if private key is valid (0x prefix + 64 hex chars)
  if (pk && pk.startsWith('0x') && pk.length === 66 && /^0x[0-9a-fA-F]{64}$/.test(pk)) {
    return [pk];
  }
  return [];
};

module.exports = {
  solidity: {
    version: "0.8.24",
    settings: {
      optimizer: {
        enabled: true,
        runs: 200,
      },
      viaIR: true, // Important for complex arbitrage contracts
    },
  },
  networks: {
    hardhat: {
      chainId: 31337,
      forking: {
        url: process.env.RPC_POLYGON || "https://polygon-rpc.com", // Fork Polygon for testing
      },
    },
    ethereum: {
      url: process.env.RPC_ETHEREUM || "https://eth-mainnet.g.alchemy.com",
      accounts: getAccounts(),
      chainId: 1,
    },
    polygon: {
      url: process.env.RPC_POLYGON || "https://polygon-rpc.com",
      accounts: getAccounts(),
      chainId: 137,
      gasPrice: "auto",
    },
    arbitrum: {
      url: process.env.RPC_ARBITRUM || "https://arb1.arbitrum.io/rpc",
      accounts: getAccounts(),
      chainId: 42161,
    },
    optimism: {
      url: process.env.RPC_OPTIMISM || "https://mainnet.optimism.io",
      accounts: getAccounts(),
      chainId: 10,
    },
    base: {
      url: process.env.RPC_BASE || "https://mainnet.base.org",
      accounts: getAccounts(),
      chainId: 8453,
    },
    bsc: {
      url: process.env.RPC_BSC || "https://bsc-dataseed.binance.org",
      accounts: getAccounts(),
      chainId: 56,
    },
    avalanche: {
      url: process.env.RPC_AVALANCHE || "https://api.avax.network/ext/bc/C/rpc",
      accounts: getAccounts(),
      chainId: 43114,
    },
    fantom: {
      url: process.env.RPC_FANTOM || "https://rpc.ftm.tools",
      accounts: getAccounts(),
      chainId: 250,
    },
    linea: {
      url: process.env.RPC_LINEA || "https://rpc.linea.build",
      accounts: getAccounts(),
      chainId: 59144,
    },
    scroll: {
      url: process.env.RPC_SCROLL || "https://rpc.scroll.io",
      accounts: getAccounts(),
      chainId: 534352,
    },
    mantle: {
      url: process.env.RPC_MANTLE || "https://rpc.mantle.xyz",
      accounts: getAccounts(),
      chainId: 5000,
    },
    zksync: {
      url: process.env.RPC_ZKSYNC || "https://mainnet.era.zksync.io",
      accounts: getAccounts(),
      chainId: 324,
    },
    blast: {
      url: process.env.RPC_BLAST || "https://rpc.blast.io",
      accounts: getAccounts(),
      chainId: 81457,
    },
    celo: {
      url: process.env.RPC_CELO || "https://forno.celo.org",
      accounts: getAccounts(),
      chainId: 42220,
    },
    opbnb: {
      url: process.env.RPC_OPBNB || "https://opbnb-mainnet-rpc.bnbchain.org",
      accounts: getAccounts(),
      chainId: 204,
    },
  },
  etherscan: {
    apiKey: {
      polygon: process.env.POLYGONSCAN_API_KEY,
      arbitrumOne: process.env.ARBISCAN_API_KEY,
    },
  },
};