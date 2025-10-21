import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from queue import Queue, Empty
import requests
from dataclasses import dataclass, field

__all__ = ['init_telegram_logger', 'log']


@dataclass
class LoggerState:
    log_dir: Path | None = None
    telegram_token_logs: str | None = None
    telegram_token_errors: str | None = None
    telegram_chat_ids: list = field(default_factory=list)
    retention_days: int = 30
    queue: Queue | None = None
    running: bool = False
    worker_thread: threading.Thread | None = None
    cleanup_thread: threading.Thread | None = None


state = LoggerState()


def init_telegram_logger(
    log_dir: str = "logs",
    telegram_token_logs: str | None = None,
    telegram_token_errors: str | None = None,
    telegram_chat_ids: list | None = None,
    retention_days: int = 30
):
    if state.running:
        return
    
    state.log_dir = Path(log_dir)
    state.log_dir.mkdir(exist_ok=True)
    
    state.telegram_token_logs = telegram_token_logs
    state.telegram_token_errors = telegram_token_errors
    state.telegram_chat_ids = telegram_chat_ids or []
    state.retention_days = retention_days
    
    state.queue = Queue(maxsize=10000)
    state.running = True
    
    state.worker_thread = threading.Thread(target=worker, daemon=True)
    state.worker_thread.start()
    
    state.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
    state.cleanup_thread.start()


def get_daily_file(is_error: bool = False) -> Path:
    now = datetime.now()
    prefix = "errors" if is_error else "logs"
    filename = f"{prefix}_{now.year}_{now.month:02d}_{now.day:02d}.log"
    return state.log_dir / filename


def write_to_file(message: str, is_error: bool = False):
    filepath = get_daily_file(is_error)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_type = "ERROR" if is_error else "INFO"
    
    with open(filepath, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] [{log_type}] {message}\n")


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
            
            if save_file:
                write_to_file(message, is_error)
            
            if send_telegram_flag:
                send_telegram(message, is_error)
            
            state.queue.task_done()
        except Empty:
            continue
        except:
            continue


def cleanup_old_logs():
    if state.log_dir is None:
        return
    
    cutoff_date = datetime.now() - timedelta(days=state.retention_days)
    
    for log_file in state.log_dir.glob("*.log"):
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


def log(message: str, is_error: bool = False, send_telegram: bool = False, save: bool = True):
    if not state.running or state.queue is None:
        raise RuntimeError("Logger not initialized. Call init_telegram_logger() first")
    
    state.queue.put((message, is_error, send_telegram, save))