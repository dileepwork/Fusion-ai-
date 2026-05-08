"""
session_manager.py — Cookie-based session persistence for Instagram Automation Engine
"""

import os
import pickle
from typing import Optional
from utils import logger
from config import SESSIONS_DIR, INSTAGRAM_URL


class SessionManager:
    """
    Saves and restores Chrome session cookies per account username.

    Cookies are persisted as pickle files in sessions/{username}.pkl.
    If a saved session exists, it is injected into the browser to skip login.
    If the session is expired, the caller must fall back to fresh login.

    Future-ready for:
    - AES-encrypted cookie storage
    - Supabase session column (serialize cookies as JSON string)
    - Redis-backed shared session cache
    """

    def __init__(self, sessions_dir: str = SESSIONS_DIR):
        self.sessions_dir = sessions_dir
        os.makedirs(self.sessions_dir, exist_ok=True)

    def _path(self, username: str) -> str:
        """Return the cookie file path for a given username."""
        safe_name = username.replace("@", "_at_").replace("/", "_")
        return os.path.join(self.sessions_dir, f"{safe_name}.pkl")

    def has_session(self, username: str) -> bool:
        """Check whether a saved session file exists for this account."""
        exists = os.path.exists(self._path(username))
        if exists:
            logger.info(f"[Session] Found saved session for: {username}")
        return exists

    def save(self, driver, username: str) -> None:
        """Serialize and save the current browser cookies to disk."""
        try:
            cookies = driver.get_cookies()
            with open(self._path(username), "wb") as f:
                pickle.dump(cookies, f)
            logger.info(f"[Session] Saved {len(cookies)} cookies for: {username}")
        except Exception as e:
            logger.error(f"[Session] Failed to save session for {username}: {e}")

    def load(self, driver, username: str) -> bool:
        """
        Load saved cookies into the browser.
        Must navigate to the domain BEFORE calling this.
        Returns True if cookies were loaded, False if file missing.
        """
        path = self._path(username)
        if not os.path.exists(path):
            logger.warning(f"[Session] No session file found for: {username}")
            return False

        try:
            # Must be on the Instagram domain for cookies to apply
            if INSTAGRAM_URL not in driver.current_url:
                driver.get(INSTAGRAM_URL)

            with open(path, "rb") as f:
                cookies = pickle.load(f)

            for cookie in cookies:
                # Remove keys that cause Selenium to reject the cookie
                cookie.pop("sameSite", None)
                cookie.pop("expiry", None)
                try:
                    driver.add_cookie(cookie)
                except Exception:
                    pass  # Skip invalid cookies silently

            logger.info(f"[Session] Loaded {len(cookies)} cookies for: {username}")
            return True

        except (pickle.UnpicklingError, EOFError, Exception) as e:
            logger.warning(f"[Session] Failed to load session for {username}: {e}. "
                           "Session file may be corrupt — will re-login.")
            self.delete(username)
            return False

    def delete(self, username: str) -> None:
        """Delete a corrupted or expired session file."""
        path = self._path(username)
        if os.path.exists(path):
            os.remove(path)
            logger.info(f"[Session] Deleted session file for: {username}")

    def __repr__(self) -> str:
        files = os.listdir(self.sessions_dir)
        return f"<SessionManager sessions_dir='{self.sessions_dir}' files={files}>"
