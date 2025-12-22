const hre = require("hardhat");

/**
 * Script to configure token rankings for OmniArbDecoder
 * Based on the OmniArb Matrix A-J design specification
 */

// Token rank ranges per chain letter (A-J)
// A: 1000-1999, B: 2000-2999, C: 3000-3999, D: 4000-4999, E: 5000-5999
// F: 6000-6999, G: 7000-7999, H: 8000-8999, I: 9000-9999, J: 10000-10999

// ETHEREUM (A) - Range 1000-1999
const ETHEREUM_TOKENS = {
  WETH: "0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2",
  USDC: "0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48",
  USDT: "0xdAC17F958D2ee523a2206206994597C13D831ec7",
  DAI: "0x6B175474E89094C44Da98b954EedeAC495271d0F",
  WBTC: "0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599",
  UNI: "0x1f9840a85d5aF5bf1D1762F925BDADdC4201F984",
  LINK: "0x514910771AF9Ca656af840dff83E8264EcF986CA",
  AAVE: "0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9",
  MATIC: "0x7D1AfA7B718fb893dB30A3aBc0Cfc608AaCfeBB0",
  CRV: "0xD533a949740bb3306d119CC777fa900bA034cd52",
  SNX: "0xC011a73ee8576Fb46F5E1c5751cA3B9Fe0af2a6F",
  MKR: "0x9f8F72aA9304c8B593d555F12eF6589cC3A579A2",
  COMP: "0xc00e94Cb662C3520282E6f5717214004A7f26888",
  SUSHI: "0x6B3595068778DD592e39A122f4f5a5cF09C90fE2",
  FXS: "0x3432B6A60D23Ca0dFCa7761B7ab56459D9C964D0",
  FRAX: "0x853d955aCEf822Db058eb8505911ED77F175b99e",
  BAL: "0xba100000625a3754423978a60c9317c58a424e3D",
  LDO: "0x5A98FcBEA516Cf06857215779Fd812CA3beF1B32",
  RPL: "0xD33526068D116cE69F19A9ee46F0bd304F21A51f",
  STETH: "0xae7ab96520DE3A18E5e111B5EaAb095312D7fE84"
};

// POLYGON (B) - Range 2000-2999
const POLYGON_TOKENS = {
  WMATIC: "0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270",
  WETH: "0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619",
  USDC: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", // Canonical USDC
  "USDC.e": "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", // Bridged USDC
  USDT: "0xc2132D05D31c914a87C6611C10748AEb04B58e8F",
  DAI: "0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063",
  WBTC: "0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6",
  AAVE: "0xD6DF932A45C0f255f85145f286eA0b292B21C90B",
  LINK: "0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39",
  CRV: "0x172370d5Cd63279eFa6d502DAB29171933a610AF",
  SUSHI: "0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a",
  BAL: "0x9a71012B13CA4d3D0Cdc72A177DF3ef03b0E76A3",
  GHST: "0x385Eeac5cB85A38A9a07A70c73e0a3271CfB54A7",
  QUICK: "0xB5C064F955D8e7F38fE0460C556a72987494eE17",
  SAND: "0xBbba073C31bF03b8ACf7c28EF0738DeCF3695683",
  MANA: "0xA1c57f48F0Deb89f569dFbE6E2B7f46D33606fD4"
};

// BASE (C) - Range 3000-3999
const BASE_TOKENS = {
  WETH: "0x4200000000000000000000000000000000000006",
  USDC: "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  USDbC: "0xd9aAEc86B65D86f6A7B5B1b0c42FFA531710b6CA", // Bridged USDC on Base
  DAI: "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
  // Add more Base tokens as they become available
};

// ARBITRUM (D) - Range 4000-4999
const ARBITRUM_TOKENS = {
  WETH: "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
  USDC: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", // Canonical USDC
  "USDC.e": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", // Bridged USDC
  USDT: "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9",
  DAI: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
  WBTC: "0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f",
  ARB: "0x912CE59144191C1204E64559FE8253a0e49E6548",
  GMX: "0xfc5A1A6EB076a2C7aD06eD22C90d7E710E35ad0a",
  MAGIC: "0x539bdE0d7Dbd336b79148AA742883198BBF60342",
  LINK: "0xf97f4df75117a78c1A5a0DBb814Af92458539FB4",
  UNI: "0xFa7F8980b0f1E64A2062791cc3b0871572f1F7f0",
  SUSHI: "0xd4d42F0b6DEF4CE0383636770eF773390d85c61A",
  CRV: "0x11cDb42B0EB46D95f990BeDD4695A6e3fA034978",
  AAVE: "0xba5DdD1f9d7F570dc94a51479a000E3BCE967196",
  FRAX: "0x17FC002b466eEc40DaE837Fc4bE5c67993ddBd6F",
  FXS: "0x9d2F299715D94d8A7E6F5eaa8E654E8c74a988A7"
};

