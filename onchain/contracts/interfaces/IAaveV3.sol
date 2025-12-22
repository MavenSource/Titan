// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IAaveV3
 * @notice Interface for Aave V3 Pool and Flash Loan functionality
 */
interface IAavePoolV3 {
    /**
     * @notice Execute a simple flashloan (single asset)
     * @param receiverAddress The address receiving the flash loan
     * @param asset The address of the asset to flash loan
     * @param amount The amount to flash loan
     * @param params Arbitrary bytes-encoded params passed to executeOperation callback
     * @param referralCode Referral code for Aave integrations (use 0 if none)
     */
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

/**
 * @title IAaveFlashLoanSimpleReceiver
 * @notice Interface that flash loan receivers must implement
 */
interface IAaveFlashLoanSimpleReceiver {
    /**
     * @notice Called by Aave Pool after funds are transferred to receiver
     * @param asset The address of the flash-borrowed asset
     * @param amount The amount of the flash-borrowed asset
     * @param premium The fee for the flash loan
     * @param initiator The address initiating the flash loan
     * @param params Arbitrary bytes-encoded params passed from flashLoanSimple
     * @return bool Must return true for the flashloan to succeed
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool);
}
