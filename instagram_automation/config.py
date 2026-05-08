"""
config.py — Central Configuration for Instagram Automation Engine
"""

import random
import time
import os

# ── Browser Settings ─────────────────────────────────────────────────────────
HEADLESS = False          # Set True for server/CI environments
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 800

# ── Human-Like Timing (seconds) ──────────────────────────────────────────────
DELAY_MIN = 3             # Minimum delay between actions
DELAY_MAX = 7             # Maximum delay between actions
TYPE_DELAY_MIN = 0.05     # Min delay between keystrokes
TYPE_DELAY_MAX = 0.18     # Max delay between keystrokes
PAGE_LOAD_WAIT = 8        # Seconds to wait for page loads
POST_WAIT = 15            # Seconds to wait after posting

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE_DIR       = os.path.dirname(os.path.abspath(__file__))
SESSIONS_DIR   = os.path.join(BASE_DIR, "sessions")
MEDIA_DIR      = os.path.join(BASE_DIR, "media", "images")
ACCOUNTS_FILE  = os.path.join(BASE_DIR, "accounts.json")
POSTS_FILE     = os.path.join(BASE_DIR, "posts.json")

# ── Instagram URLs ─────────────────────────────────────────────────────────────
INSTAGRAM_URL       = "https://www.instagram.com/"
INSTAGRAM_LOGIN_URL = "https://www.instagram.com/accounts/login/"

# ── Ensure Required Directories Exist ────────────────────────────────────────
os.makedirs(SESSIONS_DIR, exist_ok=True)
os.makedirs(MEDIA_DIR, exist_ok=True)


def random_delay(min_sec: float = DELAY_MIN, max_sec: float = DELAY_MAX) -> None:
    """Sleep for a random duration to mimic human behavior."""
    delay = random.uniform(min_sec, max_sec)
    time.sleep(delay)


def typing_delay() -> None:
    """Short delay between keystrokes to simulate real typing speed."""
    time.sleep(random.uniform(TYPE_DELAY_MIN, TYPE_DELAY_MAX))
