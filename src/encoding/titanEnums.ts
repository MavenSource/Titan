export const FlashSource = { AaveV3: 0, BalancerV3: 1 } as const;
export const RouteEncoding = { RAW_ADDRESSES: 0, REGISTRY_ENUMS: 1 } as const;

export const SwapProtocol = { UNIV2: 1, UNIV3: 2, CURVE: 3 } as const;

export const Dex = { UniV2: 0, UniV3: 1, Curve: 2, Balancer: 3, Dodo: 4, Unknown: 5 } as const;

export const TokenType = { CANONICAL: 0, BRIDGED: 1, WRAPPED: 2 } as const;

export const TokenId = { WNATIVE: 0, USDC: 1, USDT: 2, DAI: 3, WETH: 4, WBTC: 5 } as const;
