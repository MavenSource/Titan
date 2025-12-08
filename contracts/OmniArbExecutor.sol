// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

// === INTERFACES ===
interface IVaultV3 {
    function unlock(bytes calldata data) external returns (bytes memory);
    function settle(IERC20 token, uint256 amount) external returns (uint256);
    function sendTo(IERC20 token, address to, uint256 amount) external;
}

interface IAavePool {
    function flashLoanSimple(address receiver, address asset, uint256 amount, bytes calldata params, uint16 referralCode) external;
}

interface IUniswapV3Router {
    struct ExactInputSingleParams {
        address tokenIn; address tokenOut; uint24 fee; address recipient; uint256 deadline; uint256 amountIn; uint256 amountOutMinimum; uint160 sqrtPriceLimitX96;
    }
    function exactInputSingle(ExactInputSingleParams calldata params) external payable returns (uint256 amountOut);
}

interface ICurve {
    function exchange(int128 i, int128 j, uint256 dx, uint256 min_dy) external returns (uint256);
}

// === MAIN CONTRACT ===
contract OmniArbExecutor is Ownable {
    IVaultV3 public immutable BALANCER_VAULT;
    IAavePool public immutable AAVE_POOL;

    constructor(address _balancer, address _aave) Ownable(msg.sender) {
        BALANCER_VAULT = IVaultV3(_balancer);
        AAVE_POOL = IAavePool(_aave);
    }

    // =================================================================
    // 1. TRIGGER (Called by Node.js)
    // =================================================================
    function execute(
        uint8 flashSource, // 1=Balancer, 2=Aave
        address loanToken,
        uint256 loanAmount,
        bytes calldata routeData // Encoded path
    ) external onlyOwner {
        if (flashSource == 1) {
            // Balancer V3: "Unlock" the vault
            bytes memory callbackData = abi.encode(loanToken, loanAmount, routeData);
            BALANCER_VAULT.unlock(abi.encodeWithSelector(this.onBalancerUnlock.selector, callbackData));
        } else {
            // Aave V3: Standard Flashloan
            AAVE_POOL.flashLoanSimple(address(this), loanToken, loanAmount, routeData, 0);
        }
    }

    // =================================================================
    // 2. BALANCER V3 CALLBACK
    // =================================================================
    function onBalancerUnlock(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(BALANCER_VAULT), "Auth");
        (address token, uint256 amount, bytes memory routeData) = abi.decode(data, (address, uint256, bytes));

        // A. Take Debt (V3 Specific)
        BALANCER_VAULT.sendTo(IERC20(token), address(this), amount);

        // B. Execute Logic
        _runRoute(token, amount, routeData);

        // C. Repay
        IERC20(token).transfer(address(BALANCER_VAULT), amount);
        BALANCER_VAULT.settle(IERC20(token), amount);
        
        return "";
    }

    // =================================================================
    // 3. AAVE V3 CALLBACK
    // =================================================================
    function executeOperation(address asset, uint256 amount, uint256 premium, address, bytes calldata routeData) external returns (bool) {
        require(msg.sender == address(AAVE_POOL), "Auth");
        
        _runRoute(asset, amount, routeData);

        uint256 owed = amount + premium;
        IERC20(asset).approve(address(AAVE_POOL), owed);
        return true;
    }

    // =================================================================
    // 4. UNIVERSAL SWAP ENGINE
    // =================================================================
    function _runRoute(address inputToken, uint256 inputAmount, bytes memory routeData) internal {
        // Decode: Arrays of [ProtocolID, RouterAddr, TokenOut, ExtraBytes]
        (
            uint8[] memory protocols,
            address[] memory routers,
            address[] memory path,
            bytes[] memory extra
        ) = abi.decode(routeData, (uint8[], address[], address[], bytes[]));

        uint256 currentBal = inputAmount;
        address currentToken = inputToken;

        for (uint i = 0; i < protocols.length; i++) {
            IERC20(currentToken).approve(routers[i], currentBal);

            if (protocols[i] == 1) { // Uniswap V3
                uint24 fee = abi.decode(extra[i], (uint24));
                IUniswapV3Router.ExactInputSingleParams memory p = IUniswapV3Router.ExactInputSingleParams({
                    tokenIn: currentToken, tokenOut: path[i], fee: fee, recipient: address(this),
                    deadline: block.timestamp, amountIn: currentBal, amountOutMinimum: 0, sqrtPriceLimitX96: 0
                });
                currentBal = IUniswapV3Router(routers[i]).exactInputSingle(p);
            } 
            else if (protocols[i] == 2) { // Curve
                (int128 idx_i, int128 idx_j) = abi.decode(extra[i], (int128, int128));
                currentBal = ICurve(routers[i]).exchange(idx_i, idx_j, currentBal, 0);
            }
            
            currentToken = path[i];
        }
        
        // Profit Check implicitly handled by repayment success
    }

    function withdraw(address token) external onlyOwner {
        IERC20(token).transfer(msg.sender, IERC20(token).balanceOf(address(this)));
    }
}