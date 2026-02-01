# valutatrade_hub/decorators.py

import functools
import logging
from datetime import datetime
from typing import Any, Dict

# @log_action (логирование операций)

def log_action(action_name: str, verbose: bool = False):
    """
    Декоратор для логирования доменных операций (BUY, SELL и др.).
    :param action_name: тип действия (BUY/SELL/LOGIN)
    :param verbose: добавлять ли контекст (например, баланс)
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger("valutatrade.actions")
            user = getattr(args[0], 'username', 'unknown') if args else 'unknown'
            timestamp = datetime.utcnow().isoformat()

            log_data: Dict[str, Any] = {
                "timestamp": timestamp,
                "action": action_name,
                "username": user,
                "result": "OK"
            }

            # Извлекаем параметры из kwargs (ожидаем: currency_code, amount, rate, base)
            currency_code = kwargs.get("currency_code") or (args[1] if len(args) > 1 else None) # noqa: E501
            amount = kwargs.get("amount") or (args[2] if len(args) > 2 else None)
            rate = kwargs.get("rate")
            base = kwargs.get("base", "USD")

            if currency_code:
                log_data["currency_code"] = currency_code.upper()
            if amount is not None:
                log_data["amount"] = round(float(amount), 6)
            if rate is not None:
                log_data["rate"] = float(rate)
            log_data["base"] = base.upper()

            # Если verbose — можно добавить баланс 
            # (пример: передаём wallet в kwargs или через контекст)
            # Пока оставим заглушку — можно расширить позже
            if verbose and "wallet" in kwargs:
                wallet = kwargs["wallet"]
                log_data["balance_before"] = wallet.balance

            try:
                result = func(*args, **kwargs)

                if verbose and "wallet" in kwargs:
                    log_data["balance_after"] = kwargs["wallet"].balance

                logger.info("", extra=log_data)
                return result

            except Exception as e:
                log_data["result"] = "ERROR"
                log_data["error_type"] = e.__class__.__name__
                log_data["error_message"] = str(e)
                logger.error("", extra=log_data)
                raise  # пробрасываем исключение

        return wrapper
    return decorator
