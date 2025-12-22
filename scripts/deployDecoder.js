const hre = require("hardhat");

async function main() {
  console.log("🚀 Deploying OmniArbDecoder...");
  
  const Factory = await hre.ethers.getContractFactory("OmniArbDecoder");
  const decoder = await Factory.deploy();
  
  await decoder.waitForDeployment();
  
  const address = await decoder.getAddress();
  console.log("✅ OmniArbDecoder deployed to:", address);
  
  // Verify chain enum initialization
  console.log("\nVerifying chain enum mappings...");
  const chainEnums = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J'];
  const expectedChainIds = [1, 137, 8453, 42161, 10, 43114, 250, 100, 42220, 59144];
  
  for (let i = 0; i < chainEnums.length; i++) {
    const chainEnum = chainEnums[i];
    const expectedId = expectedChainIds[i];
    const actualId = await decoder.enumToChainId(
      hre.ethers.encodeBytes32String(chainEnum).slice(0, 4) // Convert to bytes1
    );
    console.log(`  ${chainEnum} → Chain ID ${actualId} ${actualId == expectedId ? '✅' : '❌'}`);
  }
  
  console.log("\n📝 Next steps:");
  console.log("1. Save the deployed address to your .env file:");
  console.log(`   DECODER_ADDRESS=${address}`);
  console.log("2. Configure token ranks for your chain:");
  console.log(`   DECODER_ADDRESS=${address} npx hardhat run scripts/configureTokenRanks.js --network <network>`);
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
