# py-telegram-logger

Minimal Python logger for local files + optional Telegram notifications.

**Why two tokens?** Many use cases need separate Telegram channels: one for general activity logs (low urgency) and another for errors/alerts (high priority notifications).

## Installation

```bash
pip install git+https://github.com/offerrall/py-telegram-logger.git
```

## Quick Start

### Local logging only

```python
from pytelegram_logger import init_telegram_logger, log

init_telegram_logger(name="my_app", # Required: unique identifier
                     log_dir="logs") 

log("App started")
log("Database error", is_error=True)
```

### With Telegram notifications

```python
from pytelegram_logger import init_telegram_logger, log

init_telegram_logger(
    name="my_app",                         
    log_dir="logs",
    telegram_token_logs="BOT_TOKEN_1",      # For general notifications
    telegram_token_errors="BOT_TOKEN_2",    # For error alerts
    telegram_chat_ids=["-1001234567890"],
    retention_days=30
)

log("Payment received", send_telegram=True)
log("Critical error", is_error=True, send_telegram=True)
```

## Core Functions

### `init_telegram_logger(name, ...)`

**Required parameter:**
- `name` - Unique identifier for log files (e.g., "api_server", "machine_1")

**Optional parameters:**
- `log_dir` - Directory for log files (default: "logs")
- `telegram_token_logs` - Bot token for general logs
- `telegram_token_errors` - Bot token for errors
- `telegram_chat_ids` - List of Telegram chat IDs
- `retention_days` - Auto-delete logs older than this (default: 30)

### `log(message, ...)`

```python
log(message, is_error=False, send_telegram=False, save=True)
```

- `is_error=True` → writes to errors file, uses error token
- `send_telegram=True` → sends Telegram notification
- `save=False` → Telegram only, no file write

### `shutdown_logger()`

Gracefully shutdown (recommended but optional).

## File Organization

```
logs/
├── my_app_logs_2025_01_21.log
├── my_app_errors_2025_01_21.log
├── api_server_logs_2025_01_21.log
└── api_server_errors_2025_01_21.log
```

Each `name` creates separate log files. Files older than `retention_days` are deleted automatically.

## Common Patterns

**Server monitoring:**
```python
init_telegram_logger(name="api_server", telegram_token_errors="TOKEN", telegram_chat_ids=["ID"])
log("Server started")
log("Database unreachable", is_error=True, send_telegram=True)
```

**Errors only to Telegram:**
```python
init_telegram_logger(
    name="payment_processor",
    telegram_token_errors="TOKEN",  # Only error token configured
    telegram_chat_ids=["ID"]
)

log("Processing payment...")  # Local file only
log("Payment failed", is_error=True, send_telegram=True)  # File + Telegram
```

## Features

- **195,000+ logs/second** on Linux, normal hardware
- **80,000+ logs/second** on Windows, normal hardware
- **Named log files** - separate files per application
- **Async & thread-safe** - non-blocking queue-based
- **Auto-rotation** - daily files with configurable retention
- **Crash-safe** - flush after every write
- **Dual Telegram channels** - separate tokens for logs vs errors
- **~230 lines of code** - only requires `requests`

## Error Messages

The logger provides clear feedback:

```python
# Forgot to initialize
log("test")  
# RuntimeError: Logger not initialized. Call init_telegram_logger() first

# Missing name
init_telegram_logger(log_dir="logs")
# ValueError: Logger name must be provided, cannot be empty

# Telegram not configured
init_telegram_logger(name="app", log_dir="logs")
log("test", send_telegram=True)
# ValueError: Telegram chat IDs not configured
```

## Requirements

- Python 3.10+
- requests

## License

MIT License