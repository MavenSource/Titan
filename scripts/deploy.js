const hre = require("hardhat");

async function main() {
  // Verify ethers is available
  if (!hre.ethers) {
    throw new Error(
      "Hardhat ethers plugin not loaded. " +
      "Make sure @nomicfoundation/hardhat-toolbox is uncommented in hardhat.config.js " +
      "and @nomicfoundation/hardhat-ethers is installed."
    );
  }

  // Balancer V3 Vault (Universal Address)
  const BALANCER_V3 = "0xbA1333333333a1BA1108E8412f11850A5C319bA9";
  
  // Aave V3 Pool (Changes per chain! Example: Polygon)
  const AAVE_POLYGON = "0x794a61358D6845594F94dc1DB02A252b5b4814aD";

  console.log("🚀 Deploying OmniArbExecutor...");
  
  // Get deployer info
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying with account:", deployer.address);
  
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log("Account balance:", hre.ethers.formatEther(balance));
  
  if (balance === 0n) {
    throw new Error("Deployer account has no balance for gas fees");
  }
  
  const Factory = await hre.ethers.getContractFactory("OmniArbExecutor");
  console.log("Deploying contract...");
  
  const contract = await Factory.deploy(BALANCER_V3, AAVE_POLYGON);
  console.log("Waiting for deployment confirmation...");
  
  await contract.waitForDeployment();
  
  const address = await contract.getAddress();
  console.log("\n✅ Deployed successfully!");
  console.log("Contract address:", address);
  console.log("\nAdd this to your .env file:");
  console.log(`EXECUTOR_ADDRESS=${address}`);
}

main().catch((error) => {
  console.error("\n❌ Deployment failed:");
  console.error(error.message);
  process.exitCode = 1;
});