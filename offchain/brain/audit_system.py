import os
import sys
from pathlib import Path

# Ensure we can import from the current directory structure
sys.path.insert(0, str(Path(__file__).parent))

try:
    from colorama import Fore, Style, init
    init(autoreset=True)
except ImportError:
    # Fallback if colorama not installed
    class Fore:
        CYAN = GREEN = RED = YELLOW = ""
    class Style:
        RESET_ALL = ""

# Paths relative to offchain/brain/
REQUIRED_FILES = [
    "../.env",  # In offchain/ (parent directory)
    "requirements.txt",
    "core/config.py",
    "core/enum_matrix.py",
    "core/token_discovery.py",
    "ml/brain.py",
    "ml/bridge_oracle.py",
    "ml/cortex/feature_store.py",
    "ml/cortex/forecaster.py",
    "ml/cortex/rl_optimizer.py",
    "../executor/execution/bot.js",
    "../executor/execution/lifi_discovery.js",
    "../executor/execution/lifi_manager.js",
    "../executor/execution/gas_manager.js",
    "../../onchain/contracts/OmniArbExecutor.sol"
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
        from core.config import CHAINS
        print(f"   ✅ Config Loaded. Chains Configured: {len(CHAINS)}")
        # Check if SIGNALS_OUTGOING path exists
        from core.config import SIGNALS_OUTGOING
        if SIGNALS_OUTGOING.exists():
            print(f"   ✅ Signals directory exists: {SIGNALS_OUTGOING}")
        else:
            print(f"   ⚠️  Signals directory will be created on first run")
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