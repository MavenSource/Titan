// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/*
=============================================================================
OmniArbExecutor.sol (Refactored with Custom Enum Logic)

- Reuses system-wide SwapHandler module for all swap operations
- Supports Aave V3 flashLoanSimple + Balancer V3 unlock transient debt
- Adds CUSTOM ENUM LOGIC for:
  * DEX registry (per-chain routers)
  * CHAIN identity (block.chainid -> Chain enum)
  * TOKEN registry with WRAPPED + BRIDGED variants
  * Optional registry-encoded routes (cleaner encoding)
=============================================================================
*/

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./modules/SwapHandler.sol";
import "./interfaces/IB3.sol";
import "./interfaces/IAaveV3.sol";

/* ============================== CUSTOM ENUMS ============================== */

/**
 * @dev Chain identifiers mapped from block.chainid
 */
enum Chain {
    ETHEREUM,      // 1
    POLYGON,       // 137
    ARBITRUM,      // 42161
    OPTIMISM,      // 10
    BASE,          // 8453
    BSC,           // 56
    AVALANCHE,     // 43114
    FANTOM,        // 250
    LINEA,         // 59144
    SCROLL,        // 534352
    MANTLE,        // 5000
    ZKSYNC,        // 324
    BLAST,         // 81457
    CELO,          // 42220
    OPBNB          // 204
}

/**
 * @dev DEX identifiers (per-chain router registry)
 */
enum DEX {
    UNISWAP_V2,
    UNISWAP_V3,
    SUSHISWAP,
    QUICKSWAP,
    PANCAKESWAP,
    CURVE,
    BALANCER,
    TRADER_JOE,
    SPOOKYSWAP,
    AERODROME,
    VELODROME
}

/**
 * @dev Token identifiers with WRAPPED + BRIDGED variants
 * Format: TOKEN_VARIANT_CHAIN (where applicable)
 */
enum Token {
    // Native wrapped
    WETH,          // Wrapped ETH on Ethereum
    WMATIC,        // Wrapped MATIC on Polygon
    WBNB,          // Wrapped BNB on BSC
    WAVAX,         // Wrapped AVAX on Avalanche
    WFTM,          // Wrapped FTM on Fantom
    
    // Stablecoins (native)
    USDC,          // Native USDC on origin chains
    USDT,          // Native USDT on origin chains
    DAI,           // Native DAI on origin chains
    FRAX,          // Native FRAX
    
    // Bridged stablecoins on Polygon
    USDC_BRIDGED_POLYGON,
    USDT_BRIDGED_POLYGON,
    DAI_BRIDGED_POLYGON,
    
    // Bridged stablecoins on Arbitrum
    USDC_BRIDGED_ARBITRUM,
    USDT_BRIDGED_ARBITRUM,
    DAI_BRIDGED_ARBITRUM,
    
    // Bridged stablecoins on Optimism
    USDC_BRIDGED_OPTIMISM,
    USDT_BRIDGED_OPTIMISM,
    DAI_BRIDGED_OPTIMISM,
    
    // Bridged stablecoins on Base
    USDC_BRIDGED_BASE,
    
    // Bridged ETH variants
    WETH_BRIDGED_POLYGON,
    WETH_BRIDGED_ARBITRUM,
    WETH_BRIDGED_OPTIMISM,
    WETH_BRIDGED_BASE,
    WETH_BRIDGED_AVALANCHE,
    
    // Bridged BTC variants
    WBTC,
    WBTC_BRIDGED_POLYGON,
    WBTC_BRIDGED_ARBITRUM,
    
    // Other major tokens
    LINK,
    AAVE,
    CRV,
    BAL,
    SUSHI
}

/* ============================== MAIN CONTRACT ============================== */

/**
 * @title OmniArbExecutor
 * @notice Multi-chain arbitrage executor with flash loan support
 * @dev Reuses SwapHandler module (system-wide component) for all swaps
 */