// OPTIMISM (E) - Range 5000-5999
const OPTIMISM_TOKENS = {
  WETH: "0x4200000000000000000000000000000000000006",
  USDC: "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85", // Canonical USDC
  "USDC.e": "0x7F5c764cBc14f9669B88837ca1490cCa17c31607", // Bridged USDC
  USDT: "0x94b008aA00579c1307B0EF2c499aD98a8ce58e58",
  DAI: "0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1",
  WBTC: "0x68f180fcCe6836688e9084f035309E29Bf0A2095",
  OP: "0x4200000000000000000000000000000000000042",
  SNX: "0x8700dAec35aF8Ff88c16BdF0418774CB3D7599B4",
  LINK: "0x350a791Bfc2C21F9Ed5d10980Dad2e2638ffa7f6",
  // Add more Optimism tokens
};

// AVALANCHE (F) - Range 6000-6999
const AVALANCHE_TOKENS = {
  WAVAX: "0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7",
  USDC: "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E", // Canonical USDC
  "USDC.e": "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664", // Bridged USDC
  USDT: "0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7",
  "USDT.e": "0xc7198437980c041c805A1EDcbA50c1Ce5db95118", // Bridged USDT
  DAI: "0xd586E7F844cEa2F87f50152665BCbc2C279D8d70",
  WBTC: "0x50b7545627a5162F82A992c33b87aDc75187B218",
  WETH: "0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB",
  // Add more Avalanche tokens
};

// FANTOM (G) - Range 7000-7999
const FANTOM_TOKENS = {
  WFTM: "0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83",
  USDC: "0x04068DA6C83AFCFA0e13ba15A6696662335D5B75",
  fUSDT: "0x049d68029688eAbF473097a2fC38ef61633A3C7A",
  DAI: "0x8D11eC38a3EB5E956B052f67Da8Bdc9bef8Abf3E",
  WBTC: "0x321162Cd933E2Be498Cd2267a90534A804051b11",
  WETH: "0x74b23882a30290451A17c44f4F05243b6b58C76d",
  // Add more Fantom tokens
};

// GNOSIS (H) - Range 8000-8999
const GNOSIS_TOKENS = {
  WXDAI: "0xe91D153E0b41518A2Ce8Dd3D7944Fa863463a97d",
  USDC: "0xDDAfbb505ad214D7b80b1f830fcCc89B60fb7A83", // USDC on Gnosis
  USDT: "0x4ECaBa5870353805a9F068101A40E0f32ed605C6",
  WETH: "0x6A023CCd1ff6F2045C3309768eAd9E68F978f6e1",
  GNO: "0x9C58BAcC331c9aa871AFD802DB6379a98e80CEdb",
  // Add more Gnosis tokens
};

// CELO (I) - Range 9000-9999
const CELO_TOKENS = {
  CELO: "0x471EcE3750Da237f93B8E339c536989b8978a438",
  cUSD: "0x765DE816845861e75A25fCA122bb6898B8B1282a",
  cEUR: "0xD8763CBa276a3738E6DE85b4b3bF5FDed6D6cA73",
  cREAL: "0xe8537a3d056DA446677B9E9d6c5dB704EaAb4787",
  // Add more Celo tokens
};

// LINEA (J) - Range 10000-10999
const LINEA_TOKENS = {
  WETH: "0xe5D7C2a44FfDDf6b295A15c148167daaAf5Cf34f",
  USDC: "0x176211869cA2b568f2A7D4EE941E073a821EE1ff",
  USDT: "0xA219439258ca9da29E9Cc4cE5596924745e12B93",
  WBTC: "0x3aAB2285ddcDdaD8edf438C1bAB47e1a9D05a9b4",
  // Add more Linea tokens
};

// USDC variants that need normalization (bridged -> canonical)
const USDC_NORMALIZATIONS = {
  137: { // Polygon
    bridged: "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", // USDC.e
    canonical: "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359" // USDC
  },
  42161: { // Arbitrum
    bridged: "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", // USDC.e
    canonical: "0xaf88d065e77c8cC2239327C5EDb3A432268e5831" // USDC
  },
  10: { // Optimism
    bridged: "0x7F5c764cBc14f9669B88837ca1490cCa17c31607", // USDC.e
    canonical: "0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85" // USDC
  },
  43114: { // Avalanche
    bridged: "0xA7D7079b0FEaD91F3e65f86E8915Cb59c1a4C664", // USDC.e
    canonical: "0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E" // USDC
  }
};

