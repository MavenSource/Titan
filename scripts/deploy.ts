import { ethers } from "hardhat";

async function main() {
  const AAVE_POOL = process.env.AAVE_POOL!;
  const BALANCER_VAULT = process.env.BALANCER_VAULT!;

  const Executor = await ethers.getContractFactory("OmniArbExecutor");
  const ex = await Executor.deploy(AAVE_POOL, BALANCER_VAULT);
  await ex.waitForDeployment();

  console.log("OmniArbExecutor:", await ex.getAddress());
}

main().catch((e) => { console.error(e); process.exit(1); });
