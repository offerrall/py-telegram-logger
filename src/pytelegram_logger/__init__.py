import threading
import time
import html
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue, Empty, Full
from dataclasses import dataclass, field
import sys

__all__ = ['init_telegram_logger', 'log', 'shutdown_logger', 'get_dropped_count']


@dataclass
class LoggerState:
    log_dir: Path | None = None
    telegram_token_logs: str | None = None
    telegram_token_errors: str | None = None
    telegram_chat_ids: list = field(default_factory=list)
    retention_days: int = 30
    name: str = ""

    file_queue: Queue | None = None
    telegram_queue: Queue | None = None

    running: bool = False
    file_worker_thread: threading.Thread | None = None
    telegram_worker_thread: threading.Thread | None = None
    cleanup_thread: threading.Thread | None = None

    log_file: object = None
    error_file: object = None
    current_log_path: str = ""
    current_error_path: str = ""

    cached_date: str = ""
    cached_log_path: Path | None = None
    cached_error_path: Path | None = None

    dropped_file: int = 0
    dropped_telegram: int = 0
    dropped_lock: threading.Lock = field(default_factory=threading.Lock)


state = LoggerState()


def init_telegram_logger(
    log_dir: str = "logs",
    telegram_token_logs: str | None = None,
    telegram_token_errors: str | None = None,
    telegram_chat_ids: list | None = None,
    retention_days: int = 30,
    name: str = "",
    queue_maxsize: int = 10000,
) -> None:
    """Initialize the Telegram logger with specified configuration.

    Args:
        log_dir: Directory where log files will be stored
        telegram_token_logs: Bot token for general log notifications
        telegram_token_errors: Bot token for error notifications
        telegram_chat_ids: List of Telegram chat IDs to send notifications to
        retention_days: Number of days to keep log files before auto-deletion
        name: Unique identifier for this logger instance (required)
        queue_maxsize: Max pending messages per queue (file and Telegram have
            independent queues). When a queue is full, new messages for that
            sink are dropped and counted (see get_dropped_count()).

    Raises:
        RuntimeError: If logger is already initialized
        ValueError: If name is empty or whitespace
    """
    if state.running:
        raise RuntimeError("Logger already initialized")

    if not name or name.strip() == "":
        raise ValueError("Logger name must be provided, cannot be empty")

    state.log_dir = Path(log_dir)
    state.log_dir.mkdir(exist_ok=True)

    state.telegram_token_logs = telegram_token_logs
    state.telegram_token_errors = telegram_token_errors
    state.telegram_chat_ids = telegram_chat_ids or []
    state.retention_days = retention_days
    state.name = name

    state.file_queue = Queue(maxsize=queue_maxsize)
    state.telegram_queue = Queue(maxsize=queue_maxsize)
    state.dropped_file = 0
    state.dropped_telegram = 0
    state.running = True

    state.file_worker_thread = threading.Thread(target=file_worker, daemon=True)
    state.file_worker_thread.start()

    state.telegram_worker_thread = threading.Thread(target=telegram_worker, daemon=True)
    state.telegram_worker_thread.start()

    state.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    state.cleanup_thread.start()


def get_daily_file(is_error: bool = False) -> Path:
    """Get the path for today's log file.

    Args:
        is_error: If True, return error log path; otherwise return general log path

    Returns:
        Path object for the appropriate log file
    """
    now = datetime.now()
    date_str = f"{now.year}_{now.month:02d}_{now.day:02d}"

    if state.cached_date != date_str:
        state.cached_log_path = state.log_dir / f"{state.name}_logs_{date_str}.log"
        state.cached_error_path = state.log_dir / f"{state.name}_errors_{date_str}.log"
        state.cached_date = date_str

    return state.cached_error_path if is_error else state.cached_log_path


def write_to_file(message: str, is_error: bool = False) -> None:
    """Write a log message to the appropriate file.

    Args:
        message: The log message to write
        is_error: If True, write to error log; otherwise write to general log
    """
    filepath = get_daily_file(is_error)
    filepath_str = str(filepath)

    now = datetime.now()
    timestamp = '%04d-%02d-%02d %02d:%02d:%02d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)

    if is_error:
        if state.current_error_path != filepath_str:
            if state.error_file:
                state.error_file.close()
            state.error_file = open(filepath, "a", encoding="utf-8")
            state.current_error_path = filepath_str

        file_handle = state.error_file
    else:
        if state.current_log_path != filepath_str:
            if state.log_file:
                state.log_file.close()
            state.log_file = open(filepath, "a", encoding="utf-8")
            state.current_log_path = filepath_str

        file_handle = state.log_file

    file_handle.write(f"[{timestamp}] {message}\n")
    file_handle.flush()


def send_telegram(message: str, is_error: bool = False) -> None:
    """Send a log message to Telegram.

    Args:
        message: The log message to send
        is_error: If True, use error token and prefix; otherwise use log token
    """
    token = state.telegram_token_errors if is_error else state.telegram_token_logs

    if not token or not state.telegram_chat_ids:
        return

    log_type = "🔴 ERROR" if is_error else "ℹ️ LOG"
    full_message = f"{log_type}\n\n{html.escape(message)}"

    url = f"https://api.telegram.org/bot{token}/sendMessage"

    for chat_id in state.telegram_chat_ids:
        try:
            data = json.dumps({
                "chat_id": chat_id,
                "text": full_message,
                "parse_mode": "HTML",
            }).encode("utf-8")

            req = urllib.request.Request(
                url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=5)
            time.sleep(0.05)
        except urllib.error.URLError as e:
            print(f"[pytelegram_logger] Telegram API error for chat {chat_id}: {e}", file=sys.stderr)
        except Exception as e:
            print(f"[pytelegram_logger] Unexpected error sending to Telegram chat {chat_id}: {e}", file=sys.stderr)


