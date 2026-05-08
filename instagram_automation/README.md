# Instagram Automation Engine

A modular, production-grade Instagram automation engine built with Python + Selenium.

## Project Structure

```
instagram_automation/
├── main.py              # Orchestration entry point
├── config.py            # Central configuration
├── account_manager.py   # Multi-account loader
├── instagram_bot.py     # Core automation class
├── post_manager.py      # Post queue manager
├── session_manager.py   # Cookie-based session persistence
├── utils.py             # Shared helpers (logger, safe_find, human_type)
├── accounts.json        # Your Instagram accounts
├── posts.json           # Your post queue
├── sessions/            # Auto-saved session cookies (gitignored)
└── media/
    └── images/          # Place your post images here
```

## Setup

```bash
pip install selenium webdriver-manager python-dotenv
```

## Quick Start

1. **Fill in accounts.json** with your credentials
2. **Add images** to `media/images/`
3. **Fill in posts.json** with image paths and captions
4. **Run:**

```bash
python main.py
```

## Configuration (`config.py`)

| Setting | Default | Description |
|---------|---------|-------------|
| `HEADLESS` | `False` | Run browser invisibly |
| `DELAY_MIN` | `3` | Min seconds between actions |
| `DELAY_MAX` | `7` | Max seconds between actions |

## Session Persistence

On first run per account, the bot logs in and saves cookies to `sessions/{username}.pkl`.
On subsequent runs, it restores from cookies — **no login required**.

To force a re-login, delete the `.pkl` file for that account.

## Future Integration Points

| Feature | Hook Location |
|---------|--------------|
| Supabase accounts | `AccountManager._load()` |
| Supabase posts table | `PostManager._load()` + `mark_completed()` |
| AI caption generation | `post_manager.py` `get_next()` |
| Scheduler (APScheduler/cron) | `main.py` `run_automation()` |
| REST API wrapper | Add FastAPI/Flask around `run_automation()` |

## .gitignore

```
sessions/
*.pkl
accounts.json
automation.log
```
