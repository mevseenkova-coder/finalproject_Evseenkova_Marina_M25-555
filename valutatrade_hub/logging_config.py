# valutatrade_hub/logging_config.py

import logging
from logging.handlers import RotatingFileHandler
import os

# Настройка логов (формат, уровень, ротация)

def setup_logging():
    """
    Настраивает логирование:
    - Формат: JSON
    - Ротация: 10 МБ, 5 архивов
    - Уровень: INFO
    """
    os.makedirs("logs", exist_ok=True)

    logger = logging.getLogger("valutatrade.actions")
    logger.setLevel(logging.INFO)
    logger.propagate = False  # не дублировать в root

    if logger.handlers:
        logger.handlers.clear()

    handler = RotatingFileHandler(
        "logs/actions.log",
        maxBytes=10 * 1024 * 1024,  # 10 МБ
        backupCount=5
    )

    # JSON-формат — удобно для ELK, Grafana, парсинга
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
                "level": record.levelname,
                "action": getattr(record, "action", "UNKNOWN"),
                "username": getattr(record, "username", "unknown"),
                "result": getattr(record, "result", "OK")
            }
            # Добавляем остальные поля
            for key in ["currency_code", "amount", "rate", "base", "error_type", "error_message", "balance_before", "balance_after"]:
                if hasattr(record, key):
                    log_entry[key] = getattr(record, key)
            return str(log_entry)

    handler.setFormatter(JsonFormatter())
    logger.addHandler(handler)
