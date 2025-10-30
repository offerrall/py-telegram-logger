import time
from pytelegram_logger import init_telegram_logger, log, shutdown_logger

# Inicializar (logs en carpeta actual)
init_telegram_logger(log_dir=".", name="test")

# Contar logs
count = 0
start = time.time()

# Loguear durante 5 segundos
while time.time() - start < 5:
    log(f"Test log {count}")
    count += 1

# Resultados
elapsed = time.time() - start
logs_per_sec = count / elapsed

print(f"\n{'='*50}")
print(f"Total logs: {count:,}")
print(f"Time: {elapsed:.2f} seconds")
print(f"Logs/second: {logs_per_sec:,.0f}")
print(f"{'='*50}\n")

# Cerrar limpiamente
shutdown_logger()