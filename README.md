# py-telegram-logger

[![PyPI version](https://img.shields.io/pypi/v/py-telegram-logger.svg)](https://pypi.org/project/py-telegram-logger/)
[![Python](https://img.shields.io/pypi/pyversions/py-telegram-logger.svg)](https://pypi.org/project/py-telegram-logger/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Fast, minimal async logger for local files with optional Telegram alerts. **Zero dependencies** (stdlib only).

## Install

```bash
pip install py-telegram-logger
```

## Usage

```python
from pytelegram_logger import init_telegram_logger, log, shutdown_logger

init_telegram_logger(name="my_app")

log("App started")
log("Database error", is_error=True)

shutdown_logger()  # optional, flushes pending logs
```

### With Telegram alerts

```python
init_telegram_logger(
    name="my_app",
    telegram_token_logs="BOT_TOKEN_1",     # routine logs
    telegram_token_errors="BOT_TOKEN_2",   # error alerts
    telegram_chat_ids=["-1001234567890"],
)

log("Payment received", send_telegram=True)
log("Critical failure", is_error=True, send_telegram=True)
```

Two tokens = two channels: routine logs stay separate from high-priority error alerts.

## API

### `init_telegram_logger(name, ...)`

| Argument | Default | Description |
|---|---|---|
| `name` | — | **Required.** Unique instance id (e.g. `"api"`, `"worker_1"`). |
| `log_dir` | `"logs"` | Directory for log files. |
| `telegram_token_logs` | `None` | Bot token for routine logs. |
| `telegram_token_errors` | `None` | Bot token for errors. |
| `telegram_chat_ids` | `[]` | List of chat IDs. |
| `retention_days` | `30` | Auto-delete files older than N days. |
| `queue_maxsize` | `10000` | Max pending messages per queue. |

### `log(message, is_error=False, send_telegram=False, save=True)`

- `is_error=True` → error file + error token
- `send_telegram=True` → also send to Telegram
- `save=False` → Telegram only, no file

### `shutdown_logger()`

Graceful shutdown: drains queues and closes files. Optional but recommended.

### `get_dropped_count(sink=None)`

Messages dropped because a queue was full (logging never blocks the caller).

```python
get_dropped_count()            # total (disk + Telegram)
get_dropped_count("file")      # local logs lost  ← the one that matters
get_dropped_count("telegram")  # Telegram alerts lost
```

## How it works

- **Disk and network are isolated.** Separate queue + worker each, so a slow or down Telegram never delays local logs. The file is the critical path: fast and reliable.
- **Non-blocking.** `log()` drops and counts when a queue is full instead of freezing your app.
- **Crash-safe.** Every line is flushed to disk immediately (durability over throughput).
- **Daily rotation** per named instance, with auto-cleanup after `retention_days`.

```
logs/
├── my_app_logs_2025_01_21.log
├── my_app_errors_2025_01_21.log
└── worker_1_logs_2025_01_21.log
```

## Requirements

- Python 3.10+
- No external dependencies

## License

MIT
