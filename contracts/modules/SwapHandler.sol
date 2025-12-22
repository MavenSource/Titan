// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IUniV2.sol";
import "../interfaces/IUniV3.sol";
import "../interfaces/ICurve.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title SwapHandler
 * @notice System-wide swap execution module supporting UniV2, UniV3, and Curve
 * @dev Reusable primitive for executing swaps across multiple DEX protocols
 */
abstract contract SwapHandler {
    using SafeERC20 for IERC20;

    // Protocol IDs
    uint8 constant PROTOCOL_UNIV2 = 1;
    uint8 constant PROTOCOL_UNIV3 = 2;
    uint8 constant PROTOCOL_CURVE = 3;

    /**
     * @notice Execute a swap on the specified protocol
     * @param protocol Protocol identifier (1=UniV2, 2=UniV3, 3=Curve)
     * @param routerOrPool Router address for UniV2/V3, pool address for Curve
     * @param tokenIn Input token address
     * @param tokenOut Output token address
     * @param amountIn Amount of input tokens to swap
     * @param extraData Protocol-specific encoded data
     * @return amountOut Amount of output tokens received
     */
    function _executeSwap(
        uint8 protocol, 
        address routerOrPool, 
        address tokenIn, 
        address tokenOut, 
        uint256 amountIn, 
        bytes memory extraData
    ) internal returns (uint256 amountOut) {
        
        // Safe approval - use safeIncreaseAllowance for OpenZeppelin v5
        IERC20(tokenIn).safeIncreaseAllowance(routerOrPool, amountIn);

        if (protocol == PROTOCOL_UNIV2) {
            // UniV2-style swap (Quickswap, Sushi, etc.)
            address[] memory path = new address[](2);
            path[0] = tokenIn;
            path[1] = tokenOut;
            uint[] memory amounts = IUniswapV2Router(routerOrPool).swapExactTokensForTokens(
                amountIn, 
                0, // minAmountOut (slippage checked off-chain)
                path, 
                address(this), 
                block.timestamp
            );
            amountOut = amounts[amounts.length - 1];

        } else if (protocol == PROTOCOL_UNIV3) {
            // UniV3 swap with fee from extraData
            uint24 fee = abi.decode(extraData, (uint24));
            IUniswapV3Router.ExactInputSingleParams memory params = IUniswapV3Router.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: fee,
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountIn,
                amountOutMinimum: 0, // slippage checked off-chain
                sqrtPriceLimitX96: 0
            });
            amountOut = IUniswapV3Router(routerOrPool).exactInputSingle(params);

        } else if (protocol == PROTOCOL_CURVE) {
            // Curve pool swap with indices from extraData
            (int128 i, int128 j) = abi.decode(extraData, (int128, int128));
            amountOut = ICurve(routerOrPool).exchange(i, j, amountIn, 0);

        } else {
            revert("Unsupported protocol");
        }

        // Reset approval to zero for safety (USDT compatibility)
        SafeERC20.forceApprove(IERC20(tokenIn), routerOrPool, 0);
        
        return amountOut;
    }
}
