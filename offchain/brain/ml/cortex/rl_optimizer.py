import random
import json
import os

class QLearningAgent:
    """
    Reinforcement Learning Agent that tunes execution parameters.
    State: (Chain, Volatility)
    Action: (Slippage Tolerance, Priority Fee)
    Reward: Profit - GasCost (or -penalty if reverted)
    """
    
    Q_TABLE_PATH = "data/q_table.json"

    def __init__(self):
        self.q_table = self.load_q_table()
        self.learning_rate = 0.1
        self.discount_factor = 0.95
        self.epsilon = 0.1 # Exploration rate

    def load_q_table(self):
        if os.path.exists(self.Q_TABLE_PATH):
            with open(self.Q_TABLE_PATH, 'r') as f:
                return json.load(f)
        return {}

    def get_state_key(self, chain_id, volatility_level):
        return f"{chain_id}_{volatility_level}"

    def recommend_parameters(self, chain_id, volatility_level):
        """
        Returns optimal {slippage_bps, priority_fee}
        """
        state = self.get_state_key(chain_id, volatility_level)
        
        # Explore (Try new settings 10% of time)
        if random.random() < self.epsilon or state not in self.q_table:
            return {
                "slippage": random.choice([10, 50, 100]), # 0.1%, 0.5%, 1.0%
                "priority": random.choice([30, 50, 100])  # Gwei
            }
        
        # Exploit (Use best known settings)
        best_action = max(self.q_table[state], key=self.q_table[state].get)
        # Parse action string "50_50" -> dict
        s, p = best_action.split("_")
        return {"slippage": int(s), "priority": int(p)}

    def learn(self, chain_id, volatility, action_taken, reward):
        """
        Updates the Q-Table based on trade outcome.
        Reward = +Profit USD or -GasSpent USD
        """
        state = self.get_state_key(chain_id, volatility)
        action_key = f"{action_taken['slippage']}_{action_taken['priority']}"
        
        # Initialize state if new
        if state not in self.q_table:
            self.q_table[state] = {}
        if action_key not in self.q_table[state]:
            self.q_table[state][action_key] = 0.0

        # Q-Learning Formula
        old_value = self.q_table[state][action_key]
        next_max = max(self.q_table[state].values()) if self.q_table[state] else 0
        
        new_value = old_value + self.learning_rate * (reward + self.discount_factor * next_max - old_value)
        self.q_table[state][action_key] = new_value
        
        # Save
        with open(self.Q_TABLE_PATH, 'w') as f:
            json.dump(self.q_table, f)