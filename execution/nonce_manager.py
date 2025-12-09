"""
Nonce Manager - Prevents transaction conflicts with concurrent execution
Manages nonce tracking and allocation for multiple simultaneous transactions
"""
import threading
from typing import Dict
from web3 import Web3

class NonceManager:
    """
    Thread-safe nonce management for concurrent transaction execution
    """
    
    def __init__(self):
        self.nonce_cache: Dict[str, int] = {}
        self.pending_nonces: Dict[str, set] = {}
        self.lock = threading.Lock()
    
    def get_next_nonce(self, w3: Web3, address: str) -> int:
        """
        Get the next available nonce for an address
        
        Args:
            w3: Web3 instance
            address: Ethereum address
            
        Returns:
            int: Next available nonce
        """
        with self.lock:
            # Normalize address
            address = Web3.to_checksum_address(address)
            
            # Get on-chain nonce
            chain_nonce = w3.eth.get_transaction_count(address, 'pending')
            
            # Initialize if first time seeing this address
            if address not in self.nonce_cache:
                self.nonce_cache[address] = chain_nonce
                self.pending_nonces[address] = set()
            
            # Use the maximum of cached nonce and chain nonce
            current_nonce = max(self.nonce_cache[address], chain_nonce)
            
            # Find next available nonce that's not pending
            while current_nonce in self.pending_nonces[address]:
                current_nonce += 1
            
            # Mark this nonce as pending
            self.pending_nonces[address].add(current_nonce)
            
            # Update cache
            self.nonce_cache[address] = current_nonce + 1
            
            return current_nonce
    
    def mark_nonce_used(self, address: str, nonce: int):
        """
        Mark a nonce as successfully used (transaction confirmed)
        
        Args:
            address: Ethereum address
            nonce: Nonce that was used
        """
        with self.lock:
            address = Web3.to_checksum_address(address)
            if address in self.pending_nonces:
                self.pending_nonces[address].discard(nonce)
    
    def release_nonce(self, address: str, nonce: int):
        """
        Release a nonce that failed (transaction reverted or not sent)
        Allows it to be reused
        
        Args:
            address: Ethereum address
            nonce: Nonce to release
        """
        with self.lock:
            address = Web3.to_checksum_address(address)
            if address in self.pending_nonces:
                self.pending_nonces[address].discard(nonce)
            
            # Reset cache if this was a future nonce
            if address in self.nonce_cache and nonce < self.nonce_cache[address]:
                self.nonce_cache[address] = nonce
    
    def reset_address(self, w3: Web3, address: str):
        """
        Reset nonce tracking for an address (sync with chain state)
        
        Args:
            w3: Web3 instance
            address: Ethereum address to reset
        """
        with self.lock:
            address = Web3.to_checksum_address(address)
            chain_nonce = w3.eth.get_transaction_count(address, 'pending')
            self.nonce_cache[address] = chain_nonce
            self.pending_nonces[address] = set()
    
    def get_pending_count(self, address: str) -> int:
        """
        Get number of pending transactions for an address
        
        Args:
            address: Ethereum address
            
        Returns:
            int: Number of pending transactions
        """
        with self.lock:
            address = Web3.to_checksum_address(address)
            return len(self.pending_nonces.get(address, set()))
