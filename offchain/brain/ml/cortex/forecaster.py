import numpy as np
import pandas as pd

class MarketForecaster:
    """
    Predicts near-future states to prevent 'Bad Timing' trades.
    """
    
    def __init__(self, history_window=50):
        self.gas_history = []
        self.window = history_window

    def ingest_gas(self, gwei):
        self.gas_history.append(gwei)
        if len(self.gas_history) > self.window:
            self.gas_history.pop(0)

    def predict_gas_trend(self):
        """
        Returns: 'UP', 'DOWN', or 'STABLE'
        Logic: Linear Regression Slope
        """
        if len(self.gas_history) < 10:
            return "STABLE"

        y = np.array(self.gas_history)
        x = np.arange(len(y))
        
        # Calculate slope
        slope, _ = np.polyfit(x, y, 1)
        
        if slope > 0.5: return "RISING_FAST"
        if slope < -0.5: return "DROPPING_FAST"
        return "STABLE"

    def should_wait(self):
        """
        AI Decision: Should we wait 1 block for cheaper gas?
        """
        trend = self.predict_gas_trend()
        if trend == "DROPPING_FAST":
            return True # Wait for the drop
        return False