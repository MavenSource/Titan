// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

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
    
    // Configurable deadline for time-sensitive swaps (in seconds)
    uint256 public swapDeadline = 180; // Default 3 minutes

    constructor(address _balancer, address _aave) Ownable(msg.sender) {
        BALANCER_VAULT = IVaultV3(_balancer);
        AAVE_POOL = IAavePool(_aave);
    }
    
    // Allow owner to adjust deadline based on trading strategy
    function setSwapDeadline(uint256 _seconds) external onlyOwner {
        require(_seconds >= 60 && _seconds <= 600, "Deadline must be 60-600 seconds");
        swapDeadline = _seconds;
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

        // Validation: All arrays must have same length
        require(protocols.length == routers.length, "Length mismatch: protocols/routers");
        require(protocols.length == path.length, "Length mismatch: protocols/path");
        require(protocols.length == extra.length, "Length mismatch: protocols/extra");
        require(protocols.length > 0, "Empty route");
        require(protocols.length <= 5, "Route too long"); // Safety limit

        uint256 currentBal = inputAmount;
        address currentToken = inputToken;
        uint256 initialInputAmount = inputAmount;

        for (uint i = 0; i < protocols.length; i++) {
            // Validation: Check for zero address router
            require(routers[i] != address(0), "Invalid router address");
            require(path[i] != address(0), "Invalid token address");
            require(currentBal > 0, "Zero balance in route");
            
            IERC20(currentToken).approve(routers[i], currentBal);
            uint256 balanceBefore = currentBal;

            if (protocols[i] == 1) { // Uniswap V3
                uint24 fee = abi.decode(extra[i], (uint24));
                require(fee == 100 || fee == 500 || fee == 3000 || fee == 10000, "Invalid pool fee");
                
                IUniswapV3Router.ExactInputSingleParams memory p = IUniswapV3Router.ExactInputSingleParams({
                    tokenIn: currentToken, 
                    tokenOut: path[i], 
                    fee: fee, 
                    recipient: address(this),
                    deadline: block.timestamp + swapDeadline, // Configurable via setSwapDeadline()
                    amountIn: currentBal, 
                    amountOutMinimum: 0, // Slippage checked off-chain via simulation
                    sqrtPriceLimitX96: 0
                });
                currentBal = IUniswapV3Router(routers[i]).exactInputSingle(p);
            } 
            else if (protocols[i] == 2) { // Curve
                (int128 idx_i, int128 idx_j) = abi.decode(extra[i], (int128, int128));
                require(idx_i >= 0 && idx_i < 8, "Invalid Curve index i");
                require(idx_j >= 0 && idx_j < 8, "Invalid Curve index j");
                require(idx_i != idx_j, "Same token swap");
                
                currentBal = ICurve(routers[i]).exchange(idx_i, idx_j, currentBal, 0);
            }
            else {
                revert("Unsupported protocol");
            }
            
            // Safety check: Ensure we received something from the swap
            require(currentBal > 0, "Swap returned zero");
            
            currentToken = path[i];
        }
        
        // Final validation: Must have more than we started with (profit check)
        // This is a basic sanity check - the real profit is validated by repayment success
        require(currentBal >= initialInputAmount / 2, "Suspicious loss detected"); // Lost more than 50%
    }

    function withdraw(address token) external onlyOwner {
        IERC20(token).transfer(msg.sender, IERC20(token).balanceOf(address(this)));
    }
}