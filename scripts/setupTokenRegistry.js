const hre = require("hardhat");

/**
 * Script to configure token registry for OmniArbExecutor
 * Uses flexible uint8 token IDs (0-255) instead of hardcoded enums
 * 
 * Recommended ID Conventions:
 * 0-10: Universal tokens (WNATIVE, USDC, USDT, DAI, WBTC)
 * 11-50: Chain-specific top tokens
 * 51-100: DeFi protocol tokens
 * 101-200: Bridge tokens
 * 201-255: Reserved/Custom
 */

// Token Type enum (from OmniArbExecutor.sol)
const TokenType = {
  CANONICAL: 0,  // Native to the chain
  BRIDGED: 1,    // Bridged version (e.g., USDC.e)
  WRAPPED: 2     // Wrapped native (WETH, WMATIC, etc.)
};

// Universal token IDs (consistent across chains)
const UniversalTokenIds = {
  WNATIVE: 0,   // Wrapped native token
  USDC: 1,      // USD Coin
  USDT: 2,      // Tether USD
  DAI: 3,       // Dai Stablecoin
  WBTC: 4,      // Wrapped Bitcoin
  WETH: 5       // Wrapped Ether (for non-Ethereum chains)
};

// Chain-specific token IDs (11-50)
const ChainTokenIds = {
  UNI: 11,
  LINK: 12,
  AAVE: 13,
  CRV: 14,
  SUSHI: 15,
  BAL: 16,
  QUICK: 17,    // QuickSwap (Polygon)
  GHST: 18,     // Aavegotchi (Polygon)
  OP: 19,       // Optimism
  ARB: 20,      // Arbitrum
  AVAX: 21,     // Avalanche
  FTM: 22       // Fantom
};

