import logging
from web3 import Web3
from core.config import DEX_ROUTERS, CHAINS

# Setup Logging
logger = logging.getLogger("DexPricer")

# === ABIS ===
# Uniswap V2 / Sushi / QuickSwap (getAmountsOut)
UNIV2_ABI = '[{"inputs":[{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"address[]","name":"path","type":"address[]"}],"name":"getAmountsOut","outputs":[{"internalType":"uint256[]","name":"amounts","type":"uint256[]"}],"stateMutability":"view","type":"function"}]'

# Uniswap V3 Quoter (quoteExactInputSingle)
UNIV3_ABI = '[{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct IQuoterV2.QuoteExactInputSingleParams","name":"params","type":"tuple"}],"name":"quoteExactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceX96After","type":"uint160"},{"internalType":"uint32","name":"initializedTicksCrossed","type":"uint32"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]'

# Curve (get_dy and coins)
CURVE_ABI = '[{"stateMutability":"view","type":"function","name":"get_dy","inputs":[{"name":"i","type":"int128"},{"name":"j","type":"int128"},{"name":"dx","type":"uint256"}],"outputs":[{"name":"","type":"uint256"}]},{"stateMutability":"view","type":"function","name":"coins","inputs":[{"name":"arg0","type":"uint256"}],"outputs":[{"name":"","type":"address"}]}]'

# Maximum number of coins to check in a Curve pool (most pools have 2-4 coins)
MAX_CURVE_COINS = 8

