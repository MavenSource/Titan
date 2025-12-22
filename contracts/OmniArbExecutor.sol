// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "./modules/SwapHandler.sol";
import "./interfaces/IAaveV3.sol";
import "./interfaces/IB3.sol";

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

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

    enum Dex { UniV2, UniV3, Curve, Balancer, Dodo, Unknown } // 0..5
    enum TokenType { CANONICAL, BRIDGED, WRAPPED }            // 0..2
    enum TokenId { WNATIVE, USDC, USDT, DAI, WETH, WBTC }     // 0..5

    // ========= CORE DEPENDENCIES =========

    IAavePoolV3 public immutable AAVE_POOL;
    IBalancerVaultV3 public immutable BALANCER_VAULT;

    // dexRouter[chainId][dex] = router address
    mapping(uint256 => mapping(uint8 => address)) public dexRouter;

    // tokenRegistry[chainId][tokenId][tokenType] = token address
    mapping(uint256 => mapping(uint8 => mapping(uint8 => address))) public tokenRegistry;

    // ========= EVENTS =========

    event DexRouterSet(uint256 indexed chainId, Dex indexed dex, address router);
    event TokenSet(uint256 indexed chainId, TokenId indexed tokenId, TokenType indexed tokenType, address token);
    event Executed(FlashSource indexed source, address indexed loanToken, uint256 loanAmount, uint256 finalBalance, int256 pnl);

    constructor(address aavePoolV3, address balancerVaultV3) Ownable(msg.sender) {
        require(aavePoolV3 != address(0) && balancerVaultV3 != address(0), "bad ctor");
        AAVE_POOL = IAavePoolV3(aavePoolV3);
        BALANCER_VAULT = IBalancerVaultV3(balancerVaultV3);
    }

    // ========= ADMIN: SET REGISTRY =========

    function setDexRouter(uint256 chainId, Dex dex, address router) external onlyOwner {
        dexRouter[chainId][uint8(dex)] = router;
        emit DexRouterSet(chainId, dex, router);
    }

    function setToken(uint256 chainId, TokenId tokenId, TokenType tokenType, address token) external onlyOwner {
        tokenRegistry[chainId][uint8(tokenId)][uint8(tokenType)] = token;
        emit TokenSet(chainId, tokenId, tokenType, token);
    }

    function resolveDex(uint256 chainId, Dex dex) public view returns (address router) {
        router = dexRouter[chainId][uint8(dex)];
        require(router != address(0), "dex not set");
    }

    function resolveToken(uint256 chainId, TokenId tokenId, TokenType preferred) public view returns (address token) {
        token = tokenRegistry[chainId][uint8(tokenId)][uint8(preferred)];
        if (token != address(0)) return token;

        // fallback canonical <-> bridged
        if (preferred == TokenType.CANONICAL) {
            token = tokenRegistry[chainId][uint8(tokenId)][uint8(TokenType.BRIDGED)];
            if (token != address(0)) return token;
        } else if (preferred == TokenType.BRIDGED) {
            token = tokenRegistry[chainId][uint8(tokenId)][uint8(TokenType.CANONICAL)];
            if (token != address(0)) return token;
        }

        // WNATIVE fallback to WRAPPED
        if (tokenId == TokenId.WNATIVE) {
            token = tokenRegistry[chainId][uint8(tokenId)][uint8(TokenType.WRAPPED)];
            if (token != address(0)) return token;
        }

        revert("token not set");
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

        if (source == FlashSource.BalancerV3) {
            bytes memory payload = abi.encode(loanToken, loanAmount, routeData);
            bytes memory callData = abi.encodeWithSelector(this.onBalancerUnlock.selector, payload);
            BALANCER_VAULT.unlock(callData);
            return;
        }

        revert("bad source");
    }

    // ========= AAVE CALLBACK =========

    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(AAVE_POOL), "Aave: auth");

        uint256 startBal = IERC20(asset).balanceOf(address(this));
        _runRoute(asset, amount, params);

        uint256 owed = amount + premium;
        require(finalAmount >= owed, "Insufficient return");
        
        IERC20(asset).forceApprove(address(AAVE_POOL), owed);

        uint256 endBal = IERC20(asset).balanceOf(address(this));
        emit Executed(FlashSource.AaveV3, asset, amount, endBal, int256(endBal) - int256(startBal));
        return true;
    }

    // ========= BALANCER CALLBACK =========

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

        (address loanToken, uint256 loanAmount, bytes memory routeData) =
            abi.decode(data, (address, uint256, bytes));

        uint256 startBal = IERC20(loanToken).balanceOf(address(this));

        BALANCER_VAULT.sendTo(IERC20(loanToken), address(this), loanAmount);

        _runRoute(loanToken, loanAmount, routeData);

        IERC20(loanToken).forceApprove(address(BALANCER_VAULT), loanAmount);
        BALANCER_VAULT.settle(IERC20(loanToken), loanAmount);

        uint256 endBal = IERC20(loanToken).balanceOf(address(this));
        emit Executed(FlashSource.BalancerV3, loanToken, loanAmount, endBal, int256(endBal) - int256(startBal));

        return bytes("");
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
        (RouteEncoding enc) = abi.decode(routeData, (RouteEncoding));

        address currentToken = inputToken;
        uint256 currentAmount = inputAmount;

        if (enc == RouteEncoding.RAW_ADDRESSES) {
            (, uint8[] memory protocols, address[] memory routers, address[] memory tokenOutPath, bytes[] memory extra) =
                abi.decode(routeData, (RouteEncoding, uint8[], address[], address[], bytes[]));

            require(protocols.length == routers.length && routers.length == tokenOutPath.length && tokenOutPath.length == extra.length, "route: len mismatch");

            for (uint256 i = 0; i < protocols.length; i++) {
                currentAmount = _executeSwap(protocols[i], routers[i], currentToken, tokenOutPath[i], currentAmount, extra[i]);
                currentToken = tokenOutPath[i];
            }
            return;
        }

        if (enc == RouteEncoding.REGISTRY_ENUMS) {
            (, uint8[] memory protocols, uint8[] memory dexIds, uint8[] memory tokenOutIds, uint8[] memory tokenOutTypes, bytes[] memory extra) =
                abi.decode(routeData, (RouteEncoding, uint8[], uint8[], uint8[], uint8[], bytes[]));

            require(protocols.length == dexIds.length && dexIds.length == tokenOutIds.length && tokenOutIds.length == tokenOutTypes.length && tokenOutTypes.length == extra.length, "route: len mismatch");

            for (uint256 i = 0; i < protocols.length; i++) {
                address router = resolveDex(chainId, Dex(dexIds[i]));
                address tokenOut = resolveToken(chainId, TokenId(tokenOutIds[i]), TokenType(tokenOutTypes[i]));

                currentAmount = _executeSwap(protocols[i], router, currentToken, tokenOut, currentAmount, extra[i]);
                currentToken = tokenOut;
            }
            return;
        }

        revert("route: bad encoding");
    }

    // ========= OWNER WITHDRAW =========

    function withdraw(address token, address to) external onlyOwner {
        require(to != address(0), "to=0");
        IERC20(token).safeTransfer(to, IERC20(token).balanceOf(address(this)));
    }
}
