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
        
        // Approve router to spend tokens
        _approveIfNeeded(tokenIn, router, amountIn);

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
        
        uint[] memory amounts = IUniswapV2Router(router).swapExactTokensForTokens(
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
            fee == 100 || fee == 500 || fee == 3000 || fee == 10000,
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
        require(i >= 0 && i < 8, "Invalid Curve index i");
        require(j >= 0 && j < 8, "Invalid Curve index j");
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
     * @dev Some tokens require allowance to be set to 0 before updating
     */
    function _approveIfNeeded(
        address token,
        address spender,
        uint256 amount
    ) internal {
        IERC20 t = IERC20(token);
        uint256 currentAllowance = t.allowance(address(this), spender);
        
        if (currentAllowance < amount) {
            // Reset allowance to 0 first (for USDT-style tokens)
            if (currentAllowance != 0) {
                t.safeApprove(spender, 0);
            }
            t.safeApprove(spender, amount);
        }
    }
}