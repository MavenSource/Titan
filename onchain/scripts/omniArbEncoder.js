const { ethers } = require("ethers");

/**
 * OmniArb Matrix A-J Encoder Utility
 * 
 * This utility provides helper functions to encode payloads for the OmniArb Matrix A-J system.
 */

// Chain enum to chain ID mapping
const CHAIN_ENUM_MAP = {
  'A': { name: 'Ethereum', chainId: 1 },
  'B': { name: 'Polygon', chainId: 137 },
  'C': { name: 'Base', chainId: 8453 },
  'D': { name: 'Arbitrum', chainId: 42161 },
  'E': { name: 'Optimism', chainId: 10 },
  'F': { name: 'Avalanche', chainId: 43114 },
  'G': { name: 'Fantom', chainId: 250 },
  'H': { name: 'Gnosis', chainId: 100 },
  'I': { name: 'Celo', chainId: 42220 },
  'J': { name: 'Linea', chainId: 59144 }
};

// Token rank ranges per chain
const CHAIN_RANK_RANGES = {
  'A': { start: 1000, end: 1999 },
  'B': { start: 2000, end: 2999 },
  'C': { start: 3000, end: 3999 },
  'D': { start: 4000, end: 4999 },
  'E': { start: 5000, end: 5999 },
  'F': { start: 6000, end: 6999 },
  'G': { start: 7000, end: 7999 },
  'H': { start: 8000, end: 8999 },
  'I': { start: 9000, end: 9999 },
  'J': { start: 10000, end: 10999 }
};

/**
 * Convert a string to bytes1
 * @param {string} str - Single character string
 * @returns {string} Bytes1 representation
 */
function toBytes1(str) {
  if (str.length !== 1) {
    throw new Error("Input must be a single character");
  }
  return ethers.encodeBytes32String(str).slice(0, 4);
}

/**
 * Get chain enum letter from chain ID
 * @param {number} chainId - Chain ID
 * @returns {string} Chain enum letter (A-J)
 */
function getChainEnum(chainId) {
  for (const [letter, info] of Object.entries(CHAIN_ENUM_MAP)) {
    if (info.chainId === chainId) {
      return letter;
    }
  }
  throw new Error(`Unknown chain ID: ${chainId}`);
}

/**
 * Get chain ID from chain enum letter
 * @param {string} chainEnum - Chain enum letter (A-J)
 * @returns {number} Chain ID
 */
function getChainId(chainEnum) {
  const info = CHAIN_ENUM_MAP[chainEnum.toUpperCase()];
  if (!info) {
    throw new Error(`Unknown chain enum: ${chainEnum}`);
  }
  return info.chainId;
}

/**
 * Get chain name from chain enum letter
 * @param {string} chainEnum - Chain enum letter (A-J)
 * @returns {string} Chain name
 */
function getChainName(chainEnum) {
  const info = CHAIN_ENUM_MAP[chainEnum.toUpperCase()];
  if (!info) {
    throw new Error(`Unknown chain enum: ${chainEnum}`);
  }
  return info.name;
}

/**
 * Validate token rank is within the correct range for the chain
 * @param {string} chainEnum - Chain enum letter (A-J)
 * @param {number} tokenRank - Token rank
 * @returns {boolean} True if valid
 */
function validateTokenRank(chainEnum, tokenRank) {
  const range = CHAIN_RANK_RANGES[chainEnum.toUpperCase()];
  if (!range) {
    throw new Error(`Unknown chain enum: ${chainEnum}`);
  }
  return tokenRank >= range.start && tokenRank <= range.end;
}

/**
 * Calculate token rank from chain and index
 * @param {string} chainEnum - Chain enum letter (A-J)
 * @param {number} index - Token index in STATIC_ORDER (0-based)
 * @returns {number} Token rank
 */
function calculateTokenRank(chainEnum, index) {
  const range = CHAIN_RANK_RANGES[chainEnum.toUpperCase()];
  if (!range) {
    throw new Error(`Unknown chain enum: ${chainEnum}`);
  }
  return range.start + index;
}

/**
 * Encode an OmniArb payload
 * @param {Object} params - Payload parameters
 * @param {string} params.chainEnum - Chain enum letter (A-J)
 * @param {number} params.tokenRank - Token rank
 * @param {string|bigint} params.amount - Token amount (as string or bigint)
 * @param {string} params.routeParams - Encoded routing parameters (hex string)
 * @param {number} params.minProfitBps - Minimum profit in basis points (0-10000)
 * @param {number} params.expiry - Unix timestamp for expiry
 * @param {string} params.receiver - Receiver address
 * @param {string} params.routeRegistryHash - Route registry hash (32 bytes hex)
 * @param {number|bigint} params.nonce - Unique nonce
 * @returns {string} Encoded payload (hex string)
 */
