import { ethers } from "hardhat";
import { Dex, TokenId, TokenType } from "../src/encoding/titanEnums";

async function main() {
  const EX = process.env.EXECUTOR!;
  const network = await ethers.provider.getNetwork();
  const chainId = network.chainId;
  const expectedChainId = process.env.CHAIN_ID;
  if (!expectedChainId) {
    throw new Error("Environment variable CHAIN_ID must be set to the expected network chain ID before seeding.");
  }
  if (chainId.toString() !== expectedChainId) {
    throw new Error(`Connected chainId ${chainId.toString()} does not match expected CHAIN_ID ${expectedChainId}. Aborting seeding.`);
  }

  const ex = await ethers.getContractAt("OmniArbExecutor", EX);

  // DEX routers
  await (await ex.setDexRouter(chainId, Dex.UniV2, process.env.QUICKSWAP_ROUTER!)).wait();
  await (await ex.setDexRouter(chainId, Dex.UniV3, process.env.UNIV3_ROUTER!)).wait();
  // Curve uses POOL addresses per-hop, but you can still store a "default" Curve router if you want.
  // Recommended: store Curve = 0x0 and use RAW for curve pools OR store known pool addresses separately.

  // Tokens
  await (await ex.setToken(chainId, TokenId.WNATIVE, TokenType.WRAPPED, process.env.WNATIVE!)).wait();
  await (await ex.setToken(chainId, TokenId.USDC, TokenType.CANONICAL, process.env.USDC!)).wait();
  await (await ex.setToken(chainId, TokenId.USDT, TokenType.CANONICAL, process.env.USDT!)).wait();
  await (await ex.setToken(chainId, TokenId.DAI,  TokenType.CANONICAL, process.env.DAI!)).wait();

  console.log("Seeded registries on chainId:", chainId.toString());
}

main().catch((e) => { console.error(e); process.exit(1); });
