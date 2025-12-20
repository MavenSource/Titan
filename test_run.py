"""Test script to show live output"""
import sys
import time

print("=" * 70, flush=True)
print("  STARTING TITAN BRAIN TEST", flush=True)
print("=" * 70, flush=True)
print(flush=True)

for i in range(5):
    print(f"[{i+1}/5] Initializing system component {i+1}...", flush=True)
    time.sleep(1)

print(flush=True)
print("System test complete. Now starting actual Brain...", flush=True)
print(flush=True)

# Import and run the real system
from mainnet_orchestrator import MainnetOrchestrator

orchestrator = MainnetOrchestrator()
orchestrator.run()
