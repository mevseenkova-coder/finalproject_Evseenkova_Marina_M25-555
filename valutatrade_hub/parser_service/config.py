# valutatrade_hub/parser_service/config.py

import os
from dataclasses import dataclass
from typing import Dict, Tuple
from pathlib import Path

# Загрузка переменных окружения из .env
from dotenv import load_dotenv

# конфигурация API и параметров обновления

'''
EXCHANGE_RATE_API_KEY = "3b47a9b92e1b14c1f1234567"  # ← замени на свой
EXCHANGE_RATE_URL = f"https://v6.exchangerate-api.com/v6/{EXCHANGE_RATE_API_KEY}/latest/USD"

COIN_GECKO_URL = "https://api.coingecko.com/api/v3/simple/price"
'''

# Соответствие тикеров и ID
CRYPTO_ID_MAP = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "ADA": "cardano",
    "DOT": "polkadot"
}

'''
# Валюты для обновления
FIAT_CURRENCIES = ["USD", "EUR", "GBP", "RUB", "JPY", "CAD", "AUD", "CHF"]
CRYPTO_CURRENCIES = ["BTC", "ETH", "SOL"]

# Пути к файлам
EXCHANGE_RATES_FILE = "../data/exchange_rates.json"

# Период обновления (в секундах)
UPDATE_INTERVAL = 600  # каждые 10 минут
'''

# Загружаем .env только если он существует
# Ищем .env в корне проекта (на уровень выше, чем valutatrade_hub/)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    print(f"🔍 Найден .env: {env_path.resolve()}")
    load_dotenv(dotenv_path=env_path)
else:
    print(f"❌ .env не найден: {env_path.resolve()}")
    print("💡 Создай файл .env в корне проекта с содержимым:")
    print("   EXCHANGERATE_API_KEY=твой_ключ")
    print("   COINGECKO_API_KEY=твой_ключ_или_пусто")

# Печатаем переменные для проверки
print("📋 Переменные окружения:")
print(f"  EXCHANGERATE_API_KEY = {os.getenv('EXCHANGERATE_API_KEY')}")
print(f"  COINGECKO_API_KEY = {os.getenv('COINGECKO_API_KEY')}")

# Интервал обновления курсов (в секундах)
try:
    UPDATE_INTERVAL = int(os.getenv("UPDATE_INTERVAL", "3600"))
    if UPDATE_INTERVAL <= 0:
        raise ValueError
    print(f"⏱️ Интервал обновления: {UPDATE_INTERVAL} секунд")
except (ValueError, TypeError):
    print("⚠️ Некорректное значение UPDATE_INTERVAL в .env. Используется значение по умолчанию: 3600 секунд")
    UPDATE_INTERVAL = 3600

@dataclass(frozen=True)  # неизменяемый — безопаснее
class ParserConfig:
    """
    Конфигурация Parser Service.
    Все чувствительные данные — из переменных окружения.
    """

    # --- API Ключи ---
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    COINGECKO_API_KEY: str = os.getenv("COINGECKO_API_KEY", "")  # опционально

    # --- Эндпоинты ---
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # --- Базовая валюта ---
    BASE_CURRENCY: str = "USD"

    # --- Списки валют ---
    FIAT_CURRENCIES: Tuple[str, ...] = (
        "EUR", "GBP", "RUB", "JPY", "CAD", "AUD", "CHF", "CNY", "INR", "BRL"
    )
    CRYPTO_CURRENCIES: Tuple[str, ...] = (
        "BTC", "ETH", "SOL", "ADA", "DOT", "BNB", "XRP", "AVAX", "LINK", "MATIC"
    )

    # --- Сопоставление криптовалют ---
    CRYPTO_ID_MAP: Dict[str, str] = None  # инициализируется в __post_init__

    # --- Пути к файлам ---
    DATA_DIR: Path = Path(__file__).parent.parent / "data"
    RATES_FILE_PATH: Path = DATA_DIR / "rates.json"
    HISTORY_FILE_PATH: Path = DATA_DIR / "exchange_rates.json"

    # --- Сетевые параметры ---
    REQUEST_TIMEOUT: int = 10
    UPDATE_INTERVAL: int = 600  # 10 минут (в секундах)

    def __post_init__(self):
        """Инициализация значений, которые нельзя задать напрямую в dataclass"""
        # Создаём DATA_DIR, если нет
        os.makedirs(self.DATA_DIR, exist_ok=True)

        # Инициализируем CRYPTO_ID_MAP, если не задан
        if ParserConfig.CRYPTO_ID_MAP is None:
            object.__setattr__(self, "CRYPTO_ID_MAP", {
                "BTC": "bitcoin",
                "ETH": "ethereum",
                "SOL": "solana",
                "ADA": "cardano",
                "DOT": "polkadot",
                "BNB": "binancecoin",
                "XRP": "ripple",
                "AVAX": "avalanche-2",
                "LINK": "chainlink",
                "MATIC": "polygon-ecosystem"
            })

    def validate(self) -> bool:
        """Проверить, что конфиг валиден"""
        if not self.EXCHANGERATE_API_KEY:
            print("❌ [Config] Не задан EXCHANGERATE_API_KEY в .env")
            return False
        return True

    '''
    def validate(self) -> bool:
        """Проверить, что конфиг валиден. Всегда возвращает True — сервис не обязателен."""
        if not self.EXCHANGERATE_API_KEY:
            print("⚠️ [Config] EXCHANGERATE_API_KEY не задан — обновление курсов будет отключено")
            return False  # ← можно вернуть False, но не кидать исключение
        return True
    '''

    def validate(self) -> bool:
        """Проверить, что хотя бы один API доступен"""
        has_fiat_key = bool(self.EXCHANGERATE_API_KEY)
        has_crypto_key = bool(self.COINGECKO_API_KEY)

        if not has_fiat_key and not has_crypto_key:
            print("❌ [Config] Не задан ни EXCHANGERATE_API_KEY, ни COINGECKO_API_KEY")
            print("💡 Добавь хотя бы один ключ в .env, чтобы обновлять курсы")
            return False

        if not has_fiat_key:
            print("⚠️ [Config] EXCHANGERATE_API_KEY не задан — обновление фиатных валют отключено")

        if not has_crypto_key:
            print("⚠️ [Config] COINGECKO_API_KEY не задан — обновление криптовалют отключено")

        return True  # ✅ Разрешаем работать, если хотя бы один API есть

# --- Глобальный экземпляр ---
config = ParserConfig()
# === Глобальные алиасы для удобства ===
# Теперь можно писать: from .config import FIAT_CURRENCIES, CRYPTO_CURRENCIES, CRYPTO_ID_MAP

FIAT_CURRENCIES = config.FIAT_CURRENCIES
CRYPTO_CURRENCIES = config.CRYPTO_CURRENCIES
CRYPTO_ID_MAP = config.CRYPTO_ID_MAP

# Если нужно — можно и другие
EXCHANGERATE_API_KEY = config.EXCHANGERATE_API_KEY
COINGECKO_API_KEY = config.COINGECKO_API_KEY
UPDATE_INTERVAL = config.UPDATE_INTERVAL
BASE_CURRENCY = config.BASE_CURRENCY
RATES_FILE_PATH = config.RATES_FILE_PATH
HISTORY_FILE_PATH = config.HISTORY_FILE_PATH
