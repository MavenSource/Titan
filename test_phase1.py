from web3 import Web3
from core.enum_matrix import ChainManager
from core.config import CHAINS
import colorama
from colorama import Fore, Style

colorama.init(autoreset=True)

def verify_matrix():
    print(f"{Fore.CYAN}========================================")
    print(f"{Fore.CYAN}   APEX-OMEGA PHASE 1: NETWORK CHECK    ")
    print(f"{Fore.CYAN}========================================{Style.RESET_ALL}\n")

    success_count = 0
    fail_count = 0

    for chain_id in CHAINS.keys():
        try:
            # 1. Get Config
            details = ChainManager.get_connection_details(chain_id)
            name = details['name'].upper()
            
            # 2. Attempt Connection
            print(f"📡 Connecting to {name}...", end=" ")
            w3 = Web3(Web3.HTTPProvider(details['rpc']))
            
            if w3.is_connected():
                # 3. Fetch Live Data (Block Number) to prove it's real
                block = w3.eth.block_number
                print(f"{Fore.GREEN}✅ ONLINE | Block: {block}")
                success_count += 1
            else:
                print(f"{Fore.RED}❌ FAILED (Connection Refused)")
                fail_count += 1
                
        except Exception as e:
            print(f"{Fore.RED}❌ ERROR: {e}")
            fail_count += 1

    print(f"\n{Fore.YELLOW}----------------------------------------")
    print(f"Summary: {success_count}/{len(CHAINS)} Chains Operational")
    print(f"{Fore.YELLOW}----------------------------------------")

    if fail_count == 0:
        print(f"{Fore.GREEN}🚀 PHASE 1 COMPLETE. SYSTEM READY FOR ASSET INGESTION.")
    else:
        print(f"{Fore.RED}⚠️  FIX BROKEN RPCs BEFORE PROCEEDING.")

if __name__ == "__main__":
    verify_matrix()