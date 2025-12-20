import requests
import json
from web3 import Web3

class TokenLoader:
    # 1inch Token Registry (Aggregates standard tokens across chains)
    URL = "https://tokens.1inch.io/v1.1"

    @staticmethod
    def get_tokens(chain_id):
        """
        Dynamically fetches top 100+ tokens for a chain. No hardcoding.
        """
        print(f"📥 Fetching tokens for Chain {chain_id}...")
        try:
            res = requests.get(f"{TokenLoader.URL}/{chain_id}")
            data = res.json()
            
            # Convert dict to clean list [ {symbol, address, decimals} ]
            # Convert all addresses to checksum format
            tokens = []
            for addr, details in data.items():
                try:
                    checksum_addr = Web3.to_checksum_address(addr)
                    tokens.append({
                        "symbol": details['symbol'],
                        "address": checksum_addr,
                        "decimals": details['decimals']
                    })
                except Exception:
                    # Skip invalid addresses
                    continue
            
            print(f"   ✅ Loaded {len(tokens)} tokens.")
            return tokens
        except Exception as e:
            print(f"   ❌ Failed to load tokens: {e}")
            return []