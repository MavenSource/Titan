// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IVaultV3 {
    function unlock(bytes calldata data) external returns (bytes memory);

    function sendTo(IERC20 token, address to, uint256 amount) external;

    function settle(IERC20 token, uint256 amount) external returns (uint256);
}

interface IBalancerVaultV3 is IVaultV3 {}