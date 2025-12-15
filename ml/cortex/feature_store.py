import pandas as pd
import time
import os
import logging
from datetime import datetime

logger = logging.getLogger("FeatureStore")

class FeatureStore:
    """
    The Memory of the Titan.
    Logs market states, bridge fees, and trade outcomes for training.
    """

    def __init__(self):
        # Use environment variable for data path, with fallback
        self_learning_dir = os.getenv('SELF_LEARNING_DATA_PATH', 'data/self_learning')
        self.DATA_PATH = os.path.join(self_learning_dir, 'history.csv')
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(self.DATA_PATH), exist_ok=True)
        
        # Initialize file if missing
        if not os.path.exists(self.DATA_PATH):
            try:
                df = pd.DataFrame(columns=[
                    "timestamp", "chain_id", "token_symbol", 
                    "dex_price", "bridge_fee_usd", "gas_price_gwei",
                    "volatility_index", "outcome_label" # 1=Profit, 0=Loss
                ])
                df.to_csv(self.DATA_PATH, index=False)
            except Exception as e:
                logger.warning(f"Failed to initialize history CSV at {self.DATA_PATH}: {e}")

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
        try:
            df = pd.DataFrame([new_row])
            df.to_csv(self.DATA_PATH, mode='a', header=False, index=False)
        except Exception as e:
            logger.error(f"Failed to append observation to {self.DATA_PATH}: {e}")

    def update_outcome(self, timestamp, profit_realized):
        """
        Updates the label (The "Y" target) after execution.
        """
        # In production, use a real DB (Postgres/TimescaleDB)
        # This CSV logic is for demonstration/MVP
        df = pd.read_csv(self.DATA_PATH)
        # Find row near timestamp and update label
        # Logic omitted for brevity (requires database ID matching)