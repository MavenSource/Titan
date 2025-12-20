import sys
print("Python starting...", flush=True)

try:
    print("Importing OmniBrain...", flush=True)
    from ml.brain import OmniBrain
    print("✅ Import successful", flush=True)
    
    print("Creating brain instance...", flush=True)
    brain = OmniBrain()
    print("✅ Brain created", flush=True)
    
    print("Initializing brain...", flush=True)
    brain.initialize()
    print("✅ Brain initialized", flush=True)
    
except Exception as e:
    print(f"❌ Error: {e}", flush=True)
    import traceback
    traceback.print_exc()
    sys.exit(1)
