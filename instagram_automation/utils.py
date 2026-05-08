"""
utils.py — Shared utility helpers for Instagram Automation Engine
"""

import logging
import os
import sys


# ── Logging Setup ─────────────────────────────────────────────────────────────
def setup_logger(name: str = "instagram_bot", level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger with console + file output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        fmt = logging.Formatter(
            "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        # Console handler
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(fmt)
        logger.addHandler(ch)

        # File handler
        log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "automation.log")
        fh = logging.FileHandler(log_path, encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)

    return logger


logger = setup_logger()


def human_type(element, text: str, delay_fn=None) -> None:
    """
    Type text into a Selenium element one character at a time
    with randomized delays to simulate human typing speed.
    """
    from config import typing_delay as _td
    delay_fn = delay_fn or _td

    element.clear()
    for char in text:
        element.send_keys(char)
        delay_fn()


def safe_find(driver, by, selector: str, timeout: int = 10):
    """
    Wait for and return a single element. Returns None on timeout.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException

    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
    except TimeoutException:
        logger.warning(f"Element not found: [{by}] '{selector}' (timeout={timeout}s)")
        return None


def safe_click(driver, by, selector: str, timeout: int = 10) -> bool:
    """
    Wait for an element to be clickable, then click it.
    Returns True on success, False on failure.
    """
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, ElementClickInterceptedException

    try:
        el = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        el.click()
        return True
    except (TimeoutException, ElementClickInterceptedException) as e:
        logger.warning(f"Click failed on [{by}] '{selector}': {e}")
        return False
