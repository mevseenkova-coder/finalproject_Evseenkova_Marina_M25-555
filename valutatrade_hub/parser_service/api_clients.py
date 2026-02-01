# valutatrade_hub/parser_service/api_clients.py

from abc import ABC, abstractmethod
from typing import Dict

import requests

from valutatrade_hub.core.exceptions import ApiRequestError

''' from .config import COIN_GECKO_URL, EXCHANGE_RATE_URL, CRYPTO_ID_MAP, 
FIAT_CURRENCIES, CRYPTO_CURRENCIES'''
from .config import config

# работа с внешними API
'''
def fetch_crypto_prices() -> Optional[Dict[str, float]]:
    ids = ",".join(CRYPTO_ID_MAP.values())
    try:
        response = requests.get(
            COIN_GECKO_URL,
            params={"ids": ids, "vs_currencies": "usd"},
            timeout=10
        )
        response.raise_for_status()
        data = response.json()
        return {code: data[coin_id]["usd"] for code, coin_id in CRYPTO_ID_MAP.items() 
            if coin_id in data} # noqa: E501
    except Exception as e:
        print(f"❌ Ошибка при запросе к CoinGecko: {e}")
        return None
'''

'''
def fetch_fiat_rates() -> Optional[Dict[str, float]]:
    try:
        url = f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/latest/
            {config.BASE_CURRENCY}" # noqa: E501
        # response = requests.get(EXCHANGE_RATE_URL, timeout=10)
        response = requests.get(url, timeout=10)
        if response.status_code == 429:
            print("❌ Лимит ExchangeRate-API превышен (429)")
            return None
        response.raise_for_status()
        data = response.json()
        if data.get("result") == "success":
            return data["rates"]
        return None
    except Exception as e:
        print(f"❌ Ошибка при запросе к ExchangeRate-API: {e}")
        return None
'''

# --- Абстрактный базовый класс ---
class BaseApiClient(ABC):
    """Абстрактный клиент для получения курсов валют"""

    @abstractmethod
    def fetch_rates(self) -> Dict[str, float]:
        """
        Получить курсы в формате:
        {"BTC_USD": 59337.21, "ETH_USD": 2345.67, ...}
        """
        pass


# --- Клиент для CoinGecko ---
class CoinGeckoClient(BaseApiClient):
    def __init__(self):
        self.url = config.COINGECKO_URL
        self.headers = {}
        if config.COINGECKO_API_KEY:
            self.headers["x-cg-demo-api-key"] = config.COINGECKO_API_KEY

    def fetch_rates(self) -> Dict[str, float]:
        ids = ",".join(config.CRYPTO_ID_MAP[c] for c in config.CRYPTO_CURRENCIES)
        params = {
            "ids": ids,
            "vs_currencies": config.BASE_CURRENCY.lower()
        }

        try:
            response = requests.get(
                self.url,
                params=params,
                headers=self.headers,
                timeout=config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            result = {}
            for code in config.CRYPTO_CURRENCIES:
                coin_id = config.CRYPTO_ID_MAP[code]
                if coin_id in data and config.BASE_CURRENCY.lower() in data[coin_id]:
                    rate = data[coin_id][config.BASE_CURRENCY.lower()]
                    if isinstance(rate, (int, float)) and rate > 0:
                        pair = f"{code}_{config.BASE_CURRENCY}"
                        result[pair] = float(rate)
            return result

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса к CoinGecko: {e}")
        except KeyError as e:
            raise ApiRequestError(f"Ошибка парсинга ответа CoinGecko: отсутствует поле {e}") # noqa: E501
        except Exception as e:
            raise ApiRequestError(f"Неизвестная ошибка при работе с CoinGecko: {e}")


# --- Клиент для ExchangeRate-API ---
class ExchangeRateApiClient(BaseApiClient):
    def __init__(self):
        if not config.EXCHANGERATE_API_KEY:
            raise ValueError("ExchangeRateApiClient: EXCHANGERATE_API_KEY не задан")
        self.url = f"{config.EXCHANGERATE_API_URL}/{config.EXCHANGERATE_API_KEY}/latest/{config.BASE_CURRENCY}" # noqa: E501

    def fetch_rates(self) -> Dict[str, float]:
        try:
            response = requests.get(self.url, timeout=config.REQUEST_TIMEOUT)
            response.raise_for_status()
            data = response.json()

            if data.get("result") != "success":
                error = data.get("error-type", "unknown")
                if error == "invalid-key":
                    raise ApiRequestError("ExchangeRate-API: неверный API-ключ")
                elif error == "quota-reached":
                    raise ApiRequestError("ExchangeRate-API: достигнут лимит запросов")
                else:
                    raise ApiRequestError(f"ExchangeRate-API: {error}")

            result = {}
            # rates = data.get("rates", {})
            rates = data.get("conversion_rates", {})
            for code in config.FIAT_CURRENCIES:
                if code == config.BASE_CURRENCY:
                    continue  # пропускаем базовую
                if code in rates:
                    rate = rates[code]
                    if isinstance(rate, (int, float)) and rate > 0:
                        pair = f"{code}_{config.BASE_CURRENCY}"
                        result[pair] = float(rate)
            return result

        except requests.exceptions.RequestException as e:
            raise ApiRequestError(f"Ошибка запроса к ExchangeRate-API: {e}")
        except KeyError as e:
            raise ApiRequestError(f"Ошибка парсинга ответа ExchangeRate-API: отсутствует поле {e}") # noqa: E501
        except Exception as e:
            raise ApiRequestError(f"Неизвестная ошибка при работе с ExchangeRate-API: {e}") # noqa: E501
