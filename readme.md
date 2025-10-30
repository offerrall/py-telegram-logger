# py-telegram-logger

Minimal Python logger that writes to local files and optionally sends notifications to Telegram. Perfect for monitoring scripts, servers, or automation tasks.

**Why two tokens?** Many use cases need separate Telegram channels: one for general activity logs (low urgency) and another for errors/alerts (high priority notifications).

## Installation

```bash
pip install git+https://github.com/offerrall/py-telegram-logger.git
```

## Quick Start

### With Telegram notifications

```python
from pytelegram_logger import init_telegram_logger, log

init_telegram_logger(
    log_dir="logs",
    telegram_token_logs="BOT_TOKEN_1",      # Optional: for general logs
    telegram_token_errors="BOT_TOKEN_2",    # Optional: for errors/alerts
    telegram_chat_ids=["-1001234567890"],   # Your Telegram chat/channel IDs
    retention_days=30
)

log("App started")
log("Payment received", send_telegram=True)
log("Critical error", is_error=True, send_telegram=True)
```

### Without Telegram (local files only)

```python
from pytelegram_logger import init_telegram_logger, log

# Initialize without Telegram - just local logging
init_telegram_logger(log_dir="logs", retention_days=7)

log("App started")
log("Processing data...")
log("Database error", is_error=True)  # Saved to errors file
```

### Multiple instances with separate files

```python
from pytelegram_logger import init_telegram_logger, log

# Each instance can have its own log files
init_telegram_logger(
    log_dir="logs",
    name="machine_1"  # Creates machine_1_logs_YYYY_MM_DD.log
)

log("Machine 1 started")
```

Result:
```
logs/
├── machine_1_logs_2025_01_21.log
├── machine_1_errors_2025_01_21.log
├── machine_2_logs_2025_01_21.log
└── machine_2_errors_2025_01_21.log
```

## Features

- **High performance**: 80,000+ logs/second (In window 10 and typical SSD)
- **Local logging**: Automatic daily log files with configurable retention
- **Telegram notifications**: Optional integration for real-time alerts
- **Dual channels**: Separate tokens for regular logs vs errors (or use just one)
- **Named instances**: Multiple loggers with separate files using `name` parameter
- **Flexible**: Works with or without Telegram - you choose what to configure
- **Clear errors**: Helpful error messages if Telegram features are used without proper setup
- **Async & fast**: Non-blocking, thread-safe, queue-based worker
- **Crash-safe**: Flush after every write ensures no data loss
- **Minimal**: ~230 lines of code, only requires `requests`

## API

### `init_telegram_logger()`

Initialize once at startup.

```python
init_telegram_logger(
    log_dir="logs",                    # Where to save log files
    telegram_token_logs=None,          # Bot token for general logs
    telegram_token_errors=None,        # Bot token for error alerts
    telegram_chat_ids=None,            # List of chat IDs to notify
    retention_days=30,                 # Auto-delete logs older than this
    name=""                            # Optional: unique name for this instance
)
```

### `log()`

Log a message.

```python
log(message, is_error=False, send_telegram=False, save=True)
```

- `is_error=True` → saves to `errors_YYYY_MM_DD.log` and uses error token
- `send_telegram=True` → sends notification to Telegram
- `save=False` → only sends to Telegram, doesn't write to file

### `shutdown_logger()`

Gracefully shutdown the logger (optional but recommended).

```python
shutdown_logger()  # Waits for queue to finish and closes files
```

## File Structure

Daily log files organized automatically:

```
logs/
├── logs_2025_01_21.log
├── logs_2025_01_22.log
├── errors_2025_01_21.log
└── errors_2025_01_21.log
```

Files older than `retention_days` are deleted automatically (checked hourly).

## Examples

```python
from pytelegram_logger import init_telegram_logger, log, shutdown_logger
import time

# Initialize (Telegram is optional)
init_telegram_logger(
    log_dir="logs",
    telegram_token_logs="123:ABC",
    telegram_token_errors="456:DEF",
    telegram_chat_ids=["-1001234567890"],
    retention_days=7
)

# Regular logging (saved locally)
log("User logged in")
log("Processing payment...")

# Important events (local + Telegram)
log("Server restarted", send_telegram=True)
log("Payment successful: $500", send_telegram=True)

# Errors (saved to errors file + Telegram alert)
log("Database connection failed", is_error=True, send_telegram=True)
log("API timeout", is_error=True, send_telegram=True)

# Quick Telegram alert without saving
log("Temporary status update", send_telegram=True, save=False)

# GRBL/CNC machine logging example
log(f"TX: {gcode}")
log(f"RX: {response}")
if "ALARM" in response:
    log(f"ALARM: {response}", is_error=True, send_telegram=True)

shutdown_logger()
```

## Use Cases

- **Server monitoring**: Get alerts when services fail
- **Automation scripts**: Track execution and catch errors
- **IoT devices**: Monitor sensors and receive alerts
- **Web scrapers**: Log progress and errors
- **CNC/3D printers**: Track commands and catch alarms (can handle 300+ machines)
- **Payment processing**: Audit transactions and alert on failures
- **Industrial automation**: Multi-machine logging with separate files per machine

## Shutting Down

```python
log("Program finished")
shutdown_logger()  # Waits for queue + closes files cleanly
```
Guarantees:
- All logs are written before exit
- Files are closed properly
- No logs are lost

## Error Handling

The logger will raise clear errors if you try to use Telegram features without proper configuration:

```python
# Not initialized
log("test")  # RuntimeError: Logger not initialized. Call init_telegram_logger() first

# Telegram not configured
init_telegram_logger(log_dir="logs")
log("test", send_telegram=True)  # ValueError: Telegram chat IDs not configured

# Missing token for logs
init_telegram_logger(log_dir="logs", telegram_chat_ids=["123"])
log("test", send_telegram=True)  # ValueError: Telegram token for logs not configured

# Missing token for errors
init_telegram_logger(log_dir="logs", telegram_chat_ids=["123"], telegram_token_logs="token")
log("error", is_error=True, send_telegram=True)  # ValueError: Telegram token for errors not configured
```

**Tip**: If you only want error alerts on Telegram, configure only `telegram_token_errors`:

```python
init_telegram_logger(
    log_dir="logs",
    telegram_token_errors="BOT_TOKEN",
    telegram_chat_ids=["-1001234567890"]
)

log("Normal log")  # Works: saved to file only
log("Critical error", is_error=True, send_telegram=True)  # Works: file + Telegram
log("Info", send_telegram=True)  # Error: telegram_token_logs not configured
```

## Requirements

- Python 3.10+
- requests

## License

MIT License