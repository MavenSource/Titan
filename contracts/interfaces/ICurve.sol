// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

interface ICurve {
    // Standard Curve Swap
    function exchange(
        int128 i, 
        int128 j, 
        uint256 dx, 
        uint256 min_dy
    ) external returns (uint256);

    // Tricrypto / NG Pools often use uint256 indices
    function exchange(
        uint256 i, 
        uint256 j, 
        uint256 dx, 
        uint256 min_dy
    ) external returns (uint256);

    // View function to check output
    function get_dy(int128 i, int128 j, uint256 dx) external view returns (uint256);
}

// Alias for compatibility
interface ICurvePool {
    function exchange(
        int128 i,
        int128 j,
        uint256 dx,
        uint256 min_dy
    ) external returns (uint256);
}