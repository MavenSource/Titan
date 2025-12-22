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
contract OmniArbExecutor is Ownable, SwapHandler, IAaveFlashLoanSimpleReceiver {
    using SafeERC20 for IERC20;

    // ============================================
    // ENUMS
    // ============================================

    /**
     * @notice Flash loan source providers
     */
    enum FlashSource {
        AaveV3,       // 0: Aave V3 flashLoanSimple
        BalancerV3    // 1: Balancer V3 unlock pattern
    }

    /**
     * @notice Route encoding format
     */
    enum RouteEncoding {
        RAW_ADDRESSES,    // 0: Explicit router + token addresses
        REGISTRY_ENUMS    // 1: DEX + Token enums resolved on-chain
    }

    /**
     * @notice DEX identifiers for registry-based routing
     */
    enum Dex {
        UniV2,        // 0: UniswapV2-style (Quickswap, Sushiswap, etc.)
        UniV3,        // 1: Uniswap V3
        Curve,        // 2: Curve pools
        Balancer,     // 3: Balancer
        Dodo,         // 4: Dodo
        Unknown       // 5: Unknown/Other DEX
    }

    /**
     * @notice Token identifiers for registry-based routing
     */
    enum TokenId {
        WNATIVE,      // 0: Wrapped native token (WETH, WMATIC, etc.)
        USDC,         // 1: USD Coin
        USDT,         // 2: Tether USD
        DAI,          // 3: Dai Stablecoin
        WETH,         // 4: Wrapped Ether
        WBTC          // 5: Wrapped Bitcoin
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

    event ExecutedDetailed(
        FlashSource indexed source,
        address indexed asset,
        uint256 amountBorrowed,
        uint256 feeOrPremium,
        uint256 repayAmount,
        uint256 startBalance,
        uint256 endBalance,
        int256 pnl,
        uint256 minProfit,
        bytes32 routeHash
    );

    event DexRouterSet(uint256 indexed chainId, uint8 indexed dexId, address router);
    event TokenSet(uint256 indexed chainId, uint8 indexed tokenId, uint8 indexed tokenType, address token, bool enabled);

    // ============================================
    // CONSTRUCTOR
    // ============================================

    constructor(address _balancer, address _aave) Ownable(msg.sender) {
        require(_balancer != address(0) && _aave != address(0), "Invalid addresses");
        BALANCER_VAULT = IVaultV3(_balancer);
        AAVE_POOL = IAavePool(_aave);
        
        // Initialize chain ID mappings
        _initializeChainMappings();
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
    function setDexRouter(uint256 chainId, uint8 dexId, address router) external onlyOwner {
        require(router != address(0), "Invalid router");
        require(router.code.length > 0, "Router not contract");
        dexRouter[chainId][dexId] = router;
        emit DexRouterSet(chainId, dexId, router);
    }
    
    /**
     * @notice Register a DEX router address for a specific chain
     */
    function setToken(uint256 chainId, uint8 tokenId, uint8 tokenType, address token) external onlyOwner {
        require(token != address(0), "Invalid token");
        require(token.code.length > 0, "Token not contract");
        tokenRegistry[chainId][tokenId][tokenType] = token;
        emit TokenSet(chainId, tokenId, tokenType, token, true);
    }
    
    /**
     * @notice Batch register multiple tokens
     */
    function batchRegisterTokens(
        Chain _chain,
        Token[] calldata _tokens,
        address[] calldata _addresses
    ) external onlyOwner {
        require(chainIds.length == dexIds.length && dexIds.length == routers.length, "Length mismatch");
        for (uint i = 0; i < chainIds.length; i++) {
            require(routers[i] != address(0), "Invalid router");
            require(routers[i].code.length > 0, "Router not contract");
            dexRouter[chainIds[i]][dexIds[i]] = routers[i];
            emit DexRouterSet(chainIds[i], dexIds[i], routers[i]);
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
        require(
            chainIds.length == tokenIds.length && 
            tokenIds.length == tokenTypes.length && 
            tokenTypes.length == tokens.length,
            "Length mismatch"
        );
        for (uint i = 0; i < chainIds.length; i++) {
            require(tokens[i] != address(0), "Invalid token");
            require(tokens[i].code.length > 0, "Token not contract");
            tokenRegistry[chainIds[i]][tokenIds[i]][tokenTypes[i]] = tokens[i];
            emit TokenSet(chainIds[i], tokenIds[i], tokenTypes[i], tokens[i], true);
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
     * @notice Execute arbitrage with flashloan
     * @param flashSource Flash loan source (AaveV3=0, BalancerV3=1)
     * @param loanToken Token to borrow
     * @param loanAmount Amount to borrow
     * @param minProfitToken Minimum profit required in loanToken units
     * @param balancerFeeHint Balancer fee hint (typically 0, but explicit)
     * @param routeData Encoded route (RAW_ADDRESSES or REGISTRY_ENUMS)
     */
    function execute(
        FlashSource flashSource,
        address loanToken,
        uint256 loanAmount,
        uint256 minProfitToken,
        uint256 balancerFeeHint,
        bytes calldata routeData
    ) external onlyOwner {
        if (flashSource == FlashSource.AaveV3) {
            // Aave V3: Standard flashloan - encode minProfit into routeData wrapper
            bytes memory callbackData = abi.encode(minProfitToken, routeData);
            AAVE_POOL.flashLoanSimple(address(this), loanToken, loanAmount, callbackData, 0);
        } else if (flashSource == FlashSource.BalancerV3) {
            // Balancer V3: Unlock pattern
            bytes memory callbackData = abi.encode(loanToken, loanAmount, minProfitToken, balancerFeeHint, routeData);
            BALANCER_VAULT.unlock(abi.encodeCall(this.onBalancerUnlock, (callbackData)));
        } else {
            revert("Invalid flash source");
        }
    }

    /* ========== FLASH LOAN CALLBACKS ========== */
    
    /**
     * @notice Balancer V3 unlock callback
     */
    function onBalancerUnlock(bytes calldata callbackData) external returns (bytes memory) {
        require(msg.sender == address(BALANCER_VAULT), "B3: bad caller");

        (address loanToken, uint256 loanAmount, uint256 minProfitToken, uint256 feeHint, bytes memory routeData) =
            abi.decode(callbackData, (address, uint256, uint256, uint256, bytes));

        // Borrow inside unlocked context
        BALANCER_VAULT.sendTo(IERC20(loanToken), address(this), loanAmount);

        uint256 startBal = IERC20(loanToken).balanceOf(address(this));

        // Execute route
        uint256 finalAmount = _runRoute(loanToken, loanAmount, routeData);

        uint256 endBal = IERC20(loanToken).balanceOf(address(this));

        // Profit calculation: endBal - startBal - feeHint
        int256 pnl = int256(endBal) - int256(startBal) - int256(feeHint);
        require(pnl >= int256(minProfitToken), "MIN_PROFIT");

        // Repay debt: loanAmount + feeHint
        uint256 repayAmount = loanAmount + feeHint;
        require(endBal >= repayAmount, "B3: insufficient repay");

        // Transfer to Vault, then settle (NOT approve)
        IERC20(loanToken).safeTransfer(address(BALANCER_VAULT), repayAmount);
        BALANCER_VAULT.settle(IERC20(loanToken), repayAmount);

        emit ExecutedDetailed(
            FlashSource.BalancerV3,
            loanToken,
            loanAmount,
            feeHint,
            repayAmount,
            startBal,
            endBal,
            pnl,
            minProfitToken,
            keccak256(routeData)
        );

        // RouteExecuted expects uint256 profit, only emit if profitable
        emit RouteExecuted(loanToken, loanAmount, finalAmount, pnl >= 0 ? uint256(pnl) : 0);
        
        return "";
    }

    /**
     * @notice Aave V3 flash loan callback
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external override returns (bool) {
        require(msg.sender == address(AAVE_POOL), "AAVE: bad caller");
        require(initiator == address(this), "AAVE: bad initiator");

        // Decode minProfit and routeData
        (uint256 minProfitToken, bytes memory routeData) = abi.decode(params, (uint256, bytes));
        
        uint256 startBal = IERC20(asset).balanceOf(address(this));
        
        // Execute arbitrage route
        uint256 finalAmount = _runRoute(asset, amount, routeData);

        uint256 endBal = IERC20(asset).balanceOf(address(this));

        uint256 owed = amount + premium;

        // Profit calculation: endBal - startBal - premium
        // Note: startBal already includes borrowed amount
        int256 pnl = int256(endBal) - int256(startBal) - int256(premium);
        require(pnl >= int256(minProfitToken), "MIN_PROFIT");
        
        require(endBal >= owed, "AAVE: insufficient return");
        
        IERC20(asset).safeIncreaseAllowance(address(AAVE_POOL), owed);

        emit ExecutedDetailed(
            FlashSource.AaveV3,
            asset,
            amount,
            premium,
            owed,
            startBal,
            endBal,
            pnl,
            minProfitToken,
            keccak256(routeData)
        );

        // RouteExecuted expects uint256 profit, only emit if profitable
        emit RouteExecuted(asset, amount, finalAmount, pnl >= 0 ? uint256(pnl) : 0);
        
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
            ,  // RouteEncoding enc - not used after decode
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
        
        (
            ,  // RouteEncoding enc - not used after decode
            uint8[] memory protocols,
            uint8[] memory dexIds,
            uint8[] memory tokenOutIds,
            uint8[] memory tokenOutTypes,
            bytes[] memory extra
        ) = abi.decode(routeData, (RouteEncoding, uint8[], uint8[], uint8[], uint8[], bytes[]));

        // Validate lengths
        require(protocols.length == dexIds.length, "len mismatch");
        require(protocols.length == tokenOutIds.length, "len mismatch");
        require(protocols.length == tokenOutTypes.length, "len mismatch");
        require(protocols.length == extra.length, "len mismatch");
        require(protocols.length > 0 && protocols.length <= 5, "Invalid route length");

        uint256 chainId = block.chainid;
        uint256 currentAmount = inputAmount;
        address currentToken = inputToken;

        for (uint i = 0; i < protocols.length; i++) {
            // Resolve router from registry
            address routerOrPool = dexRouter[chainId][dexIds[i]];
            require(routerOrPool != address(0), "Router not registered");

            // Resolve tokenOut from registry
            address tokenOut = tokenRegistry[chainId][tokenOutIds[i]][tokenOutTypes[i]];
            require(tokenOut != address(0), "Token not registered");

            require(currentAmount > 0, "Zero balance");

            currentAmount = _executeSwap(
                protocols[i],
                routerOrPool,
                currentToken,
                tokenOut,
                currentAmount,
                extra[i]
            );

            require(currentAmount > 0, "Swap returned zero");
            currentToken = tokenOut;
        }

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