contract OmniArbExecutor is Ownable, ReentrancyGuard, SwapHandler, IFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;

    /* ========== STATE VARIABLES ========== */
    
    IVaultV3 public immutable BALANCER_VAULT;
    IAavePool public immutable AAVE_POOL;
    
    // Configurable deadline for time-sensitive swaps (in seconds)
    uint256 public swapDeadline = 180; // Default 3 minutes
    
    // Loss threshold constant (50% max loss before revert)
    uint256 private constant MIN_OUTPUT_RATIO = 2;
    
    /* ========== REGISTRY MAPPINGS ========== */
    
    // Chain ID to Chain enum
    mapping(uint256 => Chain) public chainIdToChain;
    
    // Token enum to actual address (per chain)
    mapping(Chain => mapping(Token => address)) public tokenRegistry;
    
    // DEX enum to router address (per chain)
    mapping(Chain => mapping(DEX => address)) public dexRegistry;
    
    /* ========== EVENTS ========== */
    
    event ArbitrageExecuted(
        uint8 flashSource,
        address loanToken,
        uint256 loanAmount,
        uint256 profit
    );
    
    event RegistryUpdated(
        string registryType,
        uint256 indexed key1,
        uint256 indexed key2,
        address value
    );
    
    /* ========== CONSTRUCTOR ========== */
    
    constructor(
        address _balancer,
        address _aave
    ) Ownable(msg.sender) {
        BALANCER_VAULT = IVaultV3(_balancer);
        AAVE_POOL = IAavePool(_aave);
        
        // Initialize chain ID mappings
        _initializeChainMappings();
        
        // Set default swap deadline (inherited from SwapHandler)
        _swapDeadline = swapDeadline;
    }
    
    /* ========== INITIALIZATION ========== */
    
    function _initializeChainMappings() private {
        chainIdToChain[1] = Chain.ETHEREUM;
        chainIdToChain[137] = Chain.POLYGON;
        chainIdToChain[42161] = Chain.ARBITRUM;
        chainIdToChain[10] = Chain.OPTIMISM;
        chainIdToChain[8453] = Chain.BASE;
        chainIdToChain[56] = Chain.BSC;
        chainIdToChain[43114] = Chain.AVALANCHE;
        chainIdToChain[250] = Chain.FANTOM;
        chainIdToChain[59144] = Chain.LINEA;
        chainIdToChain[534352] = Chain.SCROLL;
        chainIdToChain[5000] = Chain.MANTLE;
        chainIdToChain[324] = Chain.ZKSYNC;
        chainIdToChain[81457] = Chain.BLAST;
        chainIdToChain[42220] = Chain.CELO;
        chainIdToChain[204] = Chain.OPBNB;
    }
    
    /* ========== CONFIGURATION ========== */
    
    /**
     * @notice Set swap deadline for time-sensitive operations
     */
    function setSwapDeadline(uint256 _seconds) external onlyOwner {
        require(_seconds >= 60 && _seconds <= 600, "Deadline must be 60-600 seconds");
        swapDeadline = _seconds;
        _swapDeadline = _seconds;  // Update SwapHandler's internal deadline
    }
    
    /**
     * @notice Register a token address for a specific chain
     */
    function registerToken(
        Chain _chain,
        Token _token,
        address _address
    ) external onlyOwner {
        require(_address != address(0), "Invalid address");
        tokenRegistry[_chain][_token] = _address;
        emit RegistryUpdated("token", uint256(_chain), uint256(_token), _address);
    }
    
    /**
     * @notice Register a DEX router address for a specific chain
     */
    function registerDEX(
        Chain _chain,
        DEX _dex,
        address _router
    ) external onlyOwner {
        require(_router != address(0), "Invalid router");
        dexRegistry[_chain][_dex] = _router;
        emit RegistryUpdated("dex", uint256(_chain), uint256(_dex), _router);
    }
    
    /**
     * @notice Batch register multiple tokens
     */
    function batchRegisterTokens(
        Chain _chain,
        Token[] calldata _tokens,
        address[] calldata _addresses
    ) external onlyOwner {
        require(_tokens.length == _addresses.length, "Length mismatch");
        for (uint256 i = 0; i < _tokens.length; i++) {
            require(_addresses[i] != address(0), "Invalid address");
            tokenRegistry[_chain][_tokens[i]] = _addresses[i];
            emit RegistryUpdated("token", uint256(_chain), uint256(_tokens[i]), _addresses[i]);
        }
    }
    
    /**
     * @notice Batch register multiple DEX routers
     */
    function batchRegisterDEXs(
        Chain _chain,
        DEX[] calldata _dexs,
        address[] calldata _routers
    ) external onlyOwner {
        require(_dexs.length == _routers.length, "Length mismatch");
        for (uint256 i = 0; i < _dexs.length; i++) {
            require(_routers[i] != address(0), "Invalid router");
            dexRegistry[_chain][_dexs[i]] = _routers[i];
            emit RegistryUpdated("dex", uint256(_chain), uint256(_dexs[i]), _routers[i]);
        }
    }
    
    /* ========== HELPER FUNCTIONS ========== */
    
    /**
     * @notice Get current chain enum from block.chainid
     */
    function getCurrentChain() public view returns (Chain) {
        return chainIdToChain[block.chainid];
    }
    
    /**
     * @notice Resolve token enum to address on current chain
     */
    function resolveToken(Token _token) public view returns (address) {
        address addr = tokenRegistry[getCurrentChain()][_token];
        require(addr != address(0), "Token not registered");
        return addr;
    }
    
    /**
     * @notice Resolve DEX enum to router address on current chain
     */
    function resolveDEX(DEX _dex) public view returns (address) {
        address router = dexRegistry[getCurrentChain()][_dex];
        require(router != address(0), "DEX not registered");
        return router;
    }

    /* ========== FLASH LOAN TRIGGER ========== */
    
    /**
     * @notice Execute arbitrage with flash loan
     * @param flashSource 1=Balancer, 2=Aave
     * @param loanToken Token to borrow (can be address or resolved from enum)
     * @param loanAmount Amount to borrow
     * @param routeData Encoded route (supports both enum and raw address modes)
     */
    function execute(
        uint8 flashSource,
        address loanToken,
        uint256 loanAmount,
        bytes calldata routeData
    ) external onlyOwner nonReentrant {
        require(loanToken != address(0), "Invalid loan token");
        require(loanAmount > 0, "Invalid loan amount");
        
        if (flashSource == 1) {
            // Balancer V3: "Unlock" the vault
            bytes memory callbackData = abi.encode(loanToken, loanAmount, routeData);
            BALANCER_VAULT.unlock(
                abi.encodeWithSelector(this.onBalancerUnlock.selector, callbackData)
            );
        } else if (flashSource == 2) {
            // Aave V3: Standard flash loan
            AAVE_POOL.flashLoanSimple(
                address(this),
                loanToken,
                loanAmount,
                routeData,
                0
            );
        } else {
            revert("Invalid flash source");
        }
    }

    /* ========== FLASH LOAN CALLBACKS ========== */
    
    /**
     * @notice Balancer V3 unlock callback
     */
    function onBalancerUnlock(bytes calldata data) external returns (bytes memory) {
        require(msg.sender == address(BALANCER_VAULT), "Unauthorized");
        
        (address token, uint256 amount, bytes memory routeData) = abi.decode(
            data,
            (address, uint256, bytes)
        );

        // A. Take debt (V3 specific)
        BALANCER_VAULT.sendTo(IERC20(token), address(this), amount);

        // B. Execute arbitrage route
        uint256 finalAmount = _runRoute(token, amount, routeData);

        // C. Repay debt
        IERC20(token).safeTransfer(address(BALANCER_VAULT), amount);
        BALANCER_VAULT.settle(IERC20(token), amount);
        
        // Emit profit event
        if (finalAmount > amount) {
            emit ArbitrageExecuted(1, token, amount, finalAmount - amount);
        }
        
        return "";
    }

    /**
     * @notice Aave V3 flash loan callback
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address,
        bytes calldata routeData
    ) external returns (bool) {
        require(msg.sender == address(AAVE_POOL), "Unauthorized");
        
        // Execute arbitrage route
        uint256 finalAmount = _runRoute(asset, amount, routeData);

        // Approve repayment (loan + premium)
        uint256 owed = amount + premium;
        IERC20(asset).forceApprove(address(AAVE_POOL), owed);
        
        // Emit profit event
        if (finalAmount > owed) {
            emit ArbitrageExecuted(2, asset, amount, finalAmount - owed);
        }
        
        return true;
    }

    /* ========== ROUTE EXECUTION ========== */
    
    /**
     * @notice Universal route execution engine
     * @dev Delegates all swaps to SwapHandler module (reuses system-wide component)
     * @param inputToken Starting token address
     * @param inputAmount Starting amount
     * @param routeData Encoded route data
     * @return finalAmount Final amount after all swaps
     */
    function _runRoute(
        address inputToken,
        uint256 inputAmount,
        bytes memory routeData
    ) internal returns (uint256 finalAmount) {
        // Decode route: Arrays of [Protocol, Router, TokenOut, ExtraData]
        (
            uint8[] memory protocols,
            address[] memory routers,
            address[] memory path,
            bytes[] memory extra
        ) = abi.decode(routeData, (uint8[], address[], address[], bytes[]));

        // Validation
        require(protocols.length == routers.length, "Length mismatch: protocols/routers");
        require(protocols.length == path.length, "Length mismatch: protocols/path");
        require(protocols.length == extra.length, "Length mismatch: protocols/extra");
        require(protocols.length > 0, "Empty route");
        require(protocols.length <= 5, "Route too long");

        uint256 currentAmount = inputAmount;
        address currentToken = inputToken;

        // Execute each hop using SwapHandler (system-wide module)
        for (uint256 i = 0; i < protocols.length; i++) {
            require(routers[i] != address(0), "Invalid router");
            require(path[i] != address(0), "Invalid token");
            require(currentAmount > 0, "Zero balance");
            
            // Delegate to SwapHandler._executeSwap (reusing system component)
            currentAmount = _executeSwap(
                protocols[i],
                routers[i],
                currentToken,
                path[i],
                currentAmount,
                extra[i]
            );
            
            require(currentAmount > 0, "Swap returned zero");
            currentToken = path[i];
        }
        
        // Basic sanity check (actual profit validated by flash loan repayment)
        require(
            currentAmount >= inputAmount / MIN_OUTPUT_RATIO,
            "Suspicious loss detected"
        );
        
        return currentAmount;
    }

    /* ========== EMERGENCY FUNCTIONS ========== */
    
    /**
     * @notice Withdraw any token from contract
     */
    function withdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(balance > 0, "No balance");
        IERC20(token).safeTransfer(msg.sender, balance);
    }
    
    /**
     * @notice Withdraw native currency (ETH/MATIC/etc)
     */
    function withdrawNative() external onlyOwner {
        uint256 balance = address(this).balance;
        require(balance > 0, "No balance");
        payable(msg.sender).transfer(balance);
    }
    
    /**
     * @notice Allow contract to receive native currency
     */
    receive() external payable {}
}