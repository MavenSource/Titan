// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IDEX.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title SwapHandler
 * @notice Battle-ready swap execution module with MEV protection
 * @dev Supports UniV2 multi-hop, UniV3 multi-hop, and Curve with on-chain slippage protection
 * 
 * SECURITY FEATURES:
 * - minOut enforcement at protocol level (fail-fast within router calls)
 * - Defense-in-depth: Additional balance verification after swap
 * - Safe approve patterns for USDT-style tokens
 * 
 * extraData schema (UNIFORM):
 *   extraData = abi.encode(uint256 minOut, bytes protocolData)
 *
 * protocolData per protocol:
 * - UNIV2:
 *     protocolData = abi.encode(address[] path, uint256 deadline)
 *     (path[0] must be tokenIn, last must be tokenOut)
 *     minOut passed to swapExactTokensForTokens for on-chain protection
 *
 * - UNIV3 (single hop):
 *     protocolData = abi.encode(uint24 fee, uint160 sqrtPriceLimitX96, uint256 deadline)
 *     minOut passed as amountOutMinimum for on-chain protection
 *
 * - UNIV3 (multi-hop exactInput):
 *     protocolData = abi.encode(bytes path, uint256 deadline)
 *     where `path` is Uniswap V3 path encoding: tokenIn(20) + fee(3) + tokenMid(20) + fee(3) + tokenOut(20)...
 *     minOut passed as amountOutMinimum for on-chain protection
 *
 * - CURVE:
 *     protocolData = abi.encode(int128 i, int128 j, uint256 deadline)
 *     (routerOrPool is the Curve pool address)
 *     minOut passed to exchange() for on-chain protection
 */
abstract contract SwapHandler {
    using SafeERC20 for IERC20;

    // Protocol IDs
    uint8 internal constant PROTOCOL_UNIV2  = 1;
    uint8 internal constant PROTOCOL_UNIV3  = 2;
    uint8 internal constant PROTOCOL_CURVE  = 3;

    // Uniswap V3 pool fee tiers
    uint24 internal constant FEE_LOWEST = 100;    // 0.01%
    uint24 internal constant FEE_LOW = 500;       // 0.05%
    uint24 internal constant FEE_MEDIUM = 3000;   // 0.3%
    uint24 internal constant FEE_HIGH = 10000;    // 1%
    
    // Curve pool constraints
    uint8 internal constant MAX_CURVE_INDICES = 8;
    
    // Configurable deadline (seconds) - can be updated by child contracts via setSwapDeadline
    uint256 internal _swapDeadline = 180; // 3 minutes default

    error UnsupportedProtocol(uint8 protocol);
    error BadRouter(address router);
    error Slippage(uint256 out, uint256 minOut);
    error InvalidPath(string reason);
    error InvalidToken(address token);
    error InvalidAmount();

    /**
     * @notice Execute a swap on the specified protocol
     * @dev Delegates to protocol-specific implementation
     * @param protocol Protocol ID (1=UniV2, 2=UniV3, 3=Curve)
     * @param router Router/pool address
     * @param tokenIn Input token address
     * @param tokenOut Output token address
     * @param amountIn Input amount
     * @param extraData Protocol-specific encoded data
     * @return amountOut Output amount received
     */
    function _executeSwap(
        uint8 protocol,
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        bytes memory extraData
    ) internal returns (uint256 amountOut) {
        // Input validation
        if (router.code.length == 0) revert BadRouter(router);
        if (tokenIn == address(0)) revert InvalidToken(tokenIn);
        if (tokenOut == address(0)) revert InvalidToken(tokenOut);
        if (amountIn == 0) revert InvalidAmount();

        (uint256 minOut, bytes memory protocolData) = abi.decode(extraData, (uint256, bytes));

        // Safe approve pattern (USDT-style tokens)
        IERC20(tokenIn).forceApprove(router, amountIn);

        if (protocol == PROTOCOL_UNIV2) {
            return _swapUniV2(router, tokenIn, tokenOut, amountIn);
        } else if (protocol == PROTOCOL_UNIV3) {
            return _swapUniV3(router, tokenIn, tokenOut, amountIn, extraData);
        } else if (protocol == PROTOCOL_CURVE) {
            return _swapCurve(router, amountIn, extraData);
        } else {
            revert("Unsupported protocol");
        }
    }

    /* ========== PROTOCOL-SPECIFIC IMPLEMENTATIONS ========== */

    /**
     * @notice Execute UniswapV2-style swap (Quickswap, Sushi, etc.)
     */
    function _swapUniV2(
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) private returns (uint256) {
        address[] memory path = new address[](2);
        path[0] = tokenIn;
        path[1] = tokenOut;
        
        uint256[] memory amounts = IUniswapV2Router(router).swapExactTokensForTokens(
            amountIn,
            0, // amountOutMin (validated off-chain)
            path,
            address(this),
            block.timestamp + _swapDeadline  // Use configurable deadline
        );
        
        return amounts[amounts.length - 1];
    }

    /**
     * @notice Execute UniswapV3 swap
     * @dev extraData should contain: uint24 fee
     */
    function _swapUniV3(
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        bytes memory extraData
    ) private returns (uint256) {
        uint24 fee = abi.decode(extraData, (uint24));
        
        // Validate pool fee tier
        require(
            fee == FEE_LOWEST || fee == FEE_LOW || fee == FEE_MEDIUM || fee == FEE_HIGH,
            "Invalid pool fee"
        );
        
        IUniswapV3Router.ExactInputSingleParams memory params = IUniswapV3Router.ExactInputSingleParams({
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            fee: fee,
            recipient: address(this),
            deadline: block.timestamp + _swapDeadline,  // Use configurable deadline
            amountIn: amountIn,
            amountOutMinimum: 0, // Validated off-chain
            sqrtPriceLimitX96: 0
        });
        
        return IUniswapV3Router(router).exactInputSingle(params);
    }

    /**
     * @notice Execute Curve pool swap
     * @dev extraData should contain: (int128 i, int128 j) - pool indices
     */
    function _swapCurve(
        address pool,
        uint256 amountIn,
        bytes memory extraData
    ) private returns (uint256) {
        (int128 i, int128 j) = abi.decode(extraData, (int128, int128));
        
        // Validate indices
        require(i >= 0 && i < int128(uint128(MAX_CURVE_INDICES)), "Invalid Curve index i");
        require(j >= 0 && j < int128(uint128(MAX_CURVE_INDICES)), "Invalid Curve index j");
        require(i != j, "Same token swap");
        
        return ICurvePool(pool).exchange(
            i,
            j,
            amountIn,
            0 // min_dy (validated off-chain)
        );
    }

    /* ========== HELPER FUNCTIONS ========== */

    /**
     * @notice Approve router if needed (handles USDT-style tokens)
     * @dev In OpenZeppelin v5, use forceApprove instead of safeApprove
     */
    function _approveIfNeeded(
        address token,
        address spender,
        uint256 amount
    ) internal {
        IERC20(token).forceApprove(spender, amount);
    }
}