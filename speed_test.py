import time
from pytelegram_logger import init_telegram_logger, log, shutdown_logger

init_telegram_logger(log_dir=".", name="test")

count = 0
start = time.time()

while time.time() - start < 5:
    log(f"Test log {count}")
    count += 1

elapsed = time.time() - start
logs_per_sec = count / elapsed

print(f"\n{'='*50}")
print(f"Total logs: {count:,}")
print(f"Time: {elapsed:.2f} seconds")
print(f"Logs/second: {logs_per_sec:,.0f}")
print(f"{'='*50}\n")

shutdown_logger()