function encodePayload({
  chainEnum,
  tokenRank,
  amount,
  routeParams = "0x",
  minProfitBps,
  expiry,
  receiver,
  routeRegistryHash = ethers.ZeroHash,
  nonce
}) {
  // Validate inputs
  if (!chainEnum || chainEnum.length !== 1) {
    throw new Error("chainEnum must be a single letter (A-J)");
  }
  
  chainEnum = chainEnum.toUpperCase();
  if (!CHAIN_ENUM_MAP[chainEnum]) {
    throw new Error(`Invalid chain enum: ${chainEnum}`);
  }
  
  if (!validateTokenRank(chainEnum, tokenRank)) {
    const range = CHAIN_RANK_RANGES[chainEnum];
    throw new Error(
      `Token rank ${tokenRank} is outside valid range ${range.start}-${range.end} for chain ${chainEnum}`
    );
  }
  
  if (minProfitBps < 0 || minProfitBps > 10000) {
    throw new Error("minProfitBps must be between 0 and 10000");
  }
  
  // Validate and normalize address to checksummed format
  try {
    receiver = ethers.getAddress(receiver.toLowerCase());
  } catch (e) {
    throw new Error("Invalid receiver address");
  }
  
  // Convert amount to BigInt if it's a string
  if (typeof amount === 'string') {
    amount = BigInt(amount);
  }
  
  // Encode the payload
  const encoded = ethers.AbiCoder.defaultAbiCoder().encode(
    ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
    [
      toBytes1(chainEnum),
      tokenRank,
      amount,
      routeParams,
      minProfitBps,
      expiry,
      receiver,
      routeRegistryHash,
      nonce
    ]
  );
  
  return encoded;
}

/**
 * Decode an OmniArb payload
 * @param {string} payload - Encoded payload (hex string)
 * @returns {Object} Decoded payload
 */
function decodePayload(payload) {
  const decoded = ethers.AbiCoder.defaultAbiCoder().decode(
    ["bytes1", "uint16", "uint256", "bytes", "uint16", "uint64", "address", "bytes32", "uint256"],
    payload
  );
  
  // Convert bytes1 back to character
  // The decoded bytes1 is a hex string like "0x4200000000..."
  // Extract the first byte and convert to ASCII character
  const chainEnumBytes = decoded[0];
  const firstByte = parseInt(chainEnumBytes.slice(0, 4), 16);
  const chainEnum = String.fromCharCode(firstByte);
  
  return {
    chainEnum: chainEnum,
    chainName: CHAIN_ENUM_MAP[chainEnum]?.name || 'Unknown',
    chainId: CHAIN_ENUM_MAP[chainEnum]?.chainId || 0,
    tokenRank: Number(decoded[1]),
    amount: decoded[2].toString(),
    routeParams: decoded[3],
    minProfitBps: Number(decoded[4]),
    expiry: Number(decoded[5]),
    receiver: decoded[6],
    routeRegistryHash: decoded[7],
    nonce: decoded[8].toString()
  };
}

/**
 * Create a test payload with reasonable defaults
 * @param {Object} params - Partial payload parameters
 * @returns {string} Encoded test payload
 */
function createTestPayload(params = {}) {
  const defaults = {
    chainEnum: 'B', // Polygon
    tokenRank: 2001, // WETH on Polygon
    amount: ethers.parseEther("1"),
    routeParams: "0x",
    minProfitBps: 100, // 1%
    expiry: Math.floor(Date.now() / 1000) + 3600, // 1 hour from now
    receiver: ethers.ZeroAddress,
    routeRegistryHash: ethers.ZeroHash,
    nonce: Date.now()
  };
  
  return encodePayload({ ...defaults, ...params });
}

// Export functions
module.exports = {
  toBytes1,
  getChainEnum,
  getChainId,
  getChainName,
  validateTokenRank,
  calculateTokenRank,
  encodePayload,
  decodePayload,
  createTestPayload,
  CHAIN_ENUM_MAP,
  CHAIN_RANK_RANGES
};

// Example usage when run directly
if (require.main === module) {
  console.log("=== OmniArb Matrix A-J Encoder Utility ===\n");
  
  // Example 1: Encode a payload
  console.log("Example 1: Encoding a payload for Polygon");
  const payload = encodePayload({
    chainEnum: 'B',
    tokenRank: 2001,
    amount: ethers.parseEther("1"),
    routeParams: "0x",
    minProfitBps: 100,
    expiry: Math.floor(Date.now() / 1000) + 3600,
    receiver: "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb0", // Example receiver address
    routeRegistryHash: ethers.ZeroHash,
    nonce: 1
  });
  console.log("Encoded payload:", payload.slice(0, 66) + "...\n");
  
  // Example 2: Decode the payload
  console.log("Example 2: Decoding the payload");
  const decoded = decodePayload(payload);
  console.log("Decoded:", JSON.stringify(decoded, null, 2));
  console.log();
  
  // Example 3: Chain enum mapping
  console.log("Example 3: Chain enum mappings");
  for (const [letter, info] of Object.entries(CHAIN_ENUM_MAP)) {
    console.log(`  ${letter} → ${info.name} (Chain ID: ${info.chainId})`);
  }
  console.log();
  
  // Example 4: Token rank calculation
  console.log("Example 4: Token rank calculation");
  console.log("  Ethereum token at index 0:", calculateTokenRank('A', 0)); // 1000
  console.log("  Polygon token at index 1:", calculateTokenRank('B', 1));  // 2001
  console.log("  Arbitrum token at index 5:", calculateTokenRank('D', 5)); // 4005
  console.log();
  
  // Example 5: Validation
  console.log("Example 5: Token rank validation");
  console.log("  Rank 2001 valid for Polygon?", validateTokenRank('B', 2001)); // true
  console.log("  Rank 1500 valid for Polygon?", validateTokenRank('B', 1500)); // false
}