/**
 * Build token rank arrays from token configuration
 */
function buildTokenRanks(tokens, rangeStart) {
  const ranks = [];
  const addresses = [];
  
  let index = 0;
  for (const [symbol, address] of Object.entries(tokens)) {
    const rank = rangeStart + index;
    ranks.push(rank);
    addresses.push(address);
    console.log(`  ${rank}: ${symbol} (${address})`);
    index++;
  }
  
  return { ranks, addresses };
}

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Configuring token ranks with account:", deployer.address);
  
  // Get the decoder contract address (should be passed as argument or from environment)
  const decoderAddress = process.env.DECODER_ADDRESS;
  if (!decoderAddress) {
    console.error("Error: DECODER_ADDRESS environment variable not set");
    console.log("Usage: DECODER_ADDRESS=0x... npx hardhat run scripts/configureTokenRanks.js --network <network>");
    process.exit(1);
  }
  
  console.log("Using OmniArbDecoder at:", decoderAddress);
  
  const decoder = await hre.ethers.getContractAt("OmniArbDecoder", decoderAddress);
  
  // Get current chain ID to configure appropriate tokens
  const chainId = await hre.ethers.provider.getNetwork().then(n => Number(n.chainId));
  console.log("Current chain ID:", chainId);
  
  let ranks, addresses, chainName;
  
  // Configure tokens based on current chain
  switch (chainId) {
    case 1: // Ethereum
      chainName = "Ethereum";
      ({ ranks, addresses } = buildTokenRanks(ETHEREUM_TOKENS, 1000));
      break;
    case 137: // Polygon
      chainName = "Polygon";
      ({ ranks, addresses } = buildTokenRanks(POLYGON_TOKENS, 2000));
      break;
    case 8453: // Base
      chainName = "Base";
      ({ ranks, addresses } = buildTokenRanks(BASE_TOKENS, 3000));
      break;
    case 42161: // Arbitrum
      chainName = "Arbitrum";
      ({ ranks, addresses } = buildTokenRanks(ARBITRUM_TOKENS, 4000));
      break;
    case 10: // Optimism
      chainName = "Optimism";
      ({ ranks, addresses } = buildTokenRanks(OPTIMISM_TOKENS, 5000));
      break;
    case 43114: // Avalanche
      chainName = "Avalanche";
      ({ ranks, addresses } = buildTokenRanks(AVALANCHE_TOKENS, 6000));
      break;
    case 250: // Fantom
      chainName = "Fantom";
      ({ ranks, addresses } = buildTokenRanks(FANTOM_TOKENS, 7000));
      break;
    case 100: // Gnosis
      chainName = "Gnosis";
      ({ ranks, addresses } = buildTokenRanks(GNOSIS_TOKENS, 8000));
      break;
    case 42220: // Celo
      chainName = "Celo";
      ({ ranks, addresses } = buildTokenRanks(CELO_TOKENS, 9000));
      break;
    case 59144: // Linea
      chainName = "Linea";
      ({ ranks, addresses } = buildTokenRanks(LINEA_TOKENS, 10000));
      break;
    default:
      console.error(`Unsupported chain ID: ${chainId}`);
      process.exit(1);
  }
  
  console.log(`\nConfiguring ${ranks.length} tokens for ${chainName}...`);
  
  // Configure token ranks in batches to avoid gas limits
  const BATCH_SIZE = 20;
  for (let i = 0; i < ranks.length; i += BATCH_SIZE) {
    const batchRanks = ranks.slice(i, i + BATCH_SIZE);
    const batchAddresses = addresses.slice(i, i + BATCH_SIZE);
    const batchNumber = Math.floor(i / BATCH_SIZE) + 1;
    
    console.log(`Configuring batch ${batchNumber}...`);
    const tx = await decoder.configureTokenRanks(batchRanks, batchAddresses);
    await tx.wait();
    console.log(`Batch ${batchNumber} configured. Tx: ${tx.hash}`);
  }
  
  // Configure USDC normalization if applicable for this chain
  if (USDC_NORMALIZATIONS[chainId]) {
    console.log("\nConfiguring USDC normalization...");
    const { bridged, canonical } = USDC_NORMALIZATIONS[chainId];
    const tx = await decoder.configureBridgedUSDC(chainId, bridged, canonical);
    await tx.wait();
    console.log(`USDC normalization configured. Tx: ${tx.hash}`);
  }
  
  console.log("\n✅ Token rank configuration complete!");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
