# py-telegram-logger

Fast, minimal Python logger for local files + optional Telegram notifications.

**Why two tokens?** Separate channels for routine logs (low priority) and errors (high priority alerts).

## Installation

```bash
pip install git+https://github.com/offerrall/py-telegram-logger.git
```

## Quick Start

### Local logging only

```python
from pytelegram_logger import init_telegram_logger, log

init_telegram_logger(name="my_app", log_dir="logs")

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

**Required:**
- `name` - Unique identifier (e.g., "api_server", "worker_1")

**Optional:**
- `log_dir` - Directory for logs (default: "logs")
- `telegram_token_logs` - Bot token for general logs
- `telegram_token_errors` - Bot token for errors
- `telegram_chat_ids` - List of chat IDs
- `retention_days` - Auto-delete after N days (default: 30)

### `log(message, ...)`

```python
log(message, is_error=False, send_telegram=False, save=True)
```

- `is_error=True` → error file + error token
- `send_telegram=True` → send to Telegram
- `save=False` → Telegram only (no file)

### `shutdown_logger()`

Graceful shutdown. Optional but recommended.

## File Organization

```
logs/
├── my_app_logs_2025_01_21.log
├── my_app_errors_2025_01_21.log
├── worker_1_logs_2025_01_21.log
└── worker_1_errors_2025_01_21.log
```

Daily rotation. Auto-cleanup after `retention_days`.

## Common Patterns

**Server monitoring:**
```python
init_telegram_logger(name="api", telegram_token_errors="TOKEN", telegram_chat_ids=["ID"])
log("Server started")
log("DB unreachable", is_error=True, send_telegram=True)
```

**Errors only to Telegram:**
```python
init_telegram_logger(name="payments", telegram_token_errors="TOKEN", telegram_chat_ids=["ID"])

log("Processing...")  # File only
log("Failed", is_error=True, send_telegram=True)  # File + Telegram
```

## Performance

- **195k logs/sec** on Linux (typical hardware)
- **80k logs/sec** on Windows (typical hardware)
- Non-blocking queue design
- 8KB buffer + flush for crash safety
- Negligible CPU overhead

## Features

- **Thread-safe** - queue-based async processing
- **Named instances** - multiple apps, one folder
- **Daily rotation** - auto-cleanup old files
- **Crash-safe** - flush after every write
- **Dual channels** - separate tokens for logs/errors
- **Simple** - ~230 lines, only needs `requests`

## Error Handling

Clear validation messages:

```python
# Not initialized
log("test")  
# RuntimeError: Logger not initialized. Call init_telegram_logger() first

# Missing name
init_telegram_logger(log_dir="logs")
# ValueError: Logger name must be provided, cannot be empty

# Telegram not configured
log("test", send_telegram=True)
# ValueError: Telegram chat IDs not configured
```

Internal errors print to stderr with `[pytelegram_logger]` prefix.

## Requirements

- Python 3.10+
- requests

## License

MIT License
