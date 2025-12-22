import pandas as pd
import time
import os
from datetime import datetime

class FeatureStore:
    """
    The Memory of the Titan.
    Logs market states, bridge fees, and trade outcomes for training.
    """
    DATA_PATH = "data/history.csv"

    def __init__(self):
        if not os.path.exists("data"):
            os.makedirs("data")
        
        # Initialize file if missing
        if not os.path.exists(self.DATA_PATH):
            df = pd.DataFrame(columns=[
                "timestamp", "chain_id", "token_symbol", 
                "dex_price", "bridge_fee_usd", "gas_price_gwei",
                "volatility_index", "outcome_label" # 1=Profit, 0=Loss
            ])
            df.to_csv(self.DATA_PATH, index=False)

    def log_observation(self, chain_id, token, price, fee, gas, vol):
        """
        Saves a market snapshot (The "X" features).
        """
        new_row = {
            "timestamp": time.time(),
            "chain_id": chain_id,
            "token_symbol": token,
            "dex_price": price,
            "bridge_fee_usd": fee,
            "gas_price_gwei": gas,
            "volatility_index": vol,
            "outcome_label": None # Unknown yet
        }
        
        # Append efficiently
        df = pd.DataFrame([new_row])
        df.to_csv(self.DATA_PATH, mode='a', header=False, index=False)

    def update_outcome(self, timestamp, profit_realized):
        """
        Updates the label (The "Y" target) after execution.
        """
        # In production, use a real DB (Postgres/TimescaleDB)
        # This CSV logic is for demonstration/MVP
        df = pd.read_csv(self.DATA_PATH)
        # Find row near timestamp and update label
        # Logic omitted for brevity (requires database ID matching)