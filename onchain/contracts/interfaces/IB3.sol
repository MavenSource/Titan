// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

interface IVaultV3 {
    // V3 Core: The Unlock Pattern
    function unlock(bytes calldata data) external returns (bytes memory);
    
    // V3 Transient Accounting
    // "sendTo" creates DEBT (You owe the vault)
    function sendTo(IERC20 token, address to, uint256 amount) external;
    
    // "settle" clears DEBT (You pay back)
    function settle(IERC20 token, uint256 amount) external returns (uint256);
}