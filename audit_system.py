import os
import sys
from colorama import Fore, Style, init

init(autoreset=True)

REQUIRED_FILES = [
    ".env",
    "package.json",
    "requirements.txt",
    "core/config.py",
    "core/enum_matrix.py",
    "core/token_discovery.py",
    "core/token_equivalence.py",
    "ml/brain.py",
    "ml/bridge_oracle.py",
    "ml/cortex/feature_store.py",
    "ml/cortex/forecaster.py",
    "ml/cortex/rl_optimizer.py",
    "execution/bot.js",
    "execution/lifi_discovery.js",
    "execution/lifi_manager.js",
    "execution/gas_manager.js", # The new file
    "contracts/OmniArbExecutor.sol"
]

def audit():
    print(f"{Fore.CYAN}==================================")
    print(f"   APEX-OMEGA TITAN: FINAL AUDIT  ")
    print(f"=================================={Style.RESET_ALL}")
    
    missing = []
    
    # 1. File Integrity Check
    print(f"\n{Fore.YELLOW}[1] Checking File System...{Style.RESET_ALL}")
    for file_path in REQUIRED_FILES:
        if os.path.exists(file_path):
            print(f"   ✅ Found: {file_path}")
        else:
            print(f"   ❌ MISSING: {file_path}")
            missing.append(file_path)

    # 2. Config Logic Check
    print(f"\n{Fore.YELLOW}[2] Checking Logic Imports...{Style.RESET_ALL}")
    try:
        from core.config import CHAINS, DYNAMIC_REGISTRY
        print(f"   ✅ Config Loaded. Chains Configured: {len(CHAINS)}")
        if DYNAMIC_REGISTRY is None:
             print(f"   ⚠️  Dynamic Registry not built yet (Run lifi_discovery.js first)")
    except Exception as e:
        print(f"   ❌ Config Error: {e}")
        missing.append("Config Logic")

    # 3. Summary
    print(f"\n{Fore.CYAN}==================================")
    if len(missing) == 0:
        print(f"{Fore.GREEN}🚀 AUDIT PASSED. SYSTEM IS INTEGRAL.{Style.RESET_ALL}")
        print("You are ready to run 'start_titan_full.bat'")
    else:
        print(f"{Fore.RED}🛑 AUDIT FAILED. FIX MISSING FILES.{Style.RESET_ALL}")

if __name__ == "__main__":
    audit()