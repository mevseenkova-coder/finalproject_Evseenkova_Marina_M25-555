# valutatrade_hub/infra/database.py

import json
import os
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

from valutatrade_hub.core.models import User, Portfolio, Wallet
from valutatrade_hub.infra.settings import SettingsLoader

# Singleton DatabaseManager (абстракция над JSON-хранилищем)

class DatabaseManager:
    def __init__(self):
        self.settings = SettingsLoader()
        self.data_dir = self.settings.get("data_dir", "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.users_file = os.path.join(self.data_dir, "users.json")
        self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
        self.rates_file = os.path.join(self.data_dir, "rates.json")

    def load_users(self) -> List[User]:
        if not os.path.exists(self.users_file):
            return []
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return [User.from_dict(item) for item in data]
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️ Ошибка загрузки users.json: {e}")
            return []

    '''
    def load_users_dict(self) -> Dict[int, User]:
        """Загружает пользователей в виде словаря user_id → User"""
        if not os.path.exists(self.users_file):
            return {}
        try:
            with open(self.users_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            users = {}
            for item in data:
                user = User.from_dict(item)
                users[user.user_id] = user
            return users
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️ Ошибка загрузки users.json: {e}")
            return {}

    def save_user(self, user: User):
        users = self.load_users_dict()
        users[user.user_id] = user
        self._safe_write(self.users_file, [u.to_dict() for u in users.values()])
    '''

    def save_user(self, user: User):
        users = [u for u in self.load_users() if u.user_id != user.user_id]
        users.append(user)
        self._safe_write(self.users_file, [u.to_dict() for u in users])

    '''
    def load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = self.load_portfolios()
        return portfolios.get(user_id, Portfolio(user_id=user_id, wallets=[]))
    '''
    
    def load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = self.load_portfolios()
        if user_id in portfolios:
            return portfolios[user_id]
        print(f"🔧 Портфель для user_id={user_id} не найден — создан пустой")
        return Portfolio(user_id=user_id)

    def load_portfolios(self) -> Dict[int, Portfolio]:
        if not os.path.exists(self.portfolios_file):
            return {}
        try:
            with open(self.portfolios_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            portfolios = {}
            for item in data:
                p = Portfolio.from_dict(item)
                portfolios[p.user_id] = p
            return portfolios
        except (json.JSONDecodeError, KeyError, TypeError) as e:
            print(f"⚠️ Ошибка загрузки portfolios.json: {e}")
            return {}

    def save_portfolio(self, portfolio: Portfolio):
        portfolios = self.load_portfolios()
        portfolios[portfolio.user_id] = portfolio
        self._safe_write(self.portfolios_file, [p.to_dict() for p in portfolios.values()])

    def load_rates(self) -> Dict[str, float]:
        """Загружает курсы с учётом TTL из settings."""
        ttl = self.settings.get("rates_ttl_seconds", 300)
        now = datetime.now()

        if not os.path.exists(self.rates_file):
            return self._default_rates()

        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_updated = datetime.fromisoformat(data.get("last_updated", now.isoformat()))
            if now - last_updated > timedelta(seconds=ttl):
                print("🕒 Курсы устарели — нужно обновить")
                return self._default_rates()  # или бросить исключение, если нужно
            raw_rates = data
        except (json.JSONDecodeError, OSError):
            return self._default_rates()

        # Парсим формат ParserService: "BTC_USD": { "rate": "60000" } → "BTC": 60000.0
        rates = {"USD": 1.0}
        for pair, info in raw_rates.items():
            if isinstance(info, dict) and "rate" in info and pair.endswith("_USD"):
                currency = pair.split("_")[0]
                try:
                    rates[currency] = float(info["rate"])
                except (ValueError, TypeError):
                    continue
        return rates

    def save_rates_with_timestamp(self, rates: Dict[str, float]):
        data = {**rates, "last_updated": datetime.now().isoformat()}
        self._safe_write(self.rates_file, data)

    def _safe_write(self, file_path: str, data: any):
        """Безопасная запись с резервной копией."""
        backup = file_path + ".backup"
        if os.path.exists(file_path):
            os.replace(file_path, backup)
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ Ошибка записи {file_path}: {e}")
            if os.path.exists(backup):
                os.replace(backup, file_path)
                print("✅ Восстановлено из бэкапа")

    def _default_rates(self) -> Dict[str, float]:
        return {
            "USD": 1.0,
            "EUR": 1.07,
            "BTC": 60000.0,
            "ETH": 3000.0,
            "RUB": 95.0
        }

    def load_rates_with_timestamp(self) -> Tuple[Dict[str, float], datetime]:
        """Загружает курсы и время последнего обновления"""
        ttl = self.settings.get("rates_ttl_seconds", 300)
        now = datetime.now()

        if not os.path.exists(self.rates_file):
            return self._default_rates(), now

        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_updated_str = data.get("last_updated")
            last_updated = datetime.fromisoformat(last_updated_str) if last_updated_str else now

            if now - last_updated > timedelta(seconds=ttl):
                print("🕒 Курсы устарели — нужно обновить")
                return self._default_rates(), now

            # Парсим курсы
            rates = {"USD": 1.0}
            for pair, info in data.items():
                if isinstance(info, dict) and "rate" in info and pair.endswith("_USD"):
                    currency = pair.split("_")[0]
                    try:
                        rates[currency] = float(info["rate"])
                    except (ValueError, TypeError):
                        continue
            return rates, last_updated

        except (json.JSONDecodeError, OSError) as e:
            print(f"⚠️ Ошибка чтения {self.rates_file}: {e}")
            return self._default_rates(), now

    '''
    # Перенос из модуля interface.py

    def load_rates_with_timestamp() -> tuple[dict, datetime]:
        """Загружает курсы и время последнего обновления"""
        if not os.path.exists(RATES_FILE):
            # Возвращаем дефолтные значения
            rates = {
                "USD": 1.0, "EUR": 1.07, "GBP": 1.25,
                "JPY": 0.0067, "BTC": 60000.0, "ETH": 3000.0
            }
            return rates, datetime.now()

        with open(RATES_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        rates = {k: v for k, v in data.items() if k != "last_updated"}
        last_updated = datetime.fromisoformat(data["last_updated"])
        return rates, last_updated
    '''