class DexPricer:
    def __init__(self, w3: Web3, chain_id: int):
        self.w3 = w3
        self.chain_id = chain_id
        self.config = CHAINS.get(chain_id)
        self._pool_coins_cache = {}
    
    def _get_pool_coins(self, pool_address: str) -> dict:
        """
        Queries the Curve pool to find all coin addresses and their indices.
        Cached to avoid repeated RPC calls.
        
        Returns:
            dict: {token_address_lowercase: index}
        """
        # Check cache first
        pool_address_lower = pool_address.lower()
        if pool_address_lower in self._pool_coins_cache:
            return self._pool_coins_cache[pool_address_lower]
        
        try:
            pool = self.w3.eth.contract(
                address=Web3.to_checksum_address(pool_address),
                abi=CURVE_ABI
            )
            
            coin_map = {}
            
            for i in range(MAX_CURVE_COINS):
                try:
                    # Add timeout to prevent hanging on slow RPC
                    coin_addr = pool.functions.coins(i).call(block_identifier='latest')
                    coin_map[coin_addr.lower()] = i
                    logger.debug(f"Pool {pool_address[:8]}: coins({i}) = {coin_addr}")
                except Exception as e:
                    # Pool has no more coins at this index (expected behavior)
                    logger.debug(f"No coin at index {i} for pool {pool_address[:8]}: {e}")
                    break
            
            if len(coin_map) < 2:
                logger.warning(f"Pool {pool_address} has insufficient coins: {len(coin_map)}")
                return {}
            
            logger.info(f"✅ Mapped {len(coin_map)} coins for pool {pool_address[:8]}")
            
            # Cache the result
            self._pool_coins_cache[pool_address_lower] = coin_map
            return coin_map
            
        except Exception as e:
            logger.error(f"Failed to query pool coins: {e}")
            return {}

    def get_curve_indices(self, pool_address: str, token_in: str, token_out: str) -> tuple:
        """
        Dynamically resolves the correct Curve indices for a token pair.
        
        Args:
            pool_address: Curve pool contract address
            token_in: Address of token being sold
            token_out: Address of token being bought
        
        Returns:
            tuple: (i, j) or (None, None) if tokens not found
        """
        # Normalize addresses
        token_in = token_in.lower()
        token_out = token_out.lower()
        pool_address = pool_address.lower()
        
        # Get coin mapping
        coin_map = self._get_pool_coins(pool_address)
        
        if not coin_map:
            logger.error(f"Could not map coins for pool {pool_address[:8]}")
            return (None, None)
        
        # Find indices
        idx_in = coin_map.get(token_in)
        idx_out = coin_map.get(token_out)
        
        if idx_in is None:
            logger.error(f"Token {token_in[:8]} not found in pool")
            logger.error(f"Available coins: {list(coin_map.keys())}")
            return (None, None)
        
        if idx_out is None:
            logger.error(f"Token {token_out[:8]} not found in pool")
            return (None, None)
        
        if idx_in == idx_out:
            logger.error(f"Cannot swap token to itself")
            return (None, None)
        
        logger.debug(f"Resolved: {token_in[:8]} (i={idx_in}) → {token_out[:8]} (j={idx_out})")
        return (idx_in, idx_out)

    def get_univ3_price(self, token_in, token_out, amount, fee=500):
        """
        Queries Uniswap V3 Quoter with improved error handling.
        
        Args:
            token_in: Input token address
            token_out: Output token address
            amount: Input amount in wei
            fee: Pool fee tier (500, 3000, or 10000)
            
        Returns:
            int: Output amount in wei, or 0 if query fails
            
        Note: Returns 0 for both "no liquidity" and "RPC error" cases.
              Check logs to distinguish between failure modes.
        """
        quoter_addr = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e" 
        
        try:
            contract = self.w3.eth.contract(address=quoter_addr, abi=UNIV3_ABI)
            quote = contract.functions.quoteExactInputSingle(
                (token_in, token_out, int(amount), fee, 0)
            ).call(block_identifier='latest')
            return quote[0]
        except ValueError as e:
            # Contract revert - typically means insufficient liquidity
            logger.debug(f"UniV3 quote reverted (likely no liquidity): {e}")
            return 0
        except TimeoutError:
            logger.warning(f"UniV3 quote timeout for {token_in[:8]} -> {token_out[:8]}")
            return 0
        except Exception as e:
            logger.error(f"UniV3 quote failed: {e}")
            return 0

    def get_curve_price(self, pool_address, token_in=None, token_out=None, amount=None, i=None, j=None):
        """
        Queries Curve Pool for price quote with improved error handling.
        Supports two modes:
        1. New mode: Pass token_in, token_out addresses (automatically resolves indices)
        2. Legacy mode: Pass i, j indices directly
        
        Args:
            pool_address: Curve pool contract address
            token_in: Input token address (Mode 1)
            token_out: Output token address (Mode 1)
            amount: Input amount in wei
            i: Input token index (Mode 2, legacy)
            j: Output token index (Mode 2, legacy)
            
        Returns:
            int: Output amount in wei, or 0 if query fails
        """
        try:
            contract = self.w3.eth.contract(address=pool_address, abi=CURVE_ABI)
            
            # Mode 1: Token addresses provided - resolve indices
            if token_in is not None and token_out is not None:
                indices = self.get_curve_indices(pool_address, token_in, token_out)
                if indices[0] is None:
                    logger.debug(f"Could not resolve Curve indices for {token_in} -> {token_out}")
                    return 0
                i, j = indices
            
            # Mode 2: Legacy - indices provided directly
            elif i is None and j is None:
                logger.error("get_curve_price requires either (token_in, token_out) or (i, j)")
                return 0
            
            # Execute the price query
            result = contract.functions.get_dy(i, j, int(amount)).call(block_identifier='latest')
            return result
            
        except ValueError as e:
            # Contract revert - typically means invalid indices or pool state
            logger.debug(f"Curve price query reverted: {e}")
            return 0
        except TimeoutError:
            logger.warning(f"Curve price query timeout for pool {pool_address[:8]}")
            return 0
        except Exception as e:
            logger.error(f"Curve price query failed: {e}")
            return 0

    def get_univ2_price(self, router_key, token_in, token_out, amount):
        """
        Queries UniV2-style DEX routers with improved error handling.
        
        Args:
            router_key: Key in DEX_ROUTERS config (e.g., 'QUICKSWAP', 'SUSHI')
            token_in: Input token address
            token_out: Output token address
            amount: Input amount in wei
            
        Returns:
            int: Output amount in wei, or 0 if query fails
        """
        router_addr = DEX_ROUTERS.get(self.chain_id, {}).get(router_key)
        if not router_addr:
            logger.debug(f"Router {router_key} not configured for chain {self.chain_id}")
            return 0
        
        try:
            contract = self.w3.eth.contract(address=router_addr, abi=UNIV2_ABI)
            amounts = contract.functions.getAmountsOut(
                int(amount), 
                [token_in, token_out]
            ).call(block_identifier='latest')
            return amounts[-1]
        except ValueError as e:
            # Contract revert - typically means insufficient liquidity
            logger.debug(f"{router_key} quote reverted: {e}")
            return 0
        except TimeoutError:
            logger.warning(f"{router_key} quote timeout")
            return 0
        except Exception as e:
            logger.error(f"{router_key} quote failed: {e}")
            return 0

    def find_best_price(self, token_in, token_out, amount):
        """Scans all DEXs - KEEP AS-IS"""
        results = {}
        
        v3_out = self.get_univ3_price(token_in, token_out, amount)
        results['UNIV3'] = v3_out

        if self.chain_id == 137:
            results['QUICKSWAP'] = self.get_univ2_price('QUICKSWAP', token_in, token_out, amount)
            results['SUSHI'] = self.get_univ2_price('SUSHI', token_in, token_out, amount)
            results['APE'] = self.get_univ2_price('APE', token_in, token_out, amount)

        best_dex = max(results, key=results.get)
        best_amount = results[best_dex]
        
        return {
            "dex": best_dex,
            "amount_out": best_amount,
            "all_quotes": results
        }