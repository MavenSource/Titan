// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IUniV2
 * @notice Interface for Uniswap V2 style routers (Quickswap, Sushi, etc.)
 */
interface IUniswapV2Router {
    function swapExactTokensForTokens(
        uint amountIn,
        uint amountOutMin,
        address[] calldata path,
        address to,
        uint deadline
    ) external returns (uint[] memory amounts);
}
