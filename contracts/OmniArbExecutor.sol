// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "./interfaces/IAaveV3.sol";
import "./interfaces/IB3.sol";
import "./interfaces/IUniV2.sol";
import "./interfaces/IUniV3.sol";
import "./interfaces/ICurve.sol";
import "./modules/SwapHandler.sol";

/**
 * @title OmniArbExecutor
 * @notice Refactored core executor for flashloan-based arbitrage with multi-DEX routing
 * @dev Supports Aave V3 and Balancer V3 flashloans with RAW_ADDRESSES and REGISTRY_ENUMS encoding
 */
contract OmniArbExecutor is Ownable, SwapHandler, IAaveFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;

    // ============================================
    // ENUMS
    // ============================================

    /**
     * @notice Flash loan source providers
     */
    enum FlashSource {
        AaveV3,       // 0: Aave V3 flashLoanSimple
        BalancerV3    // 1: Balancer V3 unlock pattern
    }

    /**
     * @notice Route encoding format
     */
    enum RouteEncoding {
        RAW_ADDRESSES,    // 0: Explicit router + token addresses
        REGISTRY_ENUMS    // 1: DEX + Token enums resolved on-chain
    }

    /**
     * @notice DEX identifiers for registry-based routing
     */
    enum Dex {
        UniV2,        // 0: UniswapV2-style (Quickswap, Sushiswap, etc.)
        UniV3,        // 1: Uniswap V3
        Curve,        // 2: Curve pools
        Balancer,     // 3: Balancer
        Dodo,         // 4: Dodo
        Unknown       // 5: Unknown/Other DEX
    }

    /**
     * @notice Token identifiers for registry-based routing
     */
    enum TokenId {
        WNATIVE,      // 0: Wrapped native token (WETH, WMATIC, etc.)
        USDC,         // 1: USD Coin
        USDT,         // 2: Tether USD
        DAI,          // 3: Dai Stablecoin
        WETH,         // 4: Wrapped Ether
        WBTC          // 5: Wrapped Bitcoin
    }

    /**
     * @notice Token type classification
     */
    enum TokenType {
        CANONICAL,    // 0: Native to the chain
        BRIDGED,      // 1: Bridged version (e.g., USDC.e)
        WRAPPED       // 2: Wrapped native (WETH, WMATIC, etc.)
    }

    // ============================================
    // STATE VARIABLES
    // ============================================

    IVaultV3 public immutable BALANCER_VAULT;
    IAavePoolV3 public immutable AAVE_POOL;
    
    uint256 public swapDeadline = 180; // Default 3 minutes

    // Registry mappings for REGISTRY_ENUMS encoding
    // Note: chainId uses actual chain IDs (e.g., 137 for Polygon, 1 for Ethereum)
    // not Chain enum ordinal values. The Chain enum is for reference only.
    // dexRouter[chainId][dexId] = router address (or pool address for Curve)
    mapping(uint256 => mapping(uint8 => address)) public dexRouter;
    
    // tokenRegistry[chainId][tokenId][tokenType] = token address
    mapping(uint256 => mapping(uint8 => mapping(uint8 => address))) public tokenRegistry;

    // ============================================
    // EVENTS
    // ============================================

    event RouteExecuted(
        address indexed loanToken,
        uint256 loanAmount,
        uint256 finalAmount,
        uint256 profit
    );

    event DexRouterSet(uint256 indexed chainId, uint8 indexed dexId, address router);
    event TokenSet(uint256 indexed chainId, uint8 indexed tokenId, uint8 indexed tokenType, address token);

    // ============================================
    // CONSTRUCTOR
    // ============================================

    constructor(address _balancer, address _aave) Ownable(msg.sender) {
        require(_balancer != address(0) && _aave != address(0), "Invalid addresses");
        BALANCER_VAULT = IVaultV3(_balancer);
        AAVE_POOL = IAavePoolV3(_aave);
    }

    // ============================================
    // CONFIGURATION
    // ============================================

    /**
     * @notice Set swap deadline for time-sensitive swaps
     */
    function setSwapDeadline(uint256 _seconds) external onlyOwner {
        require(_seconds >= 60 && _seconds <= 600, "Deadline must be 60-600 seconds");
        swapDeadline = _seconds;
    }

    /**
     * @notice Register a DEX router for a specific chain
     */
    function setDexRouter(uint256 chainId, uint8 dexId, address router) external onlyOwner {
        require(router != address(0), "Invalid router");
        dexRouter[chainId][dexId] = router;
        emit DexRouterSet(chainId, dexId, router);
    }

    /**
     * @notice Register a token for a specific chain, token ID, and token type
     */
    function setToken(uint256 chainId, uint8 tokenId, uint8 tokenType, address token) external onlyOwner {
        require(token != address(0), "Invalid token");
        tokenRegistry[chainId][tokenId][tokenType] = token;
        emit TokenSet(chainId, tokenId, tokenType, token);
    }

    /**
     * @notice Batch register multiple DEX routers
     */
    function batchSetDexRouters(
        uint256[] calldata chainIds,
        uint8[] calldata dexIds,
        address[] calldata routers
    ) external onlyOwner {
        require(chainIds.length == dexIds.length && dexIds.length == routers.length, "Length mismatch");
        for (uint i = 0; i < chainIds.length; i++) {
            require(routers[i] != address(0), "Invalid router");
            dexRouter[chainIds[i]][dexIds[i]] = routers[i];
            emit DexRouterSet(chainIds[i], dexIds[i], routers[i]);
        }
    }

    /**
     * @notice Batch register multiple tokens
     */
    function batchSetTokens(
        uint256[] calldata chainIds,
        uint8[] calldata tokenIds,
        uint8[] calldata tokenTypes,
        address[] calldata tokens
    ) external onlyOwner {
        require(
            chainIds.length == tokenIds.length && 
            tokenIds.length == tokenTypes.length && 
            tokenTypes.length == tokens.length,
            "Length mismatch"
        );
        for (uint i = 0; i < chainIds.length; i++) {
            require(tokens[i] != address(0), "Invalid token");
            tokenRegistry[chainIds[i]][tokenIds[i]][tokenTypes[i]] = tokens[i];
            emit TokenSet(chainIds[i], tokenIds[i], tokenTypes[i], tokens[i]);
        }
    }

    // ============================================
    // EXECUTION TRIGGER
    // ============================================

    /**
     * @notice Execute arbitrage with flashloan
     * @param flashSource Flash loan source (AaveV3=0, BalancerV3=1)
     * @param loanToken Token to borrow
     * @param loanAmount Amount to borrow
     * @param routeData Encoded route (RAW_ADDRESSES or REGISTRY_ENUMS)
     */
    function execute(
        FlashSource flashSource,
        address loanToken,
        uint256 loanAmount,
        bytes calldata routeData
    ) external onlyOwner {
        if (flashSource == FlashSource.AaveV3) {
            // Aave V3: Standard flashloan
            AAVE_POOL.flashLoanSimple(address(this), loanToken, loanAmount, routeData, 0);
        } else if (flashSource == FlashSource.BalancerV3) {
            // Balancer V3: Unlock pattern
            bytes memory callbackData = abi.encode(loanToken, loanAmount, routeData);
            BALANCER_VAULT.unlock(abi.encodeWithSelector(this.onBalancerUnlock.selector, callbackData));
        } else {
            revert("Invalid flash source");
        }
    }

    // ============================================
    // FLASHLOAN CALLBACKS
    // ============================================

    /**
     * @notice Balancer V3 unlock callback
     */
    function onBalancerUnlock(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(BALANCER_VAULT), "Auth");
        (address token, uint256 amount, bytes memory routeData) = abi.decode(data, (address, uint256, bytes));

        // Take debt (V3 transient accounting)
        BALANCER_VAULT.sendTo(IERC20(token), address(this), amount);

        // Execute route
        uint256 finalAmount = _runRoute(token, amount, routeData);

        // Ensure route was at least break-even before repaying Balancer
        require(finalAmount >= amount, "Insufficient return");

        // Repay debt
        IERC20(token).safeTransfer(address(BALANCER_VAULT), amount);
        BALANCER_VAULT.settle(IERC20(token), amount);

        emit RouteExecuted(token, amount, finalAmount, finalAmount - amount);
        
        return "";
    }

    /**
     * @notice Aave V3 flashloan callback
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address /* initiator */,
        bytes calldata routeData
    ) external override returns (bool) {
        require(msg.sender == address(AAVE_POOL), "Auth");
        
        uint256 finalAmount = _runRoute(asset, amount, routeData);

        uint256 owed = amount + premium;
        require(finalAmount >= owed, "Insufficient return");
        
        IERC20(asset).forceApprove(address(AAVE_POOL), owed);

        emit RouteExecuted(asset, amount, finalAmount, finalAmount - owed);
        
        return true;
    }

    // ============================================
    // ROUTE EXECUTION ENGINE
    // ============================================

    /**
     * @notice Execute multi-hop swap route
     * @param inputToken Starting token (loan token)
     * @param inputAmount Starting amount (loan amount)
     * @param routeData Encoded route data
     * @return finalAmount Final amount after all hops
     */
    function _runRoute(
        address inputToken,
        uint256 inputAmount,
        bytes memory routeData
    ) internal returns (uint256 finalAmount) {
        
        // Decode encoding type using ABI decoding (first tuple element)
        RouteEncoding encoding = abi.decode(routeData, (RouteEncoding));

        if (encoding == RouteEncoding.RAW_ADDRESSES) {
            return _runRouteRaw(inputToken, inputAmount, routeData);
        } else if (encoding == RouteEncoding.REGISTRY_ENUMS) {
            return _runRouteRegistry(inputToken, inputAmount, routeData);
        } else {
            revert("Invalid encoding");
        }
    }

    /**
     * @notice Execute route with RAW_ADDRESSES encoding
     */
    function _runRouteRaw(
        address inputToken,
        uint256 inputAmount,
        bytes memory routeData
    ) internal returns (uint256) {
        
        (
            RouteEncoding enc,
            uint8[] memory protocols,
            address[] memory routersOrPools,
            address[] memory tokenOutPath,
            bytes[] memory extra
        ) = abi.decode(routeData, (RouteEncoding, uint8[], address[], address[], bytes[]));

        // Validate lengths
        require(protocols.length == routersOrPools.length, "len mismatch");
        require(protocols.length == tokenOutPath.length, "len mismatch");
        require(protocols.length == extra.length, "len mismatch");
        require(protocols.length > 0 && protocols.length <= 5, "Invalid route length");

        uint256 currentAmount = inputAmount;
        address currentToken = inputToken;

        for (uint i = 0; i < protocols.length; i++) {
            require(routersOrPools[i] != address(0), "Invalid router");
            require(tokenOutPath[i] != address(0), "Invalid token");
            require(currentAmount > 0, "Zero balance");

            currentAmount = _executeSwap(
                protocols[i],
                routersOrPools[i],
                currentToken,
                tokenOutPath[i],
                currentAmount,
                extra[i]
            );

            require(currentAmount > 0, "Swap returned zero");
            currentToken = tokenOutPath[i];
        }

        return currentAmount;
    }

    /**
     * @notice Execute route with REGISTRY_ENUMS encoding
     */
    function _runRouteRegistry(
        address inputToken,
        uint256 inputAmount,
        bytes memory routeData
    ) internal returns (uint256) {
        
        (
            RouteEncoding enc,
            uint8[] memory protocols,
            uint8[] memory dexIds,
            uint8[] memory tokenOutIds,
            uint8[] memory tokenOutTypes,
            bytes[] memory extra
        ) = abi.decode(routeData, (RouteEncoding, uint8[], uint8[], uint8[], uint8[], bytes[]));

        // Validate lengths
        require(protocols.length == dexIds.length, "len mismatch");
        require(protocols.length == tokenOutIds.length, "len mismatch");
        require(protocols.length == tokenOutTypes.length, "len mismatch");
        require(protocols.length == extra.length, "len mismatch");
        require(protocols.length > 0 && protocols.length <= 5, "Invalid route length");

        uint256 chainId = block.chainid;
        uint256 currentAmount = inputAmount;
        address currentToken = inputToken;

        for (uint i = 0; i < protocols.length; i++) {
            // Resolve router from registry
            address routerOrPool = dexRouter[chainId][dexIds[i]];
            require(routerOrPool != address(0), "Router not registered");

            // Resolve tokenOut from registry
            address tokenOut = tokenRegistry[chainId][tokenOutIds[i]][tokenOutTypes[i]];
            require(tokenOut != address(0), "Token not registered");

            require(currentAmount > 0, "Zero balance");

            currentAmount = _executeSwap(
                protocols[i],
                routerOrPool,
                currentToken,
                tokenOut,
                currentAmount,
                extra[i]
            );

            require(currentAmount > 0, "Swap returned zero");
            currentToken = tokenOut;
        }

        return currentAmount;
    }

    // ============================================
    // EMERGENCY FUNCTIONS
    // ============================================

    /**
     * @notice Withdraw tokens from contract (emergency)
     */
    function withdraw(address token) external onlyOwner {
        IERC20(token).safeTransfer(msg.sender, IERC20(token).balanceOf(address(this)));
    }

    /**
     * @notice Withdraw native ETH/MATIC (emergency)
     */
    function withdrawNative() external onlyOwner {
        (bool success, ) = payable(msg.sender).call{value: address(this).balance}("");
        require(success, "Native transfer failed");
    }

    /**
     * @notice Allow the contract to receive native ETH/MATIC
     * @dev This is intended for handling native refunds or unwrapped WETH from
     *      external protocols used in arbitrage flows. Any ETH accumulated here
     *      can be recovered by the owner via {withdrawNative}.
     */
    receive() external payable {}
}
