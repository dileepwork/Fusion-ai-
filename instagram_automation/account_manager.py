"""
account_manager.py — Multi-account loader for Instagram Automation Engine
"""

import json
import os
from typing import List, Dict
from utils import logger
from config import ACCOUNTS_FILE


class AccountManager:
    """
    Loads and manages multiple Instagram accounts from accounts.json.

    Future-ready for:
    - Supabase integration (replace JSON load with DB query)
    - Account status tracking (active/paused/banned)
    - Rotation strategies (round-robin, random, priority)
    """

    def __init__(self, accounts_file: str = ACCOUNTS_FILE):
        self.accounts_file = accounts_file
        self.accounts: List[Dict] = []
        self._load()

    def _load(self) -> None:
        """Load accounts from JSON file."""
        if not os.path.exists(self.accounts_file):
            logger.error(f"Accounts file not found: {self.accounts_file}")
            raise FileNotFoundError(
                f"Create '{self.accounts_file}' with your account list. "
                "See accounts.json.example for format."
            )

        with open(self.accounts_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("accounts.json must be a non-empty JSON array.")

        # Validate required fields
        for idx, acc in enumerate(data):
            if "username" not in acc or "password" not in acc:
                raise ValueError(
                    f"Account #{idx + 1} is missing 'username' or 'password'."
                )

        self.accounts = data
        logger.info(f"Loaded {len(self.accounts)} account(s) from accounts.json")

    def get_all(self) -> List[Dict]:
        """Return the full list of accounts."""
        return self.accounts

    def get_active(self) -> List[Dict]:
        """
        Return only accounts not marked as paused.
        Supports optional 'active' flag in accounts.json.
        """
        return [a for a in self.accounts if a.get("active", True)]

    def get_by_username(self, username: str) -> Dict | None:
        """Find a specific account by username."""
        for acc in self.accounts:
            if acc["username"] == username:
                return acc
        return None

    def count(self) -> int:
        return len(self.accounts)

    def __repr__(self) -> str:
        return f"<AccountManager accounts={[a['username'] for a in self.accounts]}>"
