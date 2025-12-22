// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IUniV2.sol";
import "../interfaces/IUniV3.sol";
import "../interfaces/ICurve.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

abstract contract SwapHandler {
    using SafeERC20 for IERC20;

    // Protocol IDs (LOCK THESE)
    uint8 internal constant PROTOCOL_UNIV2 = 1;
    uint8 internal constant PROTOCOL_UNIV3 = 2;
    uint8 internal constant PROTOCOL_CURVE = 3;

    function _approveIfNeeded(address token, address spender, uint256 amount) internal {
        IERC20 t = IERC20(token);
        uint256 a = t.allowance(address(this), spender);
        if (a < amount) {
            t.forceApprove(spender, amount);
        }
    }

    function _executeSwap(
        uint8 protocol,
        address routerOrPool,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        bytes memory extraData
    ) internal returns (uint256 amountOut) {
        
        // Safe approval - use forceApprove for OpenZeppelin v5
        IERC20(tokenIn).forceApprove(routerOrPool, amountIn);

        if (protocol == PROTOCOL_UNIV2) {
            address[] memory path = new address[](2);
            path[0] = tokenIn;
            path[1] = tokenOut;

            uint256[] memory amounts = IUniswapV2Router(routerOrPool).swapExactTokensForTokens(
                amountIn,
                0,
                path,
                address(this),
                block.timestamp
            );
            amountOut = amounts[amounts.length - 1];
            require(amountOut > 0, "UniV2: out=0");
            return amountOut;
        }

        if (protocol == PROTOCOL_UNIV3) {
            require(extraData.length == 32, "UniV3: extra=fee");
            uint24 fee = abi.decode(extraData, (uint24));

            IUniswapV3Router.ExactInputSingleParams memory params =
                IUniswapV3Router.ExactInputSingleParams({
                    tokenIn: tokenIn,
                    tokenOut: tokenOut,
                    fee: fee,
                    recipient: address(this),
                    deadline: block.timestamp,
                    amountIn: amountIn,
                    amountOutMinimum: 0,
                    sqrtPriceLimitX96: 0
                });

            amountOut = IUniswapV3Router(routerOrPool).exactInputSingle(params);
            require(amountOut > 0, "UniV3: out=0");
            return amountOut;
        }

        if (protocol == PROTOCOL_CURVE) {
            require(extraData.length == 64, "Curve: extra=(i,j)");
            (int128 i, int128 j) = abi.decode(extraData, (int128, int128));

            amountOut = ICurvePool(routerOrPool).exchange(i, j, amountIn, 0);
            require(amountOut > 0, "Curve: out=0");
            return amountOut;
        }

        // Reset approval to zero for safety (USDT compatibility)
        IERC20(tokenIn).forceApprove(routerOrPool, 0);
        
        return amountOut;
    }
}
