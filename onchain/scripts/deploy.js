const hre = require("hardhat");

async function main() {
  // Balancer V3 Vault (Universal Address)
  const BALANCER_V3 = "0xbA1333333333a1BA1108E8412f11850A5C319bA9";
  
  // Aave V3 Pool (Changes per chain! Example: Polygon)
  const AAVE_POLYGON = "0x794a61358D6845594F94dc1DB02A252b5b4814aD";

  console.log("🚀 Deploying OmniArbExecutor...");
  
  const Factory = await hre.ethers.getContractFactory("OmniArbExecutor");
  const contract = await Factory.deploy(BALANCER_V3, AAVE_POLYGON);
  
  await contract.waitForDeployment();
  
  console.log("✅ Deployed to:", await contract.getAddress());
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});