"""
post_manager.py — Dynamic post loader for Instagram Automation Engine
"""

import json
import os
from typing import List, Dict, Optional
from utils import logger
from config import POSTS_FILE


class PostManager:
    """
    Loads posts from posts.json and tracks which have been completed.

    Each post entry supports:
    {
        "image": "media/images/post1.jpg",
        "caption": "Your caption here",
        "status": "pending"   <-- auto-managed field
    }

    Future-ready for:
    - Supabase posts table integration
    - AI caption generation hook (generate caption on-demand)
    - Scheduler integration (time-based post queuing)
    """

    PENDING   = "pending"
    COMPLETED = "completed"
    FAILED    = "failed"

    def __init__(self, posts_file: str = POSTS_FILE):
        self.posts_file = posts_file
        self.posts: List[Dict] = []
        self._load()

    def _load(self) -> None:
        """Load posts from JSON file, inject default status if missing."""
        if not os.path.exists(self.posts_file):
            logger.error(f"Posts file not found: {self.posts_file}")
            raise FileNotFoundError(
                f"Create '{self.posts_file}' with your posts list. "
                "See posts.json.example for format."
            )

        with open(self.posts_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, list) or len(data) == 0:
            raise ValueError("posts.json must be a non-empty JSON array.")

        # Validate and inject defaults
        for idx, post in enumerate(data):
            if "image" not in post:
                raise ValueError(f"Post #{idx + 1} is missing the 'image' field.")
            if "caption" not in post:
                post["caption"] = ""
            if "status" not in post:
                post["status"] = self.PENDING

        self.posts = data
        pending = sum(1 for p in self.posts if p["status"] == self.PENDING)
        logger.info(f"Loaded {len(self.posts)} post(s) | {pending} pending")

    def _save(self) -> None:
        """Persist updated status back to posts.json."""
        with open(self.posts_file, "w", encoding="utf-8") as f:
            json.dump(self.posts, f, indent=2, ensure_ascii=False)

    def get_next(self) -> Optional[Dict]:
        """Return the next pending post, or None if all are done."""
        for post in self.posts:
            if post["status"] == self.PENDING:
                return post
        logger.info("No pending posts remaining.")
        return None

    def get_pending(self) -> List[Dict]:
        """Return all pending posts."""
        return [p for p in self.posts if p["status"] == self.PENDING]

    def mark_completed(self, post: Dict) -> None:
        """Mark a post as completed and save the updated list."""
        post["status"] = self.COMPLETED
        self._save()
        logger.info(f"Post marked as COMPLETED: {post.get('image')}")

    def mark_failed(self, post: Dict, reason: str = "") -> None:
        """Mark a post as failed (e.g. element not found, upload error)."""
        post["status"] = self.FAILED
        post["fail_reason"] = reason
        self._save()
        logger.warning(f"Post marked as FAILED: {post.get('image')} — {reason}")

    def reset_all(self) -> None:
        """Reset all posts to pending (useful for re-running the queue)."""
        for post in self.posts:
            post["status"] = self.PENDING
            post.pop("fail_reason", None)
        self._save()
        logger.info("All posts reset to PENDING.")

    def count_pending(self) -> int:
        return sum(1 for p in self.posts if p["status"] == self.PENDING)

    def __repr__(self) -> str:
        return (
            f"<PostManager total={len(self.posts)} "
            f"pending={self.count_pending()}>"
        )
