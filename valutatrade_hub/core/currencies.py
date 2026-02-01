# valutatrade_hub/core/currencies.py

from abc import ABC, abstractmethod
from typing import Dict

# Базовый класс Currency и наследники Fiat/Crypto

# === Исключение ===
class CurrencyNotFoundError(Exception):
    """
    Исключение, выбрасываемое, когда валюта с указанным кодом не найдена в реестре.
    
    Атрибуты:
        code (str): Код валюты, который не был найден.
    """
    def __init__(self, code: str):
        self.code = code
        message = f"Валюта с кодом '{code}' не найдена. Проверьте правильность написания или используйте команду 'currencies' для просмотра доступных." # noqa: E501
        super().__init__(message)


class Currency(ABC):
    """
    Абстрактный базовый класс для всех типов валют.
    """

    def __init__(self, name: str, code: str):
        # Валидация
        if not name or not isinstance(name, str):
            raise ValueError("Имя валюты должно быть непустой строкой.")
        if not isinstance(code, str) or not (2 <= len(code) <= 5) or " " in code or not code.isupper(): # noqa: E501
            raise ValueError("Код валюты: 2–5 символов, только верхний регистр, без пробелов.") # noqa: E501

        self.name: str = name
        self.code: str = code

    @abstractmethod
    def get_display_info(self) -> str:
        """Возвращает строку с информацией о валюте (для UI/логов)."""
        pass

    def __str__(self) -> str:
        return self.get_display_info()

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} {self.code}>"

class FiatCurrency(Currency):
    """
    Фиатная валюта.
    """

    def __init__(self, name: str, code: str, issuing_country: str):
        super().__init__(name, code)
        if not issuing_country or not isinstance(issuing_country, str):
            raise ValueError("Страна эмиссии должна быть непустой строкой.")
        self.issuing_country: str = issuing_country

    def get_display_info(self) -> str:
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    """
    Криптовалюта.
    """

    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        super().__init__(name, code)
        if not algorithm or not isinstance(algorithm, str):
            raise ValueError("Алгоритм должен быть непустой строкой.")
        if market_cap < 0:
            raise ValueError("Рыночная капитализация не может быть отрицательной.")

        self.algorithm: str = algorithm
        self.market_cap: float = market_cap

    def get_display_info(self) -> str:
        # Форматируем капитализацию: 1.12e12
        mcap_str = f"{self.market_cap:.2e}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {mcap_str})" # noqa: E501

# === Алиасы ДО функции get_currency ===
CURRENCY_ALIASES = {
    "RUR": "RUB",
    "USDT": "USD",
    "EURO": "EUR",
}

# Реестр валют
_CURRENCIES_REGISTRY: Dict[str, Currency] = {
    "USD": FiatCurrency("US Dollar", "USD", "United States"),
    "EUR": FiatCurrency("Euro", "EUR", "Eurozone"),
    "GBP": FiatCurrency("British Pound", "GBP", "United Kingdom"),
    "JPY": FiatCurrency("Japanese Yen", "JPY", "Japan"),
    "RUB": FiatCurrency("Russian Ruble", "RUB", "Russia"),

    "BTC": CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12),
    "ETH": CryptoCurrency("Ethereum", "ETH", "Ethash", 4.35e11),
    "BTS": CryptoCurrency("BitShares", "BTS", "DPoS", 1.5e8),
}

def get_currency(code: str) -> Currency:
    """
    Фабричный метод: возвращает экземпляр Currency по коду.
    :param code: код валюты (например, "USD", "BTC")
    :return: объект Currency
    :raises CurrencyNotFoundError: если код не найден
    """
    code = code.strip().upper()
    code = CURRENCY_ALIASES.get(code, code)
    currency = _CURRENCIES_REGISTRY.get(code)
    if currency is None:
        raise CurrencyNotFoundError(f"Валюта с кодом '{code}' не найдена.")
    return currency

