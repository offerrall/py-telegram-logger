# py-telegram-logger

Minimal Python logger with Telegram notifications. (150 loc)

## Installation

```bash
git clone https://github.com/offerrall/py-telegram-logger
cd py-telegram-logger
pip install .
```

## Usage

```python
from pytelegram_logger import init_telegram_logger, log

init_telegram_logger(
    log_dir="logs",
    telegram_token_logs="BOT_TOKEN_1",
    telegram_token_errors="BOT_TOKEN_2",
    telegram_chat_ids=["-1001234567890"],
    retention_days=30
)

log("App started")
log("Payment received", send_telegram=True)
log("Critical error", is_error=True, send_telegram=True)
```

## API

### `init_telegram_logger()`

Initialize once at startup.

```python
init_telegram_logger(
    log_dir="logs",
    telegram_token_logs=None,
    telegram_token_errors=None,
    telegram_chat_ids=None,
    retention_days=30
)
```

### `log()`

Log a message.

```python
log(message, is_error=False, send_telegram=False, save=True)
```

- `is_error=True` → saves to error file
- `send_telegram=True` → sends to Telegram
- `save=False` → doesn't save to file

## Files

Daily log files:
```
logs/
├── logs_2025_01_21.log
├── logs_2025_01_22.log
├── errors_2025_01_21.log
└── errors_2025_01_22.log
```

Files older than `retention_days` are deleted automatically (checked hourly).

## Examples

```python
from pytelegram_logger import init_telegram_logger, log
import time

init_telegram_logger(retention_days=7)

# Normal logging
log("User login")
log("Processing data")

# With Telegram
log("Server restart", send_telegram=True)

# Errors
log("Database failed", is_error=True, send_telegram=True)

# Temporary notification
log("Quick alert", send_telegram=True, save=False)

# GRBL logging
log(f"TX: {gcode}")
log(f"RX: {response}")
if "ALARM" in response:
    log(f"ALARM: {response}", is_error=True, send_telegram=True)

time.sleep(5) # wait to allow async logs to complete
```

## Performance

- 10,000+ logs/second
- < 1ms per log call
- Thread-safe
- Non-blocking

## Requirements

- Python 3.10+
- requests

## License

MIT License