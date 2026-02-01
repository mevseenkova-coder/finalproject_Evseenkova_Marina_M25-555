# valutatrade_hub/parser_service/updater.py

from datetime import datetime, timezone
import logging
from typing import List, Dict, Any

from .config import config
from .api_clients import CoinGeckoClient, ExchangeRateApiClient, BaseApiClient
from .storage import save_rates_snapshot
from valutatrade_hub.core.exceptions import ApiRequestError

logger = logging.getLogger(__name__)


def generate_id(from_curr: str, to_curr: str, timestamp: str) -> str:
    """Создать уникальный ID: BTC_USD_2025-10-10T12:00:00Z"""
    return f"{from_curr}_{to_curr}_{timestamp}"


class RatesUpdater:
    """
    Координирует обновление курсов:
    - Опрашивает API-клиентов
    - Объединяет результаты
    - Сохраняет снимок в rates.json
    """
    def __init__(self, clients: List[BaseApiClient] = None):
        self.pairs: Dict[str, Dict[str, Any]] = {}
        self.timestamp = self._now_iso()

        if clients is not None:
            self.clients = clients
        else:
            self.clients = []

            # Добавляем клиентов, если ключи есть
            if config.EXCHANGERATE_API_KEY:
                try:
                    self.clients.append(ExchangeRateApiClient())
                    logger.info("ExchangeRateApiClient добавлен")
                except Exception as e:
                    logger.warning(f"Не удалось добавить ExchangeRateApiClient: {e}")

            try:
                self.clients.append(CoinGeckoClient())
                logger.info("CoinGeckoClient добавлен")
            except Exception as e:
                logger.warning(f"Не удалось добавить CoinGeckoClient: {e}")

    def _now_iso(self) -> str:
        """Текущее время в UTC, ISO 8601 с Z"""
        dt = datetime.now(timezone.utc)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + "Z"

    def run_update(self) -> bool:
        """Запустить обновление курсов"""
        print("🔄 [Updater] Запуск обновления курсов...")
        success = False

        for client in self.clients:
            client_name = client.__class__.__name__.replace("Client", "")
            print(f"📡 [Updater] Запрос к {client_name}...")

            try:
                rates = client.fetch_rates()
                if not rates:
                    print(f"🟡 [Updater] {client_name}: получено 0 курсов")
                    continue

                source = "CoinGecko" if "CoinGecko" in client_name else "ExchangeRate-API"

                for pair, rate in rates.items():
                    self.pairs[pair] = {
                        "rate": rate,
                        "updated_at": self.timestamp,
                        "source": source
                    }

                print(f"✅ [Updater] {client_name}: получено {len(rates)} курсов")

            except ApiRequestError as e:
                print(f"❌ [Updater] Ошибка {client_name}: {e}")
                logger.error(f"Ошибка в run_update: {client_name}: {e}")
                continue

            except Exception as e:
                print(f"❌ [Updater] Неизвестная ошибка {client_name}: {e}")
                logger.error(f"Неизвестная ошибка в run_update: {client_name}: {e}")
                continue

        if not self.pairs:
            print("❌ [Updater] Не удалось получить ни одного курса")
            return False

        # Сохраняем снимок
        try:
            if save_rates_snapshot(self.pairs, self.timestamp):
                print(f"💾 [Updater] Успешно сохранено {len(self.pairs)} пар в rates.json")
                success = True
            else:
                print("❌ [Updater] Не удалось сохранить снимок")
        except Exception as e:
            print(f"❌ [Updater] Ошибка при сохранении: {e}")
            logger.error(f"Ошибка при сохранении снимка: {e}")

        print("✅ [Updater] Обновление завершено." if success else "⚠️ [Updater] Обновление частично неудачно.")
        return success


def update_rates() -> bool:
    """Обновить курсы и сохранить как снимок в rates.json"""
    print("🔄 [Updater] Запрос актуальных курсов...")

    if not config.validate():
        print("⚠️ [Updater] Обновление отключено: нет доступных API-ключей")
        return False

    updater = RatesUpdater()
    return updater.run_update()
