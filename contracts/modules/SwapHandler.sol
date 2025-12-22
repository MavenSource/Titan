// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IUniV2.sol";
import "../interfaces/IUniV3.sol";
import "../interfaces/ICurve.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

abstract contract SwapHandler {
    // Protocol IDs
    uint8 constant PROTOCOL_UNIV2 = 1;
    uint8 constant PROTOCOL_UNIV3 = 2;
    uint8 constant PROTOCOL_CURVE = 3;

    function _executeSwap(
        uint8 protocol, 
        address router, 
        address tokenIn, 
        address tokenOut, 
        uint256 amountIn, 
        bytes memory extraData
    ) internal returns (uint256 amountOut) {
        
        IERC20(tokenIn).approve(router, amountIn);

        if (protocol == PROTOCOL_UNIV2) {
            address[] memory path = new address[](2);
            path[0] = tokenIn;
            path[1] = tokenOut;
            uint[] memory amounts = IUniswapV2Router(router).swapExactTokensForTokens(
                amountIn, 0, path, address(this), block.timestamp
            );
            return amounts[amounts.length - 1];

        } else if (protocol == PROTOCOL_UNIV3) {
            uint24 fee = abi.decode(extraData, (uint24));
            IUniswapV3Router.ExactInputSingleParams memory params = IUniswapV3Router.ExactInputSingleParams({
                tokenIn: tokenIn,
                tokenOut: tokenOut,
                fee: fee,
                recipient: address(this),
                deadline: block.timestamp,
                amountIn: amountIn,
                amountOutMinimum: 0,
                sqrtPriceLimitX96: 0
            });
            return IUniswapV3Router(router).exactInputSingle(params);

        } else if (protocol == PROTOCOL_CURVE) {
            // extraData needs to contain [i, j] indices for Curve
            (int128 i, int128 j) = abi.decode(extraData, (int128, int128));
            return ICurve(router).exchange(i, j, amountIn, 0);
        }
        
        return 0;
    }
}