// Token configurations per chain
const CHAIN_CONFIGS = {
  // Ethereum (Chain ID 1)
  1: {
    tokens: [
      { id: UniversalTokenIds.WETH, type: TokenType.WRAPPED, address: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2" },
      { id: UniversalTokenIds.USDC, type: TokenType.CANONICAL, address: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48" },
      { id: UniversalTokenIds.USDT, type: TokenType.CANONICAL, address: "0xdAC17F958D2ee523a2206206994597C13D831ec7" },
      { id: UniversalTokenIds.DAI, type: TokenType.CANONICAL, address: "0x6B175474E89094C44Da98b954EedeAC495271d0F" },
      { id: UniversalTokenIds.WBTC, type: TokenType.CANONICAL, address: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599" },
      { id: ChainTokenIds.UNI, type: TokenType.CANONICAL, address: "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984" },
      { id: ChainTokenIds.LINK, type: TokenType.CANONICAL, address: "0x514910771AF9Ca656af840dff83E8264EcF986CA" },
      { id: ChainTokenIds.AAVE, type: TokenType.CANONICAL, address: "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9" }
    ]
  },

  // Polygon (Chain ID 137)
  137: {
    tokens: [
      { id: UniversalTokenIds.WNATIVE, type: TokenType.WRAPPED, address: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270" }, // WMATIC
      { id: UniversalTokenIds.USDC, type: TokenType.CANONICAL, address: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359" },
      { id: UniversalTokenIds.USDC, type: TokenType.BRIDGED, address: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174" }, // USDC.e
      { id: UniversalTokenIds.USDT, type: TokenType.CANONICAL, address: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F" },
      { id: UniversalTokenIds.DAI, type: TokenType.CANONICAL, address: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063" },
      { id: UniversalTokenIds.WBTC, type: TokenType.CANONICAL, address: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6" },
      { id: UniversalTokenIds.WETH, type: TokenType.BRIDGED, address: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619" },
      { id: ChainTokenIds.QUICK, type: TokenType.CANONICAL, address: "0xB5C064F955D8e7F38fE0460C556a72987494eE17" },
      { id: ChainTokenIds.GHST, type: TokenType.CANONICAL, address: "0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7" }
    ]
  },

  // Arbitrum (Chain ID 42161)
  42161: {
    tokens: [
      { id: UniversalTokenIds.WETH, type: TokenType.WRAPPED, address: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1" },
      { id: UniversalTokenIds.USDC, type: TokenType.CANONICAL, address: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" },
      { id: UniversalTokenIds.USDC, type: TokenType.BRIDGED, address: "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8" }, // USDC.e
      { id: UniversalTokenIds.USDT, type: TokenType.CANONICAL, address: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9" },
      { id: UniversalTokenIds.DAI, type: TokenType.CANONICAL, address: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1" },
      { id: UniversalTokenIds.WBTC, type: TokenType.CANONICAL, address: "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f" },
      { id: ChainTokenIds.ARB, type: TokenType.CANONICAL, address: "0x912CE59144191C1204E64559FE8253a0e49E6548" }
    ]
  },

  // Optimism (Chain ID 10)
  10: {
    tokens: [
      { id: UniversalTokenIds.WETH, type: TokenType.WRAPPED, address: "0x4200000000000000000000000000000000000006" },
      { id: UniversalTokenIds.USDC, type: TokenType.CANONICAL, address: "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85" },
      { id: UniversalTokenIds.USDC, type: TokenType.BRIDGED, address: "0x7F5c764cBc14f9669B88837ca1490cCa17c31607" }, // USDC.e
      { id: UniversalTokenIds.USDT, type: TokenType.CANONICAL, address: "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58" },
      { id: UniversalTokenIds.DAI, type: TokenType.CANONICAL, address: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1" },
      { id: UniversalTokenIds.WBTC, type: TokenType.CANONICAL, address: "0x68f180fcCe6836688e9084f035309E29Bf0A2095" },
      { id: ChainTokenIds.OP, type: TokenType.CANONICAL, address: "0x4200000000000000000000000000000000000042" }
    ]
  },

  // Base (Chain ID 8453)
  8453: {
    tokens: [
      { id: UniversalTokenIds.WETH, type: TokenType.WRAPPED, address: "0x4200000000000000000000000000000000000006" },
      { id: UniversalTokenIds.USDC, type: TokenType.CANONICAL, address: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913" },
      { id: UniversalTokenIds.USDC, type: TokenType.BRIDGED, address: "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA" }, // USDbC
      { id: UniversalTokenIds.DAI, type: TokenType.CANONICAL, address: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb" }
    ]
  }
};

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Configuring OmniArbExecutor token registry with account:", deployer.address);
  
  // Get the executor contract address
  const executorAddress = process.env.EXECUTOR_ADDRESS;
  if (!executorAddress) {
    console.error("Error: EXECUTOR_ADDRESS environment variable not set");
    console.log("Usage: EXECUTOR_ADDRESS=0x... npx hardhat run scripts/setupTokenRegistry.js --network <network>");
    process.exit(1);
  }
  
  console.log("Using OmniArbExecutor at:", executorAddress);
  
  const executor = await hre.ethers.getContractAt("OmniArbExecutor", executorAddress);
  
  // Get current chain ID
  const chainId = await hre.ethers.provider.getNetwork().then(n => Number(n.chainId));
  console.log("Current chain ID:", chainId);
  
  const config = CHAIN_CONFIGS[chainId];
  if (!config) {
    console.error(`No token configuration for chain ID ${chainId}`);
    console.log("Supported chains:", Object.keys(CHAIN_CONFIGS).join(", "));
    process.exit(1);
  }
  
  console.log(`\nConfiguring ${config.tokens.length} tokens for chain ${chainId}...`);
  console.log("Token ID conventions:");
  console.log("  0-10: Universal tokens");
  console.log("  11-50: Chain-specific tokens");
  console.log("  51-255: Available for expansion\n");
  
  // Prepare batch arrays
  const chainIds = [];
  const tokenIds = [];
  const tokenTypes = [];
  const addresses = [];
  
  for (const token of config.tokens) {
    chainIds.push(chainId);
    tokenIds.push(token.id);
    tokenTypes.push(token.type);
    addresses.push(token.address);
    
    const typeStr = token.type === TokenType.CANONICAL ? "CANONICAL" : 
                    token.type === TokenType.BRIDGED ? "BRIDGED" : "WRAPPED";
    console.log(`  ID ${token.id}: ${typeStr} - ${token.address}`);
  }
  
  // Execute batch configuration
  console.log("\nExecuting batch token registration...");
  const tx = await executor.batchSetTokens(chainIds, tokenIds, tokenTypes, addresses);
  console.log("Transaction submitted:", tx.hash);
  
  const receipt = await tx.wait();
  console.log("Transaction confirmed in block:", receipt.blockNumber);
  console.log("Gas used:", receipt.gasUsed.toString());
  
  console.log("\n✅ Token registry configuration complete!");
  console.log("\nNext steps:");
  console.log("1. Tokens are now registered and can be used with REGISTRY_ENUMS encoding");
  console.log("2. For rare/unregistered tokens, use RAW_ADDRESSES encoding");
  console.log("3. Off-chain brain (brain.py) will automatically use optimal encoding");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
