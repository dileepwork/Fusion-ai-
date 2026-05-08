"""
main.py — Orchestration entry point for Instagram Automation Engine

Flow per account:
  1. Load saved session → if exists, restore it
  2. If session missing/expired → fresh login
  3. Fetch next pending post
  4. Upload image + caption
  5. Save session for next run
  6. Close browser

Run:
    python main.py
"""

import sys
from account_manager import AccountManager
from post_manager import PostManager
from instagram_bot import InstagramBot
from config import random_delay
from utils import logger


def run_automation() -> None:
    account_mgr = AccountManager()
    post_mgr    = PostManager()

    accounts = account_mgr.get_active()
    logger.info(f"=== Instagram Automation Engine START ===")
    logger.info(f"Accounts: {len(accounts)} | Pending posts: {post_mgr.count_pending()}")

    if post_mgr.count_pending() == 0:
        logger.info("No pending posts. Run post_manager.reset_all() to requeue.")
        return

    for account in accounts:
        username = account["username"]
        password = account["password"]

        # Fetch the next post for this account
        post = post_mgr.get_next()
        if not post:
            logger.info("All posts exhausted. Stopping.")
            break

        logger.info(f"\n{'─' * 50}")
        logger.info(f"Account : {username}")
        logger.info(f"Post    : {post['image']}")
        logger.info(f"Caption : {post.get('caption', '')[:60]}...")
        logger.info(f"{'─' * 50}")

        bot = InstagramBot()
        try:
            # ── 1. Start Browser ──────────────────────────────────────────────
            bot.start_browser()
            random_delay(2, 4)

            # ── 2. Session or Login ───────────────────────────────────────────
            session_restored = bot.load_session(username)
            if not session_restored:
                logger.info(f"No valid session — performing fresh login for: {username}")
                bot.login(username, password)
                random_delay(3, 5)

            # ── 3. Create Post ────────────────────────────────────────────────
            success = bot.create_post(
                image_path=post["image"],
                caption=post.get("caption", "")
            )

            # ── 4. Update Status ─────────────────────────────────────────────
            if success:
                post_mgr.mark_completed(post)
                logger.info(f"✓ Post completed for {username}")
            else:
                post_mgr.mark_failed(post, reason="create_post() returned False")
                logger.warning(f"✗ Post failed for {username}")

            # ── 5. Save Session ───────────────────────────────────────────────
            bot.save_session(username)
            random_delay(3, 6)

        except RuntimeError as e:
            logger.error(f"[RUNTIME ERROR] {username}: {e}")
            post_mgr.mark_failed(post, reason=str(e))

        except Exception as e:
            logger.error(f"[UNEXPECTED ERROR] {username}: {e}", exc_info=True)
            post_mgr.mark_failed(post, reason=str(e))

        finally:
            # ── 6. Always Close Browser ───────────────────────────────────────
            bot.close()
            random_delay(5, 10)  # Cool-down between accounts

    logger.info(f"\n=== Instagram Automation Engine COMPLETE ===")
    logger.info(f"Remaining pending posts: {post_mgr.count_pending()}")


if __name__ == "__main__":
    try:
        run_automation()
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting cleanly.")
        sys.exit(0)
    except (FileNotFoundError, ValueError) as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
