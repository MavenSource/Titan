// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IDEX.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title SwapHandler
 * @notice System-wide swap execution module (reusable across contracts)
 * @dev Abstract contract providing unified swap interface for multiple DEX protocols
 */
abstract contract SwapHandler {
    using SafeERC20 for IERC20;

    /* ========== PROTOCOL IDS ========== */
    
    uint8 internal constant PROTOCOL_UNIV2 = 1;  // UniV2-style (Quickswap, Sushi, etc.)
    uint8 internal constant PROTOCOL_UNIV3 = 2;  // Uniswap V3
    uint8 internal constant PROTOCOL_CURVE = 3;  // Curve Finance
    
    /* ========== CONSTANTS ========== */
    
    // Uniswap V3 pool fee tiers
    uint24 internal constant FEE_LOWEST = 100;    // 0.01%
    uint24 internal constant FEE_LOW = 500;       // 0.05%
    uint24 internal constant FEE_MEDIUM = 3000;   // 0.3%
    uint24 internal constant FEE_HIGH = 10000;    // 1%
    
    // Curve pool constraints
    uint8 internal constant MAX_CURVE_INDICES = 8;
    
    /* ========== CONFIGURABLE DEADLINE ========== */
    
    // Default deadline can be overridden by child contracts
    uint256 internal _swapDeadline = 180; // 3 minutes default

    /* ========== INTERNAL SWAP EXECUTION ========== */

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
        require(router != address(0), "Invalid router");
        require(tokenIn != address(0), "Invalid tokenIn");
        require(tokenOut != address(0), "Invalid tokenOut");
        require(amountIn > 0, "Invalid amount");
        
        // Safe approval - use forceApprove for OpenZeppelin v5
        IERC20(tokenIn).forceApprove(routerOrPool, amountIn);

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

        // Reset approval to zero for safety (USDT compatibility)
        IERC20(tokenIn).forceApprove(routerOrPool, 0);
        
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