// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../OmniArbExecutor.sol";

/**
 * @title RegistryInitializer
 * @notice Helper contract to batch-initialize token and DEX registries
 * @dev Deploy this, call initialize functions, then can be discarded
 */
contract RegistryInitializer {
    
    /**
     * @notice Initialize Polygon token registry
     */
    function initPolygonTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Native wrapped
        exec.registerToken(Chain.POLYGON, Token.WMATIC, 0x0d500B1d8E8eF31E21C99d1Db9A6444d3ADf1270);
        exec.registerToken(Chain.POLYGON, Token.WETH, 0x7ceB23fD6bC0adD59E62ac25578270cFf1b9f619);
        
        // Stablecoins (bridged)
        exec.registerToken(Chain.POLYGON, Token.USDC_BRIDGED_POLYGON, 0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174);
        exec.registerToken(Chain.POLYGON, Token.USDT_BRIDGED_POLYGON, 0xc2132D05D31c914a87C6611C10748AEb04B58e8F);
        exec.registerToken(Chain.POLYGON, Token.DAI_BRIDGED_POLYGON, 0x8f3Cf7ad23Cd3CaDbD9735AFf958023239c6A063);
        
        // WBTC
        exec.registerToken(Chain.POLYGON, Token.WBTC_BRIDGED_POLYGON, 0x1BFD67037B42Cf73acF2047067bd4F2C47D9BfD6);
        
        // Other major tokens
        exec.registerToken(Chain.POLYGON, Token.LINK, 0x53E0bca35eC356BD5ddDFebbD1Fc0fD03FaBad39);
        exec.registerToken(Chain.POLYGON, Token.AAVE, 0xD6DF932A45C0f255f85145f286eA0b292B21C90B);
        exec.registerToken(Chain.POLYGON, Token.CRV, 0x172370d5Cd63279eFa6d502DAB29171933a610AF);
        exec.registerToken(Chain.POLYGON, Token.SUSHI, 0x0b3F868E0BE5597D5DB7fEB59E1CADBb0fdDa50a);
    }
    
    /**
     * @notice Initialize Polygon DEX registry
     */
    function initPolygonDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.POLYGON, DEX.QUICKSWAP, 0xa5E0829CaCEd8fFDD4De3c43696c57F7D7A678ff);
        exec.registerDEX(Chain.POLYGON, DEX.SUSHISWAP, 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506);
        exec.registerDEX(Chain.POLYGON, DEX.UNISWAP_V3, 0xE592427A0AEce92De3Edee1F18E0157C05861564);
    }
    
    /**
     * @notice Initialize Ethereum token registry
     */
    function initEthereumTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Native wrapped
        exec.registerToken(Chain.ETHEREUM, Token.WETH, 0xC02aaA39b223FE8D0A0e5C4F27eAD9083C756Cc2);
        
        // Stablecoins
        exec.registerToken(Chain.ETHEREUM, Token.USDC, 0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48);
        exec.registerToken(Chain.ETHEREUM, Token.USDT, 0xdAC17F958D2ee523a2206206994597C13D831ec7);
        exec.registerToken(Chain.ETHEREUM, Token.DAI, 0x6B175474E89094C44Da98b954EedeAC495271d0F);
        exec.registerToken(Chain.ETHEREUM, Token.FRAX, 0x853d955aCEf822Db058eb8505911ED77F175b99e);
        
        // WBTC
        exec.registerToken(Chain.ETHEREUM, Token.WBTC, 0x2260FAC5E5542a773Aa44fBCfeDf7C193bc2C599);
        
        // Other major tokens
        exec.registerToken(Chain.ETHEREUM, Token.LINK, 0x514910771AF9Ca656af840dff83E8264EcF986CA);
        exec.registerToken(Chain.ETHEREUM, Token.AAVE, 0x7Fc66500c84A76Ad7e9c93437bFc5Ac33E2DDaE9);
        exec.registerToken(Chain.ETHEREUM, Token.CRV, 0xD533a949740bb3306d119CC777fa900bA034cd52);
        exec.registerToken(Chain.ETHEREUM, Token.BAL, 0xba100000625a3754423978a60c9317c58a424e3D);
        exec.registerToken(Chain.ETHEREUM, Token.SUSHI, 0x6B3595068778DD592e39A122f4f5a5cF09C90fE2);
    }
    
    /**
     * @notice Initialize Ethereum DEX registry
     */
    function initEthereumDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.ETHEREUM, DEX.UNISWAP_V2, 0x7a250d5630B4cF539739dF2C5dAcb4c659F2488D);
        exec.registerDEX(Chain.ETHEREUM, DEX.UNISWAP_V3, 0xE592427A0AEce92De3Edee1F18E0157C05861564);
        exec.registerDEX(Chain.ETHEREUM, DEX.SUSHISWAP, 0xd9e1cE17f2641f24aE83637ab66a2cca9C378B9F);
    }
    
    /**
     * @notice Initialize Arbitrum token registry
     */
    function initArbitrumTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Wrapped ETH
        exec.registerToken(Chain.ARBITRUM, Token.WETH, 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1);
        
        // Stablecoins (bridged)
        exec.registerToken(Chain.ARBITRUM, Token.USDC_BRIDGED_ARBITRUM, 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8);
        exec.registerToken(Chain.ARBITRUM, Token.USDT_BRIDGED_ARBITRUM, 0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9);
        exec.registerToken(Chain.ARBITRUM, Token.DAI_BRIDGED_ARBITRUM, 0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1);
        
        // WBTC
        exec.registerToken(Chain.ARBITRUM, Token.WBTC_BRIDGED_ARBITRUM, 0x2f2a2543B76A4166549F7aaB2e75Bef0aefC5B0f);
        
        // Other tokens
        exec.registerToken(Chain.ARBITRUM, Token.LINK, 0xf97f4df75117a78c1A5a0DBb814Af92458539FB4);
        exec.registerToken(Chain.ARBITRUM, Token.AAVE, 0xba5DdD1f9d7F570dc94a51479a000E3BCE967196);
    }
    
    /**
     * @notice Initialize Arbitrum DEX registry
     */
    function initArbitrumDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.ARBITRUM, DEX.UNISWAP_V3, 0xE592427A0AEce92De3Edee1F18E0157C05861564);
        exec.registerDEX(Chain.ARBITRUM, DEX.SUSHISWAP, 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506);
    }
    
    /**
     * @notice Initialize Optimism token registry
     */
    function initOptimismTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Wrapped ETH
        exec.registerToken(Chain.OPTIMISM, Token.WETH, 0x4200000000000000000000000000000000000006);
        
        // Stablecoins (bridged)
        exec.registerToken(Chain.OPTIMISM, Token.USDC_BRIDGED_OPTIMISM, 0x7F5c764cBc14f9669B88837ca1490cCa17c31607);
        exec.registerToken(Chain.OPTIMISM, Token.USDT_BRIDGED_OPTIMISM, 0x94b008aA00579c1307B0EF2c499aD98a8ce58e58);
        exec.registerToken(Chain.OPTIMISM, Token.DAI_BRIDGED_OPTIMISM, 0xDA10009cBd5D07dd0CeCc66161FC93D7c9000da1);
        
        // Other tokens
        exec.registerToken(Chain.OPTIMISM, Token.LINK, 0x350a791Bfc2C21F9Ed5d10980Dad2e2638ffa7f6);
    }
    
    /**
     * @notice Initialize Optimism DEX registry
     */
    function initOptimismDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.OPTIMISM, DEX.UNISWAP_V3, 0xE592427A0AEce92De3Edee1F18E0157C05861564);
        exec.registerDEX(Chain.OPTIMISM, DEX.VELODROME, 0x9c12939390052919aF3155f41Bf4160Fd3666A6f);
    }
    
    /**
     * @notice Initialize Base token registry
     */
    function initBaseTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Wrapped ETH
        exec.registerToken(Chain.BASE, Token.WETH, 0x4200000000000000000000000000000000000006);
        
        // Stablecoins (native)
        exec.registerToken(Chain.BASE, Token.USDC_BRIDGED_BASE, 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913);
    }
    
    /**
     * @notice Initialize Base DEX registry
     */
    function initBaseDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.BASE, DEX.UNISWAP_V3, 0x2626664c2603336E57B271c5C0b26F421741e481);
        exec.registerDEX(Chain.BASE, DEX.AERODROME, 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43);
    }
    
    /**
     * @notice Initialize BSC token registry
     */
    function initBSCTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Wrapped BNB
        exec.registerToken(Chain.BSC, Token.WBNB, 0xbb4CdB9CBd36B01bD1cBaEBF2De08d9173bc095c);
        
        // Stablecoins
        exec.registerToken(Chain.BSC, Token.USDC, 0x8AC76a51cc950d9822D68b83fE1Ad97B32Cd580d);
        exec.registerToken(Chain.BSC, Token.USDT, 0x55d398326f99059fF775485246999027B3197955);
        exec.registerToken(Chain.BSC, Token.DAI, 0x1AF3F329e8BE154074D8769D1FFa4eE058B1DBc3);
    }
    
    /**
     * @notice Initialize BSC DEX registry
     */
    function initBSCDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.BSC, DEX.PANCAKESWAP, 0x10ED43C718714eb63d5aA57B78B54704E256024E);
        exec.registerDEX(Chain.BSC, DEX.SUSHISWAP, 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506);
    }
    
    /**
     * @notice Initialize Avalanche token registry
     */
    function initAvalancheTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Wrapped AVAX
        exec.registerToken(Chain.AVALANCHE, Token.WAVAX, 0xB31f66AA3C1e785363F0875A1B74E27b85FD66c7);
        
        // Stablecoins
        exec.registerToken(Chain.AVALANCHE, Token.USDC, 0xB97EF9Ef8734C71904D8002F8b6Bc66Dd9c48a6E);
        exec.registerToken(Chain.AVALANCHE, Token.USDT, 0x9702230A8Ea53601f5cD2dc00fDBc13d4dF4A8c7);
        exec.registerToken(Chain.AVALANCHE, Token.DAI, 0xd586E7F844cEa2F87f50152665BCbc2C279D8d70);
        
        // Wrapped ETH (bridged)
        exec.registerToken(Chain.AVALANCHE, Token.WETH_BRIDGED_AVALANCHE, 0x49D5c2BdFfac6CE2BFdB6640F4F80f226bc10bAB);
    }
    
    /**
     * @notice Initialize Avalanche DEX registry
     */
    function initAvalancheDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.AVALANCHE, DEX.TRADER_JOE, 0x60aE616a2155Ee3d9A68541Ba4544862310933d4);
        exec.registerDEX(Chain.AVALANCHE, DEX.SUSHISWAP, 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506);
    }
    
    /**
     * @notice Initialize Fantom token registry
     */
    function initFantomTokens(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        // Wrapped FTM
        exec.registerToken(Chain.FANTOM, Token.WFTM, 0x21be370D5312f44cB42ce377BC9b8a0cEF1A4C83);
        
        // Stablecoins
        exec.registerToken(Chain.FANTOM, Token.USDC, 0x04068DA6C83AFCFA0e13ba15A6696662335D5B75);
        exec.registerToken(Chain.FANTOM, Token.DAI, 0x8D11eC38a3EB5E956B052f67Da8Bdc9bef8Abf3E);
    }
    
    /**
     * @notice Initialize Fantom DEX registry
     */
    function initFantomDEXs(address executor) external {
        OmniArbExecutor exec = OmniArbExecutor(payable(executor));
        
        exec.registerDEX(Chain.FANTOM, DEX.SPOOKYSWAP, 0xF491e7B69E4244ad4002BC14e878a34207E38c29);
        exec.registerDEX(Chain.FANTOM, DEX.SUSHISWAP, 0x1b02dA8Cb0d097eB8D57A175b88c7D8b47997506);
    }
}
