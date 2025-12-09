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
CURVE_ABI = '''[
    {
        "stateMutability":"view",
        "type":"function",
        "name":"get_dy",
        "inputs":[
            {"name":"i","type":"int128"},
            {"name":"j","type":"int128"},
            {"name":"dx","type":"uint256"}
        ],
        "outputs":[{"name":"","type":"uint256"}]
    },
    {
        "stateMutability":"view",
        "type":"function",
        "name":"coins",
        "inputs":[{"name":"arg0","type":"uint256"}],
        "outputs":[{"name":"","type":"address"}]
    }
]'''

# Curve pools typically have 2-8 coins
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
                    coin_addr = pool.functions.coins(i).call()
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

    def get_curve_price(self, pool_address, token_in, token_out, amount):
        """
        Queries Curve pool with DYNAMIC index resolution.
        
        MODIFIED: Now takes token addresses instead of indices
        
        Args:
            pool_address: Curve pool address
            token_in: Input token address (was 'i')
            token_out: Output token address (was 'j')
            amount: Input amount in wei
        
        Returns:
            int: Output amount in wei, or 0 if query fails
        """
        try:
            # Get the correct indices dynamically
            i, j = self.get_curve_indices(pool_address, token_in, token_out)
            
            if i is None or j is None:
                logger.warning(f"Could not resolve Curve indices")
                return 0
            
            # Query the pool with correct indices
            pool = self.w3.eth.contract(
                address=Web3.to_checksum_address(pool_address),
                abi=CURVE_ABI
            )
            
            output_amount = pool.functions.get_dy(i, j, int(amount)).call()
            
            logger.debug(f"Curve quote: {amount} → {output_amount} (i={i}, j={j})")
            return output_amount
            
        except Exception as e:
            logger.error(f"Curve price query failed: {e}")
            return 0

    def get_univ3_price(self, token_in, token_out, amount, fee=500):
        """Queries Uniswap V3 Quoter - KEEP AS-IS"""
        quoter_addr = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e" 
        
        try:
            contract = self.w3.eth.contract(address=quoter_addr, abi=UNIV3_ABI)
            quote = contract.functions.quoteExactInputSingle(
                (token_in, token_out, int(amount), fee, 0)
            ).call()
            return quote[0]
        except Exception as e:
            return 0

    def get_univ2_price(self, router_key, token_in, token_out, amount):
        """Queries UniV2 Forks - KEEP AS-IS"""
        router_addr = DEX_ROUTERS.get(router_key)
        if not router_addr: return 0
        
        try:
            contract = self.w3.eth.contract(address=router_addr, abi=UNIV2_ABI)
            amounts = contract.functions.getAmountsOut(int(amount), [token_in, token_out]).call()
            return amounts[-1]
        except Exception:
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