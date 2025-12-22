/**
 * Example: Using the OmniArb Matrix A-J Decoder
 * 
 * This example demonstrates how to:
 * 1. Deploy the decoder
 * 2. Configure token ranks
 * 3. Encode and decode payloads
 * 4. Validate payloads on-chain
 */

const { ethers } = require("hardhat");
const encoder = require("./omniArbEncoder");

async function main() {
  console.log("=== OmniArb Matrix A-J Example ===\n");
  
  // Get signer
  const [deployer] = await ethers.getSigners();
  console.log("Using account:", deployer.address);
  
  // Get network info
  const network = await ethers.provider.getNetwork();
  const chainId = Number(network.chainId);
  console.log("Chain ID:", chainId);
  
  // Get chain enum for current network
  let chainEnum;
  try {
    chainEnum = encoder.getChainEnum(chainId);
    console.log("Chain Enum:", chainEnum, "-", encoder.getChainName(chainEnum));
  } catch (e) {
    console.log("⚠️  Current chain not in A-J mapping, using Polygon (B) for example");
    chainEnum = 'B';
  }
  console.log();
  
  // Step 1: Deploy the decoder (skip if already deployed)
  console.log("Step 1: Checking for existing decoder deployment...");
  const decoderAddress = process.env.DECODER_ADDRESS;
  
  let decoder;
  if (decoderAddress) {
    console.log("Using existing decoder at:", decoderAddress);
    decoder = await ethers.getContractAt("OmniArbDecoder", decoderAddress);
  } else {
    console.log("Deploying new OmniArbDecoder...");
    const DecoderFactory = await ethers.getContractFactory("OmniArbDecoder");
    decoder = await DecoderFactory.deploy();
    await decoder.waitForDeployment();
    const address = await decoder.getAddress();
    console.log("✅ Deployed to:", address);
    console.log("💡 Save this address: DECODER_ADDRESS=" + address);
  }
  console.log();
  
  // Step 2: Verify chain enum mappings
  console.log("Step 2: Verifying chain enum mappings...");
  for (const [letter, info] of Object.entries(encoder.CHAIN_ENUM_MAP)) {
    const chainIdFromContract = await decoder.enumToChainId(encoder.toBytes1(letter));
    const match = Number(chainIdFromContract) === info.chainId ? "✅" : "❌";
    console.log(`  ${letter} → ${info.name} (${info.chainId}) ${match}`);
  }
  console.log();
  
  // Step 3: Configure some test token ranks
  console.log("Step 3: Configuring test token ranks...");
  const testRanks = chainEnum === 'B' ? [2000, 2001, 2002] : [1000, 1001, 1002];
  const testTokens = [
    "0x0000000000000000000000000000000000000001", // Mock token 1
    "0x0000000000000000000000000000000000000002", // Mock token 2
    "0x0000000000000000000000000000000000000003"  // Mock token 3
  ];
  
  console.log(`Configuring ${testRanks.length} test tokens...`);
  const configureTx = await decoder.configureTokenRanks(testRanks, testTokens);
  await configureTx.wait();
  console.log("✅ Token ranks configured");
  console.log();
  
  // Step 4: Verify token configuration
  console.log("Step 4: Verifying token configuration...");
  for (let i = 0; i < testRanks.length; i++) {
    const tokenAddress = await decoder.rankToToken(testRanks[i]);
    console.log(`  Rank ${testRanks[i]} → ${tokenAddress}`);
  }
  console.log();
  
  // Step 5: Encode a test payload
  console.log("Step 5: Encoding a test payload...");
  const currentChainId = await decoder.enumToChainId(encoder.toBytes1(chainEnum));
  
  const payload = encoder.encodePayload({
    chainEnum: chainEnum,
    tokenRank: testRanks[1], // Use second test token
    amount: ethers.parseEther("1"),
    routeParams: "0x",
    minProfitBps: 100, // 1%
    expiry: Math.floor(Date.now() / 1000) + 3600, // 1 hour
    receiver: deployer.address,
    routeRegistryHash: ethers.ZeroHash,
    nonce: Math.floor(Date.now() / 1000)
  });
  
  console.log("Payload encoded:", payload.slice(0, 66) + "...");
  console.log();
  
  // Step 6: Decode payload using encoder utility
  console.log("Step 6: Decoding payload off-chain...");
  const decoded = encoder.decodePayload(payload);
  console.log("Decoded payload:");
  console.log("  Chain:", decoded.chainEnum, "-", decoded.chainName);
  console.log("  Token Rank:", decoded.tokenRank);
  console.log("  Amount:", ethers.formatEther(decoded.amount), "tokens");
  console.log("  Min Profit:", decoded.minProfitBps / 100, "%");
  console.log("  Receiver:", decoded.receiver);
  console.log();
  
  // Step 7: Decode and validate on-chain (only if on correct chain)
  if (Number(currentChainId) === chainId) {
    console.log("Step 7: Decoding and validating on-chain...");
    try {
      const decodedOnChain = await decoder.decodePayload(payload);
      console.log("✅ Payload validated on-chain");
      console.log("  Chain Enum:", decodedOnChain.chainEnum);
      console.log("  Token Rank:", Number(decodedOnChain.tokenRank));
      console.log("  Amount:", decodedOnChain.amount.toString());
      console.log("  Nonce:", decodedOnChain.nonce.toString());
    } catch (error) {
      console.log("❌ Validation failed:", error.message);
    }
  } else {
    console.log("Step 7: Skipping on-chain validation (chain mismatch)");
    console.log(`  Current chain: ${chainId}`);
    console.log(`  Payload chain: ${Number(currentChainId)}`);
  }
  console.log();
  
  // Step 8: Demonstrate token resolution
  console.log("Step 8: Resolving token from rank...");
  const resolvedToken = await decoder.getTokenByRank(testRanks[1]);
  console.log(`  Rank ${testRanks[1]} → ${resolvedToken}`);
  console.log();
  
  console.log("=== Example Complete ===");
  console.log("\n💡 Next steps:");
  console.log("1. Configure real token addresses using scripts/configureTokenRanks.js");
  console.log("2. Set up USDC normalization for chains with USDC.e");
  console.log("3. Integrate decoder into your arbitrage execution pipeline");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
