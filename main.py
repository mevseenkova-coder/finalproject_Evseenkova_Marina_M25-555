# main.py

import threading

from valutatrade_hub.cli.interface import main as cli_main
from valutatrade_hub.logging_config import setup_logging
from valutatrade_hub.parser_service.scheduler import start_scheduler


def main():
    print("🚀 ValutaTrade Hub запущен")

    # Запускаем планировщик в фоне
    scheduler_thread = threading.Thread(target=start_scheduler, daemon=True)
    scheduler_thread.start()

    # Запускаем CLI
    cli_main()


if __name__ == "__main__":
    setup_logging()
    main()
