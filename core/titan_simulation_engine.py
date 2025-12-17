import json
import os
import logging
from web3 import Web3
from dotenv import load_dotenv
from core.config import CHAINS, BALANCER_V3_VAULT
from core.chain_registry import get_chain_registry

load_dotenv()
logger = logging.getLogger("SimulationEngine")

# Minimum ABI for ERC20 Balance checking
ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

# Uniswap V3 Quoter V2 ABI (Minimal)
QUOTER_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct IQuoterV2.QuoteExactInputSingleParams","name":"params","type":"tuple"}],"name":"quoteExactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceX96After","type":"uint160"},{"internalType":"uint32","name":"initializedTicksCrossed","type":"uint32"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]

class TitanSimulationEngine:
    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.chain_config = CHAINS.get(chain_id)
        self.chain_registry = get_chain_registry()
        
        if not self.chain_config:
            raise ValueError(f"Chain {chain_id} not configured")
        
        # Get RPC URL from chain registry (with validation)
        rpc_url = self.chain_registry.get_rpc_url(chain_id)
        
        if not rpc_url:
            logger.error(
                f"[{self.chain_registry.get_chain_name(chain_id)}] "
                f"No RPC URL configured - check .env file"
            )
            raise ValueError(f"No RPC configured for chain {chain_id}")
        
        # Initialize Web3 Connection
        try:
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            if not self.w3.is_connected():
                logger.error(
                    f"[{self.chain_registry.get_chain_name(chain_id)}] "
                    f"Could not connect to RPC: {rpc_url}"
                )
                raise ConnectionError(f"RPC connection failed for chain {chain_id}")
            
            # Log successful connection
            block_number = self.w3.eth.block_number
            logger.info(
                f"[{self.chain_registry.get_chain_name(chain_id)}] "
                f"RPC connected - block #{block_number}"
            )
            
        except Exception as e:
            logger.error(
                f"[{self.chain_registry.get_chain_name(chain_id)}] "
                f"RPC initialization failed: {e}"
            )
            raise

    def get_lender_tvl(self, token_address, protocol="BALANCER"):
        """
        Checks how deep the lender's pockets are.
        Returns: Total Available Liquidity (int, raw units)
        """
        chain_name = self.chain_registry.get_chain_name(self.chain_id)
        
        # Determine Lender Address
        lender_address = None
        if protocol == "BALANCER":
            lender_address = BALANCER_V3_VAULT
        elif protocol == "AAVE":
            lender_address = self.chain_config['aave_pool']

        if not lender_address:
            logger.warning(f"[{chain_name}] No lender address for protocol {protocol}")
            return 0

        # Query Balance
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            balance = token_contract.functions.balanceOf(lender_address).call()
            
            logger.debug(
                f"[{chain_name}] TVL check: {protocol} has {balance} units of {token_address}"
            )
            
            return balance
        except Exception as e:
            logger.error(
                f"[{chain_name}] TVL check failed for {token_address} on {protocol}: {e}"
            )
            return 0

    def get_price_impact(self, token_in, token_out, amount, fee=500):
        """
        Simulates a swap on Uniswap V3 to calculate output.
        Returns: estimated_output (int)
        """
        # Address of QuoterV2 (Standard deployment on most chains, check specific chain ID in prod)
        # Using Arbitrum Quoter as default example
        quoter_addr = "0x61fFE014bA17989E743c5F6cB21bF9697530B21e" 
        
        try:
            quoter = self.w3.eth.contract(address=quoter_addr, abi=QUOTER_ABI)
            
            # params: tokenIn, tokenOut, amountIn, fee, sqrtPriceLimitX96
            call_params = (token_in, token_out, int(amount), fee, 0)
            
            # Simulate call (Static Call)
            quote = quoter.functions.quoteExactInputSingle(call_params).call()
            amount_out = quote[0]
            
            return amount_out
        except Exception as e:
            # If simulation reverts (e.g., price impact too high), return 0
            return 0


# Standalone function for backward compatibility and convenience
def get_provider_tvl(token_address, lender_address=None, chain_id=137):
    """
    Standalone function to check provider liquidity.
    Used by TitanCommander for liquidity validation.
    
    Args:
        token_address (str): ERC20 token address to check
        lender_address (str): Unused parameter for backward compatibility
        chain_id (int): Chain ID (default: 137 for Polygon)
        
    Returns:
        int: Available liquidity in raw token units (smallest token unit)
    """
    try:
        engine = TitanSimulationEngine(chain_id)
        return engine.get_lender_tvl(token_address, protocol="BALANCER")
    except Exception as e:
        logger.error(f"get_provider_tvl failed for chain {chain_id}: {e}")
        return 0