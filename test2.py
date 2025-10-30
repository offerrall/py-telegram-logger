import time
import cProfile
import pstats
import io
from pytelegram_logger import init_telegram_logger, log, shutdown_logger

init_telegram_logger(log_dir=".", name="test")

count = 0
start = time.time()

profiler = cProfile.Profile()
profiler.enable()

while time.time() - start < 5:
    log(f"Test log {count}")
    count += 1

profiler.disable()

elapsed = time.time() - start
logs_per_sec = count / elapsed

print(f"\n{'='*50}")
print(f"Total logs: {count:,}")
print(f"Time: {elapsed:.2f} seconds")
print(f"Logs/second: {logs_per_sec:,.0f}")
print(f"{'='*50}\n")

print("Waiting for queue...")
shutdown_logger()

s = io.StringIO()
ps = pstats.Stats(profiler, stream=s)
ps.strip_dirs()
ps.sort_stats('cumulative')

print("\n" + "="*60)
print("TOP 20 FUNCTIONS BY CUMULATIVE TIME")
print("="*60 + "\n")
ps.print_stats(20)
print(s.getvalue())

s = io.StringIO()
ps = pstats.Stats(profiler, stream=s)
ps.strip_dirs()
ps.sort_stats('time')

print("\n" + "="*60)
print("TOP 20 FUNCTIONS BY SELF TIME")
print("="*60 + "\n")
ps.print_stats(20)
print(s.getvalue())

print("\n" + "="*60)
print("ANALYSIS COMPLETE")
print("="*60)