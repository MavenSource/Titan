// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IUniV2.sol";
import "../interfaces/IUniV3.sol";
import "../interfaces/ICurve.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title SwapHandler
 * @notice Battle-ready swap execution module with MEV protection
 * @dev Supports UniV2 multi-hop, UniV3 multi-hop, and Curve with on-chain slippage protection
 * 
 * extraData schema (UNIFORM):
 *   extraData = abi.encode(uint256 minOut, bytes protocolData)
 *
 * protocolData per protocol:
 * - UNIV2:
 *     protocolData = abi.encode(address[] path, uint256 deadline)
 *     (path[0] must be tokenIn, last must be tokenOut)
 *
 * - UNIV3 (single hop):
 *     protocolData = abi.encode(uint24 fee, uint160 sqrtPriceLimitX96, uint256 deadline)
 *
 * - UNIV3 (multi-hop exactInput):
 *     protocolData = abi.encode(bytes path, uint256 deadline)
 *     where `path` is Uniswap V3 path encoding: tokenIn(20) + fee(3) + tokenMid(20) + fee(3) + tokenOut(20)...
 *
 * - CURVE:
 *     protocolData = abi.encode(int128 i, int128 j, uint256 deadline)
 *     (routerOrPool is the Curve pool address)
 */
abstract contract SwapHandler {
    using SafeERC20 for IERC20;

    // Protocol IDs
    uint8 internal constant PROTOCOL_UNIV2  = 1;
    uint8 internal constant PROTOCOL_UNIV3  = 2;
    uint8 internal constant PROTOCOL_CURVE  = 3;

    error UnsupportedProtocol(uint8 protocol);
    error BadRouter(address router);
    error Slippage(uint256 out, uint256 minOut);
    error InvalidPath(string reason);

    /**
     * @notice Execute a swap on the specified protocol with on-chain slippage protection
     * @param protocol Protocol identifier (1=UniV2, 2=UniV3, 3=Curve)
     * @param router Router address for UniV2/V3, pool address for Curve
     * @param tokenIn Input token address
     * @param tokenOut Output token address
     * @param amountIn Amount of input tokens to swap
     * @param extraData Encoded as abi.encode(uint256 minOut, bytes protocolData)
     * @return amountOut Amount of output tokens received
     */
    function _executeSwap(
        uint8 protocol,
        address router,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        bytes memory extraData
    ) internal returns (uint256 amountOut) {
        if (router.code.length == 0) revert BadRouter(router);

        (uint256 minOut, bytes memory protocolData) = abi.decode(extraData, (uint256, bytes));

        // Safe approve pattern (USDT-style tokens)
        IERC20(tokenIn).forceApprove(router, amountIn);

        if (protocol == PROTOCOL_UNIV2) {
            (address[] memory path, uint256 deadline) = abi.decode(protocolData, (address[], uint256));
            // Sanity checks
            if (path.length < 2) revert InvalidPath("UNIV2: bad path length");
            if (path[0] != tokenIn) revert InvalidPath("UNIV2: path[0]!=tokenIn");
            if (path[path.length - 1] != tokenOut) revert InvalidPath("UNIV2: path[last]!=tokenOut");

            uint256[] memory amounts = IUniswapV2Router(router).swapExactTokensForTokens(
                amountIn,
                minOut,                 // ✅ on-chain slippage guard
                path,
                address(this),
                deadline == 0 ? block.timestamp : deadline
            );
            amountOut = amounts[amounts.length - 1];
            require(amountOut > 0, "UniV2: out=0");
            return amountOut;
        }

        } else if (protocol == PROTOCOL_UNIV3) {
            // Decide between single-hop vs multi-hop by protocolData length
            // Single hop: (uint24, uint160, uint256) = 96 bytes (3 * 32)
            // Multi-hop: (bytes, uint256) = variable + 32 bytes (always > 96)
            // NOTE: This heuristic works because:
            // - Single hop encoding is always exactly 96 bytes
            // - Multi-hop encoding has dynamic bytes array (always different length)
            // - Bot must encode correctly based on intended routing
            if (protocolData.length == 96) {
                // Single hop
                (uint24 fee, uint160 sqrtPriceLimitX96, uint256 deadline) =
                    abi.decode(protocolData, (uint24, uint160, uint256));

                IUniswapV3Router.ExactInputSingleParams memory params =
                    IUniswapV3Router.ExactInputSingleParams({
                        tokenIn: tokenIn,
                        tokenOut: tokenOut,
                        fee: fee,
                        recipient: address(this),
                        deadline: deadline == 0 ? block.timestamp : deadline,
                        amountIn: amountIn,
                        amountOutMinimum: minOut,          // ✅ slippage guard
                        sqrtPriceLimitX96: sqrtPriceLimitX96
                    });

                amountOut = IUniswapV3Router(router).exactInputSingle(params);
            } else {
                // Multi-hop
                (bytes memory pathBytes, uint256 deadline) = abi.decode(protocolData, (bytes, uint256));

                IUniswapV3Router.ExactInputParams memory p =
                    IUniswapV3Router.ExactInputParams({
                        path: pathBytes,
                        recipient: address(this),
                        deadline: deadline == 0 ? block.timestamp : deadline,
                        amountIn: amountIn,
                        amountOutMinimum: minOut          // ✅ slippage guard
                    });

                amountOut = IUniswapV3Router(router).exactInput(p);
            }

        } else if (protocol == PROTOCOL_CURVE) {
            (int128 i, int128 j, uint256 deadline) = abi.decode(protocolData, (int128, int128, uint256));
            if (deadline != 0 && block.timestamp > deadline) revert InvalidPath("CURVE: expired");

            amountOut = ICurve(router).exchange(i, j, amountIn, minOut); // ✅ slippage guard

        } else {
            revert UnsupportedProtocol(protocol);
        }

        // Final safety check: Ensure amountOut meets minimum expectation
        // NOTE: While protocol-specific calls already enforce minOut, this provides
        // defense-in-depth against unexpected protocol behavior or implementation bugs
        if (amountOut < minOut) revert Slippage(amountOut, minOut);
    }
}
