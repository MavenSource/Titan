import json
import os
from web3 import Web3
from dotenv import load_dotenv
from core.config import CHAINS, BALANCER_V3_VAULT

load_dotenv()

# Minimum ABI for ERC20 Balance checking
ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"}]

# Uniswap V3 Quoter V2 ABI (Minimal)
QUOTER_ABI = [{"inputs":[{"components":[{"internalType":"address","name":"tokenIn","type":"address"},{"internalType":"address","name":"tokenOut","type":"address"},{"internalType":"uint256","name":"amountIn","type":"uint256"},{"internalType":"uint24","name":"fee","type":"uint24"},{"internalType":"uint160","name":"sqrtPriceLimitX96","type":"uint160"}],"internalType":"struct IQuoterV2.QuoteExactInputSingleParams","name":"params","type":"tuple"}],"name":"quoteExactInputSingle","outputs":[{"internalType":"uint256","name":"amountOut","type":"uint256"},{"internalType":"uint160","name":"sqrtPriceX96After","type":"uint160"},{"internalType":"uint32","name":"initializedTicksCrossed","type":"uint32"},{"internalType":"uint256","name":"gasEstimate","type":"uint256"}],"stateMutability":"nonpayable","type":"function"}]

class TitanSimulationEngine:
    def __init__(self, chain_id):
        self.chain_id = chain_id
        self.chain_config = CHAINS.get(chain_id)
        
        if not self.chain_config:
            raise ValueError(f"Chain {chain_id} not configured")
            
        # Initialize Web3 Connection using configured RPC
        rpc_url = self.chain_config.get('rpc')
        if not rpc_url:
            self.w3 = None
            return
            
        try:
            self.w3 = Web3(Web3.HTTPProvider(
                rpc_url,
                request_kwargs={'timeout': 10}
            ))
            if not self.w3.is_connected():
                self.w3 = None
        except Exception as e:
            self.w3 = None

    def get_lender_tvl(self, token_address, protocol="BALANCER"):
        """
        Checks how deep the lender's pockets are.
        Returns: Total Available Liquidity (int, raw units)
        """
        # Skip TVL checks if Web3 not connected (PAPER mode)
        if not self.w3 or not self.w3.is_connected():
            return 0
            
        # Determine Lender Address
        lender_address = None
        if protocol == "BALANCER":
            lender_address = BALANCER_V3_VAULT
        elif protocol == "AAVE":
            lender_address = self.chain_config['aave_pool'] # Pool address holds funds (or aTokens)
            # Note: For Aave V3, the 'Pool' contract doesn't hold funds directly, 
            # the aToken does. But checking the aToken supply is a safe proxy for this V4 implementation.
            # For exact Aave liquidity, we'd query getReserveData, but let's stick to checking the Vault balance for now.

        if not lender_address:
            return 0

        # Query Balance
        try:
            token_contract = self.w3.eth.contract(address=token_address, abi=ERC20_ABI)
            balance = token_contract.functions.balanceOf(lender_address).call()
            return balance
        except Exception:
            # Silently return 0 in PAPER mode (vault checks optional)
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
    engine = TitanSimulationEngine(chain_id)
    return engine.get_lender_tvl(token_address, protocol="BALANCER")