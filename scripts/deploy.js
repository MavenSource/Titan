const hre = require("hardhat");

async function main() {
  const chainId = await hre.ethers.provider.getNetwork().then(n => n.chainId);
  console.log(`\n🌐 Deploying to chain ID: ${chainId}`);
  
  // === CHAIN-SPECIFIC ADDRESSES ===
  const ADDRESSES = {
    1: { // Ethereum
      balancer: "0xbA1333333333a1BA1108E8412f11850A5C319bA9",
      aave: "0x87870Bca3F3fD6335C3F4ce8392D69350B4fA4E2"
    },
    137: { // Polygon
      balancer: "0xbA1333333333a1BA1108E8412f11850A5C319bA9",
      aave: "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    },
    42161: { // Arbitrum
      balancer: "0xbA1333333333a1BA1108E8412f11850A5C319bA9",
      aave: "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    },
    10: { // Optimism
      balancer: "0xbA1333333333a1BA1108E8412f11850A5C319bA9",
      aave: "0x794a61358D6845594F94dc1DB02A252b5b4814aD"
    },
    8453: { // Base
      balancer: "0xbA1333333333a1BA1108E8412f11850A5C319bA9",
      aave: "0xA238Dd80C259a72e81d7e4664a9801593F98d1c5"
    }
  };

  const addresses = ADDRESSES[Number(chainId)];
  if (!addresses) {
    console.error(`❌ Chain ID ${chainId} not supported yet`);
    process.exit(1);
  }

  // === DEPLOY EXECUTOR ===
  console.log("\n🚀 Deploying OmniArbExecutor...");
  const ExecutorFactory = await hre.ethers.getContractFactory("OmniArbExecutor");
  const executor = await ExecutorFactory.deploy(addresses.balancer, addresses.aave);
  await executor.waitForDeployment();
  const executorAddress = await executor.getAddress();
  console.log(`✅ OmniArbExecutor deployed to: ${executorAddress}`);

  // === DEPLOY REGISTRY INITIALIZER ===
  console.log("\n📋 Deploying RegistryInitializer...");
  const InitializerFactory = await hre.ethers.getContractFactory("RegistryInitializer");
  const initializer = await InitializerFactory.deploy();
  await initializer.waitForDeployment();
  const initializerAddress = await initializer.getAddress();
  console.log(`✅ RegistryInitializer deployed to: ${initializerAddress}`);

  // === INITIALIZE REGISTRIES ===
  console.log("\n🔧 Initializing registries...");
  
  const initFunctions = {
    1: ["initEthereumTokens", "initEthereumDEXs"],
    137: ["initPolygonTokens", "initPolygonDEXs"],
    42161: ["initArbitrumTokens", "initArbitrumDEXs"],
    10: ["initOptimismTokens", "initOptimismDEXs"],
    8453: ["initBaseTokens", "initBaseDEXs"],
    56: ["initBSCTokens", "initBSCDEXs"],
    43114: ["initAvalancheTokens", "initAvalancheDEXs"],
    250: ["initFantomTokens", "initFantomDEXs"]
  };

  const functions = initFunctions[Number(chainId)];
  if (functions) {
    for (const func of functions) {
      console.log(`  - Calling ${func}...`);
      const tx = await initializer[func](executorAddress);
      await tx.wait();
      console.log(`    ✅ ${func} completed`);
    }
  } else {
    console.log("⚠️  No registry initialization available for this chain");
  }

  // === SUMMARY ===
  console.log("\n" + "=".repeat(60));
  console.log("🎉 DEPLOYMENT COMPLETE");
  console.log("=".repeat(60));
  console.log(`OmniArbExecutor: ${executorAddress}`);
  console.log(`RegistryInitializer: ${initializerAddress}`);
  console.log(`Chain ID: ${chainId}`);
  console.log("=".repeat(60));
  console.log("\n💡 Next Steps:");
  console.log("1. Save the executor address to your .env file");
  console.log("2. Fund the executor with gas tokens");
  console.log("3. Test with a small arbitrage opportunity");
  console.log("4. Verify contracts on block explorer (optional)");
  console.log("\n");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});