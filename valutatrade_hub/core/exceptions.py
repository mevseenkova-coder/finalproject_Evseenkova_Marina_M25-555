# valutatrade_hub/core/exceptions.py

# Пользовательские исключения

class ValutaTradeError(Exception):
    """Базовый класс для всех исключений приложения."""
    pass


class InsufficientFundsError(ValutaTradeError):
    """
    Исключение: недостаточно средств на кошельке.
    Выбрасывается при попытке снять или продать больше, чем есть.
    """
    def __init__(self, available: float, required: float, code: str):
        self.available = available
        self.required = required
        self.code = code
        message = f"Недостаточно средств: доступно {available:,.6f} {code}, требуется {required:,.6f} {code}"
        super().__init__(message)


class CurrencyNotFoundError(ValutaTradeError):
    """
    Исключение: валюта с таким кодом не поддерживается.
    Выбрасывается при поиске валюты по коду.
    """
    def __init__(self, code: str):
        self.code = code
        message = f"Неизвестная валюта '{code}'"
        super().__init__(message)


class ApiRequestError(ValutaTradeError):
    """
    Исключение: ошибка при обращении к внешнему API.
    Выбрасывается при сбое загрузки курсов.
    """
    def __init__(self, reason: str):
        self.reason = reason
        message = f"Ошибка при обращении к внешнему API: {reason}"
        super().__init__(message)


class UserAlreadyExistsError(ValutaTradeError):
    """
    Исключение: пользователь с таким именем уже существует.
    Выбрасывается при попытке зарегистрировать уже существующее имя.
    """
    def __init__(self, username: str):
        self.username = username
        message = f"Пользователь с именем '{username}' уже существует"
        super().__init__(message)
