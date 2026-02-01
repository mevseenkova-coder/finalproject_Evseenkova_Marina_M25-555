# valutatrade_hub/infra/database.py

import json
import os
from datetime import datetime, timedelta

# infra/database.py
from pathlib import Path
from typing import Dict, List, Tuple

from valutatrade_hub.core.models import Portfolio, User
from valutatrade_hub.infra.settings import SettingsLoader


class JsonDatabase:
    def __init__(self, filepath: str):
        self.path = Path(filepath)
        self.path.parent.mkdir(exist_ok=True)
        if not self.path.exists():
            self.path.write_text("{}")

    def read(self) -> dict:
        return json.loads(self.path.read_text())

    def write(self, data: dict) -> None:
        self.path.write_text(json.dumps(data, indent=2))

# Singleton DatabaseManager (абстракция над JSON-хранилищем)
class DatabaseManager:
    def __init__(self):
        self.settings = SettingsLoader()

        # Получаем data_dir из настроек
        data_dir = self.settings.get("data_dir", "data")

        # Преобразуем в абсолютный путь: если относительный — считаем от корня проекта
        project_root = Path(__file__).parent.parent.parent 
        # valutatrade_hub → finalproject_...
        self.data_dir = str(project_root / data_dir)

        os.makedirs(self.data_dir, exist_ok=True)

        self.users_file = os.path.join(self.data_dir, "users.json")
        self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
        self.rates_file = os.path.join(self.data_dir, "rates.json")

        '''
        self.settings = SettingsLoader()
        self.data_dir = self.settings.get("data_dir", "data")
        os.makedirs(self.data_dir, exist_ok=True)

        self.users_file = os.path.join(self.data_dir, "users.json")
        self.portfolios_file = os.path.join(self.data_dir, "portfolios.json")
        self.rates_file = os.path.join(self.data_dir, "rates.json")
        '''
        '''
        self.settings = SettingsLoader()
        # Получаем data_dir из настроек
        data_dir = self.settings.get("data_dir", "data")
        # Преобразуем в абсолютный путь: считаем от корня проекта
        project_root = Path(__file__).resolve().parent.parent.parent
        self.data_dir = project_root / data_dir  # Path, не строка
        self.data_dir.mkdir(exist_ok=True)

        # Используем / вместо os.path.join
        self.users_file = self.data_dir / "users.json"
        self.portfolios_file = self.data_dir / "portfolios.json"
        self.rates_file = self.data_dir / "rates.json"

        print(f"📁 [DatabaseManager] Рабочая директория: {self.data_dir.resolve()}")
        '''

        # 🔍 Отладка: покажем, куда мы пишем        
        print(f"📁 [DatabaseManager] Рабочая директория: {self.data_dir}")
        print(f"💾 users.json: {self.users_file}")
        print(f"💼 portfolios.json: {self.portfolios_file}")
        print(f"💱 rates.json: {self.rates_file}")
        

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
    
    '''
    def load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = self.load_portfolios()
        return portfolios.get(user_id, Portfolio(user_id=user_id, wallets=[]))
    '''
    
    def load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = self.load_portfolios()
        if user_id in portfolios:
            return portfolios[user_id]
        # Если портфель не найден — возвращаем пустой (без магии!)
        print(f"🔧 Портфель для user_id={user_id} не найден — создан пустой")
        return Portfolio(user_id=user_id)
    
    '''
    def load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = self.load_portfolios()
        if user_id in portfolios:
            return portfolios[user_id]

        print(f"🔧 Портфель для user_id={user_id} не найден — создаём новый 
            с начальным капиталом") # noqa: E501
        portfolio = Portfolio(user_id=user_id)

        # Добавляем стартовый капитал
        usd_wallet = Wallet(currency_code="USD", balance=1000.0)
        portfolio.add_wallet(usd_wallet)

        # Сохраняем в память и на диск
        portfolios[user_id] = portfolio
        self.save_portfolio(portfolio)

        return portfolio
    '''
    '''
    def load_portfolio(self, user_id: int) -> Portfolio:
        portfolios = self.load_portfolios()
        if user_id in portfolios:
            return portfolios[user_id]

        print(f"🔧 Портфель для user_id={user_id} не найден — создаём новый 
            с начальным капиталом") # noqa: E501
        portfolio = Portfolio(user_id=user_id)

        # Добавляем стартовый капитал
        portfolio.add_currency("USD", initial_balance=1000.0)

        # Сохраняем
        portfolios[user_id] = portfolio
        self.save_portfolio(portfolio)

        return portfolio
    '''
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
        self._safe_write(self.portfolios_file, [p.to_dict() for p in portfolios.values()]) # noqa: E501

    '''
    def load_rates(self) -> Dict[str, float]:
        """Загружает курсы с учётом TTL из settings."""
        ttl = self.settings.get("rates_ttl_seconds", 300)
        now = datetime.now()

        if not os.path.exists(self.rates_file):
            return self._default_rates()

        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            last_updated = datetime.fromisoformat(data.get("last_updated", 
                now.isoformat())) # noqa: E501
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
    '''
    '''
    def load_rates(self) -> Dict[str, float]:
        """
        Возвращает словарь вида: {"EUR": 1.0786, "BTC": 59337.21, "USD": 1.0}
        На основе формата:
        {"pairs": {"EUR_USD": {"rate": 1.0786, ...}}}
        """
        if not os.path.exists(self.rates_file):
            # Дефолтные курсы на случай отсутствия файла
            return {
                "USD": 1.0,
                "EUR": 1.07,
                "BTC": 60000.0,
                "ETH": 3000.0,
                "GBP": 1.25,
                "JPY": 0.0067,
                "RUB": 95.0
            }

        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Ошибка чтения rates.json: {e}")
            return {"USD": 1.0}
        # Новый формат: пары вида "EUR_USD"
        rates = {}
        pairs = data.get("pairs", {})

        for pair, info in pairs.items():
            if isinstance(info, dict) and "rate" in info:
                # Обрабатываем пары вида XXX_USD
                if pair.endswith("_USD"):
                    # Извлекаем валюту: "EUR_USD" → "EUR"
                    currency = pair.split("_")[0]
                    rates[currency] = float(info["rate"])
                # Особый случай: USD_USD
                elif pair == "USD_USD":
                    rates["USD"] = 1.0

        # Гарантируем наличие USD
        if "USD" not in rates:
            rates["USD"] = 1.0

        return rates
    '''

    def load_rates(self) -> Dict[str, float]:
        """
        Возвращает словарь: {"USD": 1.0, "EUR": 1.0786, "RUB": 75.9557, "BTC": 59337.21}
        Учитывает:
        - Для фиата: RUB_USD: 75.9557 → это означает 1 USD = 75.9557 RUB → значит, 
        курс RUB = 75.9557
        - Для крипты: BTC_USD: 59337.21 → 1 BTC = 59337.21 USD → значит, 
        курс BTC = 59337.21
        """
        print(f"📂 [load] Чтение из: {self.rates_file}")
        if not os.path.exists(self.rates_file):
            return {
                "USD": 1.0,
                "EUR": 1.07,
                "BTC": 60000.0,
                "ETH": 3000.0,
                "RUB": 95.0
            }
        
        try:
            with open(self.rates_file, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            print(f"❌ Ошибка чтения rates.json: {e}")
            return {"USD": 1.0}

        rates = {"USD": 1.0}       
        print("🔍 [load_rates] Весь JSON из файла:", data)
        pairs = data.get("pairs", {})

        for pair, info in pairs.items():
            if not isinstance(info, dict) or "rate" not in info:
                continue

            rate = float(info["rate"])

            # Разбираем пару
            if "_" not in pair:
                continue

            from_curr, to_curr = pair.split("_", 1)

            # Если пара заканчивается на _USD
            if to_curr == "USD":
                if from_curr in {"BTC", "ETH", "SOL", "ADA", "DOT", "BNB", "XRP", "AVAX", "LINK"}: # noqa: E501
                    # Криптовалюты: BTC_USD = 59337 → 1 BTC = 59337 USD
                    rates[from_curr] = rate
                else:
                    """ Фиат: RUB_USD = 75.9557 → это НА САМОМ ДЕЛЕ означает: 
                    1 USD = 75.9557 RUB
                    → значит, курс RUB (сколько RUB за 1 USD) = 75.9557 """
                    rates[from_curr] = rate  # Да, сохраняем как есть: RUB = 75.9557
            # Если пара USD_XXX — например, USD_EUR = 0.8407
            elif from_curr == "USD":
                # 1 USD = 0.8407 EUR → значит, 1 EUR = 1 / 0.8407 ≈ 1.189
                rates[to_curr] = 1 / rate

        # Гарантируем USD
        if "USD" not in rates:
            rates["USD"] = 1.0
        
        print("🔧 [load_rates] Все найденные пары:", list(pairs.keys()))
        print("📊 [load_rates] Итоговые курсы:", rates)
  
        return rates

    def save_rates_with_timestamp(self, rates: Dict[str, float]):
        data = {**rates, "last_updated": datetime.now().isoformat()}
        print(f"💾 [save] Запись в: {self.rates_file}")
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
            last_updated = datetime.fromisoformat(last_updated_str) if last_updated_str else now # noqa: E501

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