def file_worker() -> None:
    """Background worker thread that writes log messages to disk."""
    while state.running:
        try:
            item = state.file_queue.get(timeout=1)
        except Empty:
            continue

        if item is None:
            state.file_queue.task_done()
            break

        message, is_error = item
        try:
            write_to_file(message, is_error)
        except Exception as e:
            print(f"[pytelegram_logger] Error writing log to file: {e}", file=sys.stderr)
        finally:
            state.file_queue.task_done()


def telegram_worker() -> None:
    """Background worker thread that sends log messages to Telegram."""
    while state.running:
        try:
            item = state.telegram_queue.get(timeout=1)
        except Empty:
            continue

        if item is None:
            state.telegram_queue.task_done()
            break

        message, is_error = item
        try:
            send_telegram(message, is_error)
        except Exception as e:
            print(f"[pytelegram_logger] Error sending log to Telegram: {e}", file=sys.stderr)
        finally:
            state.telegram_queue.task_done()


def cleanup_old_logs() -> None:
    """Delete log files older than the configured retention period."""
    if state.log_dir is None:
        return

    cutoff_date = datetime.now() - timedelta(days=state.retention_days)

    log_pattern = f"{state.name}_logs_*.log"
    error_pattern = f"{state.name}_errors_*.log"

    for pattern in [log_pattern, error_pattern]:
        for log_file in state.log_dir.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_date:
                    log_file.unlink()
            except (OSError, ValueError) as e:
                print(f"[pytelegram_logger] Error deleting old log file {log_file}: {e}", file=sys.stderr)
            except Exception as e:
                print(f"[pytelegram_logger] Unexpected error during cleanup of {log_file}: {e}", file=sys.stderr)


def cleanup_worker() -> None:
    """Background worker thread that periodically cleans up old log files."""
    while state.running:
        time.sleep(3600)
        cleanup_old_logs()


def shutdown_logger() -> None:
    """Gracefully shutdown the logger and close all resources.

    Waits for all queued messages (file and Telegram) to be processed before
    shutting down.
    """
    if not state.running:
        return

    if state.file_queue:
        state.file_queue.join()
    if state.telegram_queue:
        state.telegram_queue.join()

    state.running = False

    if state.file_worker_thread:
        state.file_worker_thread.join(timeout=5)

    if state.telegram_worker_thread:
        state.telegram_worker_thread.join(timeout=5)

    if state.cleanup_thread:
        state.cleanup_thread.join(timeout=1)

    if state.log_file:
        state.log_file.close()
        state.log_file = None

    if state.error_file:
        state.error_file.close()
        state.error_file = None


def _drop_file() -> None:
    """Increment the dropped-file-message counter (thread-safe)."""
    with state.dropped_lock:
        state.dropped_file += 1


def _drop_telegram() -> None:
    """Increment the dropped-Telegram-message counter (thread-safe)."""
    with state.dropped_lock:
        state.dropped_telegram += 1


def get_dropped_count(sink: str | None = None) -> int:
    """Return how many messages were dropped because a queue was full.

    Useful to detect a saturated disk sink or a stuck/down Telegram without
    ever blocking the application. Disk and Telegram are counted separately:
    losing a local log is worse than losing a Telegram notification.

    Args:
        sink: "file" for disk-only, "telegram" for Telegram-only, or None
            (default) for the combined total.

    Returns:
        Number of dropped messages for the requested sink. Returns 0 cleanly
        even if called before init_telegram_logger().

    Raises:
        ValueError: If sink is not None, "file" or "telegram".
    """
    if sink not in (None, "file", "telegram"):
        raise ValueError('sink must be None, "file" or "telegram"')

    with state.dropped_lock:
        if sink == "file":
            return state.dropped_file
        if sink == "telegram":
            return state.dropped_telegram
        return state.dropped_file + state.dropped_telegram


def log(message: str, is_error: bool = False, send_telegram: bool = False, save: bool = True) -> None:
    """Log a message to file and/or Telegram.

    Non-blocking: if a queue is full the message is dropped and counted
    (see get_dropped_count()). Logging must never freeze the caller.

    Args:
        message: The message to log
        is_error: If True, treat as error (different file and Telegram token)
        send_telegram: If True, send notification to Telegram
        save: If True, save to log file; if False, only send to Telegram

    Raises:
        RuntimeError: If logger not initialized
        ValueError: If Telegram is requested but not properly configured
    """
    if not state.running or state.file_queue is None or state.telegram_queue is None:
        raise RuntimeError("Logger not initialized. Call init_telegram_logger() first")

    if send_telegram and not state.telegram_chat_ids:
        raise ValueError("Telegram chat IDs not configured")

    if send_telegram and is_error and not state.telegram_token_errors:
        raise ValueError("Telegram token for errors not configured")

    if send_telegram and not is_error and not state.telegram_token_logs:
        raise ValueError("Telegram token for logs not configured")

    if save:
        try:
            state.file_queue.put_nowait((message, is_error))
        except Full:
            _drop_file()

    if send_telegram:
        try:
            state.telegram_queue.put_nowait((message, is_error))
        except Full:
            _drop_telegram()
