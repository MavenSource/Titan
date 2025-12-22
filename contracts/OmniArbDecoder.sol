// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title OmniArbDecoder
 * @notice Decoder for OmniArb Matrix A-J design
 * @dev Uses bytes1 chainEnum (A-J) and uint16 tokenRank for chain/token selection
 */
contract OmniArbDecoder is Ownable {
    
    // ========================================================================
    // STRUCTS
    // ========================================================================
    
    /**
     * @notice Decoded payload structure for OmniArb execution
     * @param chainEnum ASCII letter 'A'..'J' representing the chain
     * @param tokenRank Deterministic rank in chain-specific range
     * @param amount Token amount for the operation
     * @param routeParams Encoded routing parameters
     * @param minProfitBps Minimum profit in basis points
     * @param expiry Timestamp after which payload is invalid
     * @param receiver Address to receive output tokens
     * @param routeRegistryHash Hash of the route registry for verification
     * @param nonce Unique identifier to prevent replay attacks
     */
    struct DecodedPayload {
        bytes1 chainEnum;
        uint16 tokenRank;
        uint256 amount;
        bytes routeParams;
        uint16 minProfitBps;
        uint64 expiry;
        address receiver;
        bytes32 routeRegistryHash;
        uint256 nonce;
    }
    
    // ========================================================================
    // STATE VARIABLES
    // ========================================================================
    
    /// @notice Mapping from chain enum (A-J) to chain ID
    mapping(bytes1 => uint256) public enumToChainId;
    
    /// @notice Mapping from token rank to token address
    mapping(uint16 => address) public rankToToken;
    
    /// @notice Mapping from bridged USDC to canonical USDC per chain
    mapping(uint256 => mapping(address => address)) public bridgedToCanonical;
    
    /// @notice Used nonces to prevent replay attacks
    mapping(uint256 => bool) public usedNonces;
    
    /// @notice Current route registry hash for verification
    bytes32 public routeRegistryHash;
    
    // ========================================================================
    // EVENTS
    // ========================================================================
    
    event ChainEnumConfigured(bytes1 indexed chainEnum, uint256 chainId);
    event TokenRankConfigured(uint16 indexed tokenRank, address tokenAddress);
    event BridgedUSDCConfigured(uint256 indexed chainId, address bridged, address canonical);
    event RouteRegistryHashUpdated(bytes32 newHash);
    event PayloadDecoded(uint256 indexed nonce, bytes1 chainEnum, uint16 tokenRank);
    
    // ========================================================================
    // ERRORS
    // ========================================================================
    
    error InvalidChainEnum(bytes1 chainEnum);
    error ChainMismatch(uint256 expected, uint256 actual);
    error InvalidTokenRank(uint16 tokenRank);
    error PayloadExpired(uint64 expiry, uint64 currentTime);
    error NonceAlreadyUsed(uint256 nonce);
    error InvalidRouteRegistryHash(bytes32 expected, bytes32 actual);
    error InvalidMinProfitBps(uint16 minProfitBps);
    
    // ========================================================================
    // CONSTRUCTOR
    // ========================================================================
    
    constructor() Ownable(msg.sender) {
        _initializeChainEnums();
    }
    
    // ========================================================================
    // INITIALIZATION
    // ========================================================================
    
    /**
     * @notice Initialize chain enum to chain ID mappings (A-J)
     * @dev Fixed alphabetical ordering (append-only; never reassign letters)
     */
    function _initializeChainEnums() internal {
        // A → Ethereum (1)
        enumToChainId[bytes1("A")] = 1;
        emit ChainEnumConfigured(bytes1("A"), 1);
        
        // B → Polygon (137)
        enumToChainId[bytes1("B")] = 137;
        emit ChainEnumConfigured(bytes1("B"), 137);
        
        // C → Base (8453)
        enumToChainId[bytes1("C")] = 8453;
        emit ChainEnumConfigured(bytes1("C"), 8453);
        
        // D → Arbitrum (42161)
        enumToChainId[bytes1("D")] = 42161;
        emit ChainEnumConfigured(bytes1("D"), 42161);
        
        // E → Optimism (10)
        enumToChainId[bytes1("E")] = 10;
        emit ChainEnumConfigured(bytes1("E"), 10);
        
        // F → Avalanche (43114)
        enumToChainId[bytes1("F")] = 43114;
        emit ChainEnumConfigured(bytes1("F"), 43114);
        
        // G → Fantom (250)
        enumToChainId[bytes1("G")] = 250;
        emit ChainEnumConfigured(bytes1("G"), 250);
        
        // H → Gnosis (100)
        enumToChainId[bytes1("H")] = 100;
        emit ChainEnumConfigured(bytes1("H"), 100);
        
        // I → Celo (42220)
        enumToChainId[bytes1("I")] = 42220;
        emit ChainEnumConfigured(bytes1("I"), 42220);
        
        // J → Linea (59144)
        enumToChainId[bytes1("J")] = 59144;
        emit ChainEnumConfigured(bytes1("J"), 59144);
    }
    
    // ========================================================================
    // ADMIN FUNCTIONS - TOKEN CONFIGURATION
    // ========================================================================
    
    /**
     * @notice Configure multiple token ranks at once
     * @param ranks Array of token ranks
     * @param tokens Array of token addresses
     */
    function configureTokenRanks(uint16[] calldata ranks, address[] calldata tokens) external onlyOwner {
        require(ranks.length == tokens.length, "Length mismatch");
        for (uint256 i = 0; i < ranks.length; i++) {
            rankToToken[ranks[i]] = tokens[i];
            emit TokenRankConfigured(ranks[i], tokens[i]);
        }
    }
    
    /**
     * @notice Configure a single token rank
     * @param rank Token rank
     * @param token Token address
     */
    function configureTokenRank(uint16 rank, address token) external onlyOwner {
        rankToToken[rank] = token;
        emit TokenRankConfigured(rank, token);
    }
    
    /**
     * @notice Configure bridged USDC to canonical USDC mapping
     * @param chainId Chain ID where the bridged USDC exists
     * @param bridged Bridged USDC address (e.g., USDC.e)
     * @param canonical Canonical USDC address
     */
    function configureBridgedUSDC(uint256 chainId, address bridged, address canonical) external onlyOwner {
        bridgedToCanonical[chainId][bridged] = canonical;
        emit BridgedUSDCConfigured(chainId, bridged, canonical);
    }
    
    /**
     * @notice Update the route registry hash
     * @param newHash New route registry hash
     */
    function updateRouteRegistryHash(bytes32 newHash) external onlyOwner {
        routeRegistryHash = newHash;
        emit RouteRegistryHashUpdated(newHash);
    }
    
    // ========================================================================
    // DECODING FUNCTIONS
    // ========================================================================
    
    /**
     * @notice Decode and validate a payload
     * @param payload Encoded payload bytes
     * @return decoded Decoded payload structure
     */
    function decodePayload(bytes calldata payload) external returns (DecodedPayload memory decoded) {
        // Decode the payload tuple
        (
            decoded.chainEnum,
            decoded.tokenRank,
            decoded.amount,
            decoded.routeParams,
            decoded.minProfitBps,
            decoded.expiry,
            decoded.receiver,
            decoded.routeRegistryHash,
            decoded.nonce
        ) = abi.decode(payload, (bytes1, uint16, uint256, bytes, uint16, uint64, address, bytes32, uint256));
        
        // Validate the payload
        _validatePayload(decoded);
        
        // Mark nonce as used
        usedNonces[decoded.nonce] = true;
        
        emit PayloadDecoded(decoded.nonce, decoded.chainEnum, decoded.tokenRank);
        
        return decoded;
    }
    
    /**
     * @notice Validate a decoded payload
     * @param payload Decoded payload to validate
     */
    function _validatePayload(DecodedPayload memory payload) internal view {
        // Validate chain enum matches current chain
        uint256 expectedChainId = enumToChainId[payload.chainEnum];
        if (expectedChainId == 0) {
            revert InvalidChainEnum(payload.chainEnum);
        }
        if (expectedChainId != block.chainid) {
            revert ChainMismatch(expectedChainId, block.chainid);
        }
        
        // Validate token rank is configured
        if (rankToToken[payload.tokenRank] == address(0)) {
            revert InvalidTokenRank(payload.tokenRank);
        }
        
        // Validate expiry
        if (uint64(block.timestamp) > payload.expiry) {
            revert PayloadExpired(payload.expiry, uint64(block.timestamp));
        }
        
        // Validate nonce hasn't been used
        if (usedNonces[payload.nonce]) {
            revert NonceAlreadyUsed(payload.nonce);
        }
        
        // Validate route registry hash
        if (routeRegistryHash != bytes32(0) && payload.routeRegistryHash != routeRegistryHash) {
            revert InvalidRouteRegistryHash(routeRegistryHash, payload.routeRegistryHash);
        }
        
        // Validate minProfitBps is reasonable (max 10000 = 100%)
        if (payload.minProfitBps > 10000) {
            revert InvalidMinProfitBps(payload.minProfitBps);
        }
    }
    
    /**
     * @notice Resolve token address from rank, normalizing bridged USDC to canonical
     * @param tokenRank Token rank to resolve
     * @return token Resolved token address (canonical if USDC variant)
     */
    function resolveToken(uint16 tokenRank) external view returns (address token) {
        token = rankToToken[tokenRank];
        if (token == address(0)) {
            revert InvalidTokenRank(tokenRank);
        }
        
        // Check if this is a bridged USDC that should be normalized to canonical
        address canonical = bridgedToCanonical[block.chainid][token];
        if (canonical != address(0)) {
            return canonical;
        }
        
        return token;
    }
    
    /**
     * @notice Get the chain ID for a given chain enum
     * @param chainEnum Chain enum (A-J)
     * @return chainId Chain ID
     */
    function getChainId(bytes1 chainEnum) external view returns (uint256 chainId) {
        chainId = enumToChainId[chainEnum];
        if (chainId == 0) {
            revert InvalidChainEnum(chainEnum);
        }
        return chainId;
    }
    
    /**
     * @notice Check if a chain enum is valid for the current chain
     * @param chainEnum Chain enum to check
     * @return valid True if the chain enum matches the current chain
     */
    function isValidChainEnum(bytes1 chainEnum) external view returns (bool valid) {
        uint256 expectedChainId = enumToChainId[chainEnum];
        return expectedChainId != 0 && expectedChainId == block.chainid;
    }
    
    /**
     * @notice Get token address for a rank without normalization
     * @param tokenRank Token rank
     * @return token Token address
     */
    function getTokenByRank(uint16 tokenRank) external view returns (address token) {
        token = rankToToken[tokenRank];
        if (token == address(0)) {
            revert InvalidTokenRank(tokenRank);
        }
        return token;
    }
}
