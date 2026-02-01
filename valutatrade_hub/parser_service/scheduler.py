# valutatrade_hub/parser_service/scheduler.py

import time
import logging
from .updater import update_rates
from .config import config

logger = logging.getLogger(__name__)

def start_scheduler() -> None:
    """Запустить автоматическое обновление по расписанию"""
    if not config.validate():
        logger.info("⏰ Parser Service отключён. Работа с локальными данными.")
        print("⚠️ Parser Service отключён. Используйте локальные данные или добавьте API-ключи.")
        return

    print(f"⏰ [Scheduler] Запущен. Обновление каждые {config.UPDATE_INTERVAL // 60} минут.")
    logger.info("Scheduler запущен", extra={"interval_minutes": config.UPDATE_INTERVAL // 60})

    # Первое обновление
    update_rates()

    # Цикл
    while True:
        time.sleep(config.UPDATE_INTERVAL)
        update_rates()
