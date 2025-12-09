require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

module.exports = {
  solidity: {
    version: "0.8.20",
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
    polygon: {
      url: process.env.RPC_POLYGON || "https://polygon-rpc.com",
      accounts: [process.env.PRIVATE_KEY],
      chainId: 137,
      gasPrice: "auto",
    },
    arbitrum: {
      url: process.env.RPC_ARBITRUM || "https://arb1.arbitrum.io/rpc",
      accounts: [process.env.PRIVATE_KEY],
      chainId: 42161,
    },
  },
  etherscan: {
    apiKey: {
      polygon: process.env.POLYGONSCAN_API_KEY,
      arbitrumOne: process.env.ARBISCAN_API_KEY,
    },
  },
};