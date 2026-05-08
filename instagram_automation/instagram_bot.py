"""
instagram_bot.py — Core browser automation class for Instagram Automation Engine
"""

import os
import time
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    TimeoutException,
    NoSuchElementException,
    WebDriverException,
)
from webdriver_manager.chrome import ChromeDriverManager

from config import (
    HEADLESS, WINDOW_WIDTH, WINDOW_HEIGHT,
    PAGE_LOAD_WAIT, POST_WAIT,
    INSTAGRAM_URL, INSTAGRAM_LOGIN_URL,
    random_delay,
)
from session_manager import SessionManager
from utils import logger, human_type, safe_find, safe_click


class InstagramBot:
    """
    Full-featured Instagram browser automation bot.

    Handles: login, session persistence, image posting.
    Built for multi-account workflows via main.py orchestration.

    Usage:
        bot = InstagramBot()
        bot.start_browser()
        if not bot.load_session("user1"):
            bot.login("user1", "pass1")
        bot.create_post("media/images/post1.jpg", "Hello world!")
        bot.save_session("user1")
        bot.close()
    """

    def __init__(self, headless: bool = HEADLESS):
        self.headless = headless
        self.driver: Optional[webdriver.Chrome] = None
        self.session_mgr = SessionManager()

    # ─────────────────────────────────────────────────────────────────────────
    # Browser Lifecycle
    # ─────────────────────────────────────────────────────────────────────────

    def start_browser(self) -> None:
        """Initialize and configure the Chrome WebDriver."""
        logger.info("Starting Chrome browser...")
        options = Options()

        if self.headless:
            options.add_argument("--headless=new")

        options.add_argument(f"--window-size={WINDOW_WIDTH},{WINDOW_HEIGHT}")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-infobars")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-notifications")
        options.add_argument("--lang=en-US")

        # Mask Selenium's navigator.webdriver fingerprint
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=options)

        # Remove webdriver property via CDP
        self.driver.execute_cdp_cmd(
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
        )

        self.driver.implicitly_wait(5)
        logger.info("Browser started successfully.")

    def close(self) -> None:
        """Safely close the browser."""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("Browser closed.")
            except WebDriverException:
                pass
            finally:
                self.driver = None

    # ─────────────────────────────────────────────────────────────────────────
    # Session Management
    # ─────────────────────────────────────────────────────────────────────────

    def load_session(self, username: str) -> bool:
        """
        Try to restore a saved session for this account.
        Returns True if session loaded + user appears logged in.
        """
        if not self.session_mgr.has_session(username):
            return False

        # Navigate to Instagram domain first (required to set cookies)
        self.driver.get(INSTAGRAM_URL)
        random_delay(2, 4)

        loaded = self.session_mgr.load(self.driver, username)
        if not loaded:
            return False

        # Refresh to apply cookies
        self.driver.refresh()
        random_delay(PAGE_LOAD_WAIT, PAGE_LOAD_WAIT + 3)

        # Verify if we're actually logged in by checking for an element
        # that only appears on the home feed
        if self._is_logged_in():
            logger.info(f"Session restored for: {username}")
            return True
        else:
            logger.warning(f"Session expired for: {username}. Will re-login.")
            self.session_mgr.delete(username)
            return False

    def save_session(self, username: str) -> None:
        """Save the current browser cookies for future reuse."""
        self.session_mgr.save(self.driver, username)

    def _is_logged_in(self) -> bool:
        """Detect if the browser is on an authenticated Instagram session."""
        try:
            # Look for the 'New post' button or home icon — only visible when logged in
            WebDriverWait(self.driver, 8).until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "svg[aria-label='Home'], a[href='/']")
                )
            )
            return True
        except TimeoutException:
            return False

    # ─────────────────────────────────────────────────────────────────────────
    # Login
    # ─────────────────────────────────────────────────────────────────────────

    def login(self, username: str, password: str) -> bool:
        """
        Perform a full Instagram login flow.
        Returns True on success, raises RuntimeError on failure.
        """
        logger.info(f"Logging in as: {username}")
        try:
            self.driver.get(INSTAGRAM_LOGIN_URL)
            random_delay(PAGE_LOAD_WAIT, PAGE_LOAD_WAIT + 2)

            # Enter username
            username_input = safe_find(
                self.driver, By.NAME, "username", timeout=15
            )
            if not username_input:
                raise RuntimeError("Username input not found on login page.")
            human_type(username_input, username)
            random_delay(1, 2)

            # Enter password
            password_input = safe_find(
                self.driver, By.NAME, "password", timeout=10
            )
            if not password_input:
                raise RuntimeError("Password input not found on login page.")
            human_type(password_input, password)
            random_delay(1, 3)

            # Submit
            password_input.send_keys(Keys.RETURN)
            logger.info("Login form submitted. Waiting for response...")
            random_delay(PAGE_LOAD_WAIT, PAGE_LOAD_WAIT + 4)

            # Handle "Save your login info?" popup
            self._dismiss_popup("Save info", "Not now", "Not Now")

            # Handle notifications popup
            self._dismiss_popup("Turn on notifications", "Not Now")

            if self._is_logged_in():
                logger.info(f"Login successful: {username}")
                return True
            else:
                raise RuntimeError(
                    f"Login failed for {username}. "
                    "Check credentials or 2FA requirements."
                )

        except RuntimeError:
            raise
        except Exception as e:
            raise RuntimeError(f"Login encountered an unexpected error: {e}") from e

    def _dismiss_popup(self, *trigger_texts: str) -> None:
        """
        Attempt to dismiss a modal/popup by clicking text-matched buttons.
        Silently skips if popup is not present.
        """
        random_delay(2, 4)
        for text in trigger_texts:
            try:
                btn = self.driver.find_element(
                    By.XPATH, f"//button[contains(text(), '{text}')]"
                )
                btn.click()
                logger.debug(f"Dismissed popup: '{text}'")
                random_delay(1, 2)
                return
            except NoSuchElementException:
                continue

    # ─────────────────────────────────────────────────────────────────────────
    # Post Creation
    # ─────────────────────────────────────────────────────────────────────────

    def create_post(self, image_path: str, caption: str = "") -> bool:
        """
        Upload a static image post to Instagram.

        Steps:
        1. Click the '+' (New Post) button in the nav
        2. Upload the image file via hidden input
        3. Click through the editor steps (Crop → Filter → Caption)
        4. Write the caption
        5. Click Share

        Returns True on success, False on failure.
        """
        abs_image_path = os.path.abspath(image_path)
        if not os.path.exists(abs_image_path):
            logger.error(f"Image not found: {abs_image_path}")
            return False

        logger.info(f"Creating post — image: {image_path}")

        try:
            # ── Step 1: Click the New Post (+) button ────────────────────────
            self.driver.get(INSTAGRAM_URL)
            random_delay(3, 5)

            new_post_btn = safe_find(
                self.driver,
                By.XPATH,
                "//span[contains(@aria-label,'New post') or contains(@aria-label,'Create')]"
                "/ancestor::a | //a[@href='/create/style/']",
                timeout=15
            )
            if not new_post_btn:
                # Fallback: look for the SVG icon
                new_post_btn = safe_find(
                    self.driver,
                    By.XPATH,
                    "//svg[@aria-label='New post']/ancestor::div[1]",
                    timeout=10
                )
            if not new_post_btn:
                logger.error("Could not find 'New Post' button.")
                return False

            new_post_btn.click()
            random_delay(2, 4)

            # ── Step 2: Upload the image via file input ───────────────────────
            # Instagram's file input is hidden; find and send file path to it
            file_inputs = self.driver.find_elements(By.CSS_SELECTOR, "input[type='file']")
            if not file_inputs:
                logger.error("File upload input not found.")
                return False

            file_inputs[0].send_keys(abs_image_path)
            logger.info(f"File uploaded: {abs_image_path}")
            random_delay(3, 6)

            # ── Step 3: Click "Next" through editor steps ─────────────────────
            for step in ["Crop", "Filter/Edit", "Caption"]:
                if not self._click_next_button():
                    logger.warning(f"Could not advance past {step} step.")
                random_delay(2, 4)

            # ── Step 4: Write caption ─────────────────────────────────────────
            if caption:
                caption_field = safe_find(
                    self.driver,
                    By.XPATH,
                    "//div[@aria-label='Write a caption...' or @aria-label='Write a caption']",
                    timeout=10
                )
                if caption_field:
                    caption_field.click()
                    random_delay(1, 2)
                    human_type(caption_field, caption)
                    logger.info("Caption entered.")
                    random_delay(2, 3)
                else:
                    logger.warning("Caption field not found. Posting without caption.")

            # ── Step 5: Click Share ───────────────────────────────────────────
            shared = safe_click(
                self.driver,
                By.XPATH,
                "//div[text()='Share'] | //button[text()='Share']",
                timeout=10
            )
            if not shared:
                logger.error("Share button not found. Post may not have been submitted.")
                return False

            logger.info("Share button clicked. Waiting for post to upload...")
            random_delay(POST_WAIT, POST_WAIT + 5)

            logger.info("Post successfully created!")
            return True

        except Exception as e:
            logger.error(f"create_post() failed: {e}")
            return False

    def _click_next_button(self) -> bool:
        """Click the 'Next' button in the post editor flow."""
        return safe_click(
            self.driver,
            By.XPATH,
            "//div[text()='Next'] | //button[text()='Next']",
            timeout=8
        )

    def __repr__(self) -> str:
        return f"<InstagramBot headless={self.headless} driver={'active' if self.driver else 'inactive'}>"
