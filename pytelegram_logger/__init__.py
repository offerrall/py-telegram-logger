import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue, Empty
import requests
from dataclasses import dataclass, field

__all__ = ['init_telegram_logger', 'log', 'shutdown_logger']


@dataclass
class LoggerState:
    log_dir: Path | None = None
    telegram_token_logs: str | None = None
    telegram_token_errors: str | None = None
    telegram_chat_ids: list = field(default_factory=list)
    retention_days: int = 30
    name: str = ""
    queue: Queue | None = None
    running: bool = False
    worker_thread: threading.Thread | None = None
    cleanup_thread: threading.Thread | None = None
    
    log_file: object = None
    error_file: object = None
    current_log_path: str = ""
    current_error_path: str = ""
    
    cached_date: str = ""
    cached_log_path: Path | None = None
    cached_error_path: Path | None = None


state = LoggerState()


def init_telegram_logger(
    log_dir: str = "logs",
    telegram_token_logs: str | None = None,
    telegram_token_errors: str | None = None,
    telegram_chat_ids: list | None = None,
    retention_days: int = 30,
    name: str = ""
):
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
    
    state.queue = Queue(maxsize=10000)
    state.running = True
    
    state.worker_thread = threading.Thread(target=worker, daemon=True)
    state.worker_thread.start()
    
    state.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    state.cleanup_thread.start()


def get_daily_file(is_error: bool = False) -> Path:
    now = datetime.now()
    date_str = f"{now.year}_{now.month:02d}_{now.day:02d}"
    
    if state.cached_date != date_str:
        prefix_log = "logs"
        prefix_error = "errors"
        
        if state.name:
            state.cached_log_path = state.log_dir / f"{state.name}_{prefix_log}_{date_str}.log"
            state.cached_error_path = state.log_dir / f"{state.name}_{prefix_error}_{date_str}.log"
        else:
            state.cached_log_path = state.log_dir / f"{prefix_log}_{date_str}.log"
            state.cached_error_path = state.log_dir / f"{prefix_error}_{date_str}.log"
        
        state.cached_date = date_str
    
    return state.cached_error_path if is_error else state.cached_log_path


def write_to_file(message: str, is_error: bool = False):
    filepath = get_daily_file(is_error)
    filepath_str = str(filepath)
    
    now = datetime.now()
    timestamp = '%04d-%02d-%02d %02d:%02d:%02d' % (now.year, now.month, now.day, now.hour, now.minute, now.second)
    
    if is_error:
        if state.current_error_path != filepath_str:
            if state.error_file:
                state.error_file.close()
            state.error_file = open(filepath, "a", encoding="utf-8", buffering=8192)
            state.current_error_path = filepath_str
        
        file_handle = state.error_file
    else:
        if state.current_log_path != filepath_str:
            if state.log_file:
                state.log_file.close()
            state.log_file = open(filepath, "a", encoding="utf-8", buffering=8192)
            state.current_log_path = filepath_str
        
        file_handle = state.log_file
    
    file_handle.write(f"[{timestamp}] {message}\n")
    file_handle.flush()


def send_telegram(message: str, is_error: bool = False):
    token = state.telegram_token_errors if is_error else state.telegram_token_logs
    
    if not token or not state.telegram_chat_ids:
        return
    
    log_type = "🔴 ERROR" if is_error else "ℹ️ LOG"
    full_message = f"{log_type}\n\n{message}"
    
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    
    for chat_id in state.telegram_chat_ids:
        try:
            data = {
                "chat_id": chat_id,
                "text": full_message,
                "parse_mode": "HTML"
            }
            requests.post(url, json=data, timeout=5)
            time.sleep(0.05)
        except:
            pass


def worker():
    while state.running:
        try:
            item = state.queue.get(timeout=1)
            
            if item is None:
                break
            
            message, is_error, send_telegram_flag, save_file = item
            
            try:
                if save_file:
                    write_to_file(message, is_error)
                
                if send_telegram_flag:
                    send_telegram(message, is_error)
            except:
                pass
            finally:
                state.queue.task_done()
                
        except Empty:
            continue


def cleanup_old_logs():
    if state.log_dir is None:
        return
    
    cutoff_date = datetime.now() - timedelta(days=state.retention_days)
    
    # Only delete logs that belong to this logger instance
    log_pattern = f"{state.name}_logs_*.log"
    error_pattern = f"{state.name}_errors_*.log"
    
    for pattern in [log_pattern, error_pattern]:
        for log_file in state.log_dir.glob(pattern):
            try:
                mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
                if mtime < cutoff_date:
                    log_file.unlink()
            except:
                pass


def cleanup_worker():
    while state.running:
        time.sleep(3600)
        cleanup_old_logs()


def shutdown_logger():
    if not state.running:
        return
    
    if state.queue:
        state.queue.join()
    
    state.running = False
    
    if state.log_file:
        state.log_file.close()
        state.log_file = None
    
    if state.error_file:
        state.error_file.close()
        state.error_file = None
    
    if state.worker_thread:
        state.worker_thread.join(timeout=5)
    
    if state.cleanup_thread:
        state.cleanup_thread.join(timeout=1)


def log(message: str, is_error: bool = False, send_telegram: bool = False, save: bool = True):
    if not state.running or state.queue is None:
        raise RuntimeError("Logger not initialized. Call init_telegram_logger() first")
    
    if send_telegram and not state.telegram_chat_ids:
        raise ValueError("Telegram chat IDs not configured")
    
    if send_telegram and is_error and not state.telegram_token_errors:
        raise ValueError("Telegram token for errors not configured")
    
    if send_telegram and not is_error and not state.telegram_token_logs:
        raise ValueError("Telegram token for logs not configured")

    state.queue.put((message, is_error, send_telegram, save))