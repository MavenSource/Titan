import { ethers } from "ethers";
import { Dex, SwapProtocol, TokenId, TokenType } from "./titanEnums";
import type { RegistryHop } from "./routeEncoder";

const abi = ethers.AbiCoder.defaultAbiCoder();

// A–J matrix "DEX Compatibility" → (protocol + dexId)
export function dexToHop(compat: string): { protocol: number; dexId: number } {
  const s = compat.toLowerCase();

  if (s.includes("uniswap v2")) return { protocol: SwapProtocol.UNIV2, dexId: Dex.UniV2 };
  if (s.includes("uniswap v3")) return { protocol: SwapProtocol.UNIV3, dexId: Dex.UniV3 };
  if (s.includes("curve")) return { protocol: SwapProtocol.CURVE, dexId: Dex.Curve };

  // IMPORTANT: Balancer is supported as a flash loan source (FlashSource.BalancerV3)
  // but Balancer swaps are not yet implemented in SwapHandler.
  if (s.includes("balancer")) throw new Error("Balancer swaps not supported by SwapHandler. Use Balancer as flash source only.");

  throw new Error(`Unknown DEX compatibility: ${compat}`);
}

// Token symbol → TokenId + TokenType
// IMPORTANT: Only supports TokenIds you have on-chain. Extend by APPENDING enum members.
export function tokenToIdType(native: string, wrapped: string): { tokenOutId: number; tokenOutType: number } {
  const t = (wrapped || native).toUpperCase();

  // "Wrapped native" tokens map to WNATIVE + WRAPPED
  if (["WETH", "WMATIC", "WBNB", "WAVAX", "WFTM"].includes(t)) {
    return { tokenOutId: TokenId.WNATIVE, tokenOutType: TokenType.WRAPPED };
  }

  // Canonical stablecoins
  if (t === "USDC") return { tokenOutId: TokenId.USDC, tokenOutType: TokenType.CANONICAL };
  if (t === "USDT") return { tokenOutId: TokenId.USDT, tokenOutType: TokenType.CANONICAL };
  if (t === "DAI")  return { tokenOutId: TokenId.DAI,  tokenOutType: TokenType.CANONICAL };

  // Bridged variants treated as TokenType.BRIDGED of base TokenId (when it's the same asset class)
  if (t.includes("USDC")) return { tokenOutId: TokenId.USDC, tokenOutType: TokenType.BRIDGED };
  if (t.includes("USDT")) return { tokenOutId: TokenId.USDT, tokenOutType: TokenType.BRIDGED };
  if (t.includes("DAI"))  return { tokenOutId: TokenId.DAI,  tokenOutType: TokenType.BRIDGED };

  throw new Error(`Token not supported by TokenId enum yet: ${t}`);
}

// Build a 1-hop route from a matrix row (you'll likely build multi-hop from multiple rows)
export function matrixRowToHop(row: {
  dexCompatibility: string;     // e.g. "Curve, Uniswap"
  nativeToken: string;          // e.g. "USDC"
  wrappedEquivalent: string;    // e.g. "axlUSDC"
  feeTier?: number;             // uni v3 fee (500/3000/10000)
  curveI?: number;              // curve i index
  curveJ?: number;              // curve j index
}): RegistryHop {

  const { protocol, dexId } = dexToHop(row.dexCompatibility);
  const { tokenOutId, tokenOutType } = tokenToIdType(row.nativeToken, row.wrappedEquivalent);

  let extra = "0x";

  if (protocol === SwapProtocol.UNIV3) {
    const fee = row.feeTier ?? 3000;
    extra = abi.encode(["uint24"], [fee]);
  }

  if (protocol === SwapProtocol.CURVE) {
    const i = row.curveI ?? 0;
    const j = row.curveJ ?? 1;
    extra = abi.encode(["int128", "int128"], [i, j]);
  }

  // UniV2 keeps extra = 0x

  return { protocol, dexId, tokenOutId, tokenOutType, extra };
}
