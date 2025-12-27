import { ethers } from "ethers";
import { RouteEncoding } from "./titanEnums";

const abi = ethers.AbiCoder.defaultAbiCoder();

export type RegistryHop = {
  protocol: number;       // 1/2/3
  dexId: number;          // Dex enum numeric
  tokenOutId: number;     // TokenId enum numeric
  tokenOutType: number;   // TokenType enum numeric
  extra: string;          // bytes
};

export function encodeRegistryRoute(hops: RegistryHop[]): string {
  const protocols = hops.map(h => h.protocol);
  const dexIds = hops.map(h => h.dexId);
  const tokenOutIds = hops.map(h => h.tokenOutId);
  const tokenOutTypes = hops.map(h => h.tokenOutType);
  const extra = hops.map(h => h.extra);

  return abi.encode(
    ["uint8", "uint8[]", "uint8[]", "uint8[]", "uint8[]", "bytes[]"],
    [RouteEncoding.REGISTRY_ENUMS, protocols, dexIds, tokenOutIds, tokenOutTypes, extra]
  );
}
