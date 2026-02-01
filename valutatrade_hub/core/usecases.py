# valutatrade_hub/core/usecases.py

import json
import os
from datetime import datetime, timezone, timedelta
from typing import Dict, Optional, List, Any
from valutatrade_hub.core.models import User, Portfolio, Wallet
from valutatrade_hub.decorators import log_action
from valutatrade_hub.core.exceptions import InsufficientFundsError, CurrencyNotFoundError, UserAlreadyExistsError
from valutatrade_hub.infra.database import DatabaseManager
from valutatrade_hub.infra.settings import SettingsLoader
from hashlib import pbkdf2_hmac

# бизнес-логика
# ДОПОЛНИТЬ: buy/sell/get-rate с исключениями и логированием

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")

'''
def load_users() -> Dict[int, User]:
    if not os.path.exists(USERS_FILE):
        return {}

    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения {USERS_FILE}: {e}")
        print("Файл повреждён. Создаём новый список пользователей.")
        return {}

    users = {}
    for item in data:
        try:
            user = User.from_json_record(item)
            users[user.user_id] = user
        except Exception as e:
            print(f"⚠️ Пропущен пользователь из-за ошибки: {e}")
            continue

    return users
'''
'''
def save_users(users: Dict[int, User]):
    data = [user.to_dict() for user in users.values()]
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
'''
'''
def load_portfolios() -> Dict[int, Portfolio]:
    if not os.path.exists(PORTFOLIOS_FILE):
        return {}

    try:
        with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"❌ Ошибка чтения {PORTFOLIOS_FILE}: {e}")
        print("Файл портфелей повреждён. Создаём пустые портфели.")
        return {}

    portfolios = {}
    for item in data:
        try:
            portfolio = Portfolio.from_dict(item)
            portfolios[portfolio.user_id] = portfolio
        except Exception as e:
            print(f"⚠️ Пропущен портфель: {e}")
            continue

    return portfolios
'''

'''
def load_portfolios() -> Dict[int, Portfolio]:
    abs_path = os.path.abspath(PORTFOLIOS_FILE)
    print(f"\n📂 ЗАГРУЗКА ПОРТФЕЛЕЙ: {abs_path}")

    if not os.path.exists(PORTFOLIOS_FILE):
        print("❌ Файл НЕ найден — возвращаем пустой портфель")
        return {}

    print("✅ Файл найден — читаем...")

    with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as f:
        content = f.read().strip()
        print(f"📄 СОДЕРЖИМОЕ ФАЙЛА:\n{content}")

    if not content:
        print("⚠️  Файл пуст")
        return {}

    try:
        with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"✅ JSON распаршен — {len(data)} записей")
    except json.JSONDecodeError as e:
        print(f"❌ ОШИБКА JSON: {e}")
        print("🚨 Скорее всего, файл записан через str(), а не json.dump()")
        return {}

    portfolios = {}
    for item in data:
        try:
            portfolio = Portfolio.from_dict(item)
            portfolios[portfolio.user_id] = portfolio
            print(f"✅ Загружен портфель user_id={portfolio.user_id}")
        except Exception as e:
            print(f"⚠️ Не удалось восстановить портфель: {e}")
            continue

    print(f"📊 Всего загружено портфелей: {len(portfolios)}")
    return portfolios
'''
'''
def save_portfolios(portfolios: Dict[int, Portfolio]):
    data = [p.to_dict() for p in portfolios.values()]
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
'''

'''
def save_portfolios(portfolios: Dict[int, Portfolio]):
    data = [p.to_dict() for p in portfolios.values()]
    print(f"\n💾 СОХРАНЕНИЕ ПОРТФЕЛЕЙ — ВСЕГО: {len(data)}")
    print(f"📄 Формат данных: {type(data)}")
    if data:
        print(f"📄 Пример записи: {data[0]}")
    print(f"📍 Путь: {os.path.abspath(PORTFOLIOS_FILE)}")

    try:
        with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✅ УСПЕШНО СОХРАНЕНО В ФОРМАТЕ JSON")
    except Exception as e:
        print(f"❌ ОШИБКА СОХРАНЕНИЯ: {e}")
        raise
'''
'''
def save_portfolios(portfolios: Dict[int, Portfolio]):
    data = [p.to_dict() for p in portfolios.values()]

    # 🔍 Проверка: можно ли сериализовать?
    try:
        json.dumps(data, ensure_ascii=False, indent=2)
        print("🟢 JSON: OK")
    except TypeError as e:
        print(f"🔴 Ошибка сериализации: {e}")
        import pprint
        pprint.pprint(data)
        return  # ❌ Не сохраняем

    try:
        with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("✅ Успешно сохранено")
    except Exception as e:
        print(f"❌ Ошибка записи: {e}")
        raise
'''
'''
def load_rates() -> Dict[str, float]:
    if not os.path.exists(RATES_FILE):
        # Возвращаем дефолтные курсы
        return {
            "USD": 1.0, "EUR": 1.07, "GBP": 1.25,
            "JPY": 0.0067, "BTC": 60000.0, "ETH": 3000.0
        }
    with open(RATES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    return {k: v for k, v in data.items() if k != "last_updated"}
'''

'''
def load_rates() -> Dict[str, float]:
    if not os.path.exists(RATES_FILE):
        print(f"🔧 [LOAD_RATES] Файл {RATES_FILE} не найден — создаём дефолтные курсы")
        return {
            "USD": 1.0, "EUR": 1.07, "GBP": 1.25,
            "JPY": 0.0067, "BTC": 60000.0, "ETH": 3000.0
        }

    print(f"🔧 [LOAD_RATES] Читаем файл: {RATES_FILE}")
    with open(RATES_FILE, "r", encoding="utf-8") as f:
        content = f.read()
        print(f"📄 [DEBUG] Содержимое файла:\n{content}")

        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            print(f"❌ [ERROR] Ошибка парсинга JSON: {e}")
            raise

    return {k: v for k, v in data.items() if k != "last_updated"}
'''
'''
def load_rates() -> Dict[str, float]:
    if not os.path.exists(RATES_FILE):
        # Возвращаем дефолтные курсы в нужном формате
        return {
            "USD": 1.0,
            "EUR": 1.07,
            "BTC": 60000.0,
            "RUB": 95.0,
            "ETH": 3000.0
        }

    with open(RATES_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # Преобразуем формат ParserService: "EUR_USD" → "EUR": 1.0786
    rates = {}

    for pair, info in data.items():
        if isinstance(info, dict) and "rate" in info:
            if pair.endswith("_USD"):
                # Извлекаем код валюты: "EUR_USD" → "EUR"
                currency = pair.split("_")[0]
                rates[currency] = float(info["rate"])
            elif pair == "RUB_USD":
                rates["RUB"] = float(info["rate"])

    # Добавляем USD
    rates["USD"] = 1.0

    return rates
'''
'''
def register_user(username: str, password: str) -> User:
    users = load_users()
    user_id = max(users.keys(), default=0) + 1
    user = User(
        user_id=user_id,
        username=username,
        password=password,
        salt=f"salt{user_id}",
        registration_date=datetime.now()
    )
    users[user_id] = user
    save_users(users)
    return user
'''

@log_action("REGISTER", verbose=False)
def register_user(username: str, password: str) -> User:
    """
    Регистрация нового пользователя с хэшированием пароля.
    :param username: Имя пользователя
    :param password: Пароль (будет захэширован)
    :return: Объект User
    """
    db = DatabaseManager()
    users: List[User] = db.load_users()

    # Проверка: пользователь уже существует?
    if any(u.username == username for u in users):
        raise UserAlreadyExistsError(username)

    if len(password) < 4:
        raise ValueError("Пароль должен быть не короче 4 символов.")
    username = username.strip()
    
    # Генерация соли
    salt = os.urandom(32)  # 32 байта — криптостойко

    # Хэширование пароля: PBKDF2 с 100_000 итераций
    pwd_hash = pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100_000)

    # Генерация ID
    user_id = max((u.user_id for u in users), default=0) + 1

    # Создаём пользователя
    # В models.User пароль хранится как hashed_password, соль — отдельно
    new_user = User(
        user_id=user_id,
        username=username,
        hashed_password=pwd_hash.hex(),  # сохраняем как hex-строку
        salt=salt.hex(),                # соль тоже в hex
        registration_date=datetime.now()
    )

    # Сохраняем
    db.save_user(new_user)
    return new_user
    
'''
def login(username: str, password: str) -> Optional[User]:
    users = load_users()
    for user in users.values():
        if user.username == username and user.verify_password(password):
            return user
    return None
'''

@log_action("LOGIN", verbose=False)
def login(username: str, password: str) -> User:
    db = DatabaseManager()
    users = db.load_users()

    for user in users:
        if user.username == username:
            if user.verify_password(password):
                return user
            else:
                raise AuthenticationError("Неверный пароль")
    raise AuthenticationError("Пользователь не найден")

'''
def get_portfolio(user_id: int) -> Portfolio:
    portfolios = load_portfolios()
    if user_id not in portfolios:
        portfolios[user_id] = Portfolio(user_id=user_id)
        # Добавим USD-кошелёк по умолчанию
        portfolios[user_id].add_currency("USD", 1000.0)  # Стартовый капитал
        save_portfolios(portfolios)
    return portfolios[user_id]
'''

'''
def get_portfolio(user: User) -> Portfolio:
    print(f"\n🔍 get_portfolio: ищем портфель для user_id={user.user_id}, username={user.username}")
    
    portfolios = load_portfolios()
    print(f"📊 Загружено портфелей: {len(portfolios)}")

    if user.user_id not in portfolios:
        print(f"🆕 Создаём новый портфель для {user.user_id}")
        portfolio = Portfolio(user_id=user.user_id)
        portfolio.add_currency("USD", 1000.0)
        portfolios[user.user_id] = portfolio
        save_portfolios(portfolios)
        print("✅ Новый портфель сохранён")
    else:
        print(f"✅ Портфель найден")

    result = portfolios[user.user_id]
    print(f"💼 Возвращаем портфель: user_id={result.user_id}, wallets={list(result._wallets.keys())}")
    return result
'''

'''
def get_portfolio(user: User) -> Portfolio:
    print(f"\n🔍 get_portfolio: user = {user}, type = {type(user)}")
    
    if not isinstance(user, User):
        raise TypeError(f"❌ Ожидался объект User, но получен {type(user)}: {user}")

    print(f"🔍 Ищем портфель для user_id={user.user_id}, username={user.username}")
    portfolios = load_portfolios()
    print(f"📊 Загружено портфелей: {len(portfolios)}")

    if user.user_id not in portfolios:
        print(f"🆕 Создаём новый портфель для {user.user_id}")
        portfolio = Portfolio(user_id=user.user_id)
        portfolio.add_currency("USD", 1000.0)
        portfolios[user.user_id] = portfolio
        save_portfolios(portfolios)
        print("✅ Новый портфель сохранён")
    else:
        print(f"✅ Портфель найден")

    result = portfolios[user.user_id]
    print(f"💼 Возвращаем портфель: user_id={result.user_id}, wallets={list(result._wallets.keys())}")
    return result
'''
'''
def get_portfolio(user: User) -> Portfolio:
    """Получить портфель пользователя. Создаёт пустой с 1000 USD, если его нет."""
    if not isinstance(user, User):
        raise TypeError(f"Ожидался User, получен {type(user)}")

    db = DatabaseManager()
    portfolio = db.load_portfolio(user.user_id)

    # Если портфель только что создан — добавим стартовый капитал
    if len(portfolio._wallets) == 0:
        # usd_wallet = Wallet(currency_code="USD", initial_balance=1000.0)
        # portfolio.add_wallet(usd_wallet)
        portfolio.add_currency("USD", initial_balance=1000.0)
        db.save_portfolio(portfolio)

    return portfolio
'''

def get_portfolio(user: User) -> Portfolio:
    """Получить портфель пользователя. Не добавляет стартовый капитал."""
    if not isinstance(user, User):
        raise TypeError(f"Ожидался User, получен {type(user)}")

    db = DatabaseManager()
    portfolio = db.load_portfolio(user.user_id)

    return portfolio

'''
def update_portfolio(portfolio: Portfolio):
    portfolios = load_portfolios()
    portfolios[portfolio.user_id] = portfolio
    save_portfolios(portfolios)
'''
'''
def get_exchange_rate(currency: str) -> Optional[float]:
    rates = load_rates()
    return rates.get(currency.upper())
'''

'''
def get_exchange_rate(from_code: str, to_code: str) -> float:
    settings = SettingsLoader()
    db = DatabaseManager()

    # Используем TTL из конфига
    ttl = settings.get("rates_ttl_seconds", 300)
    rates = db.load_rates(ttl=ttl)  # ← например

    if from_code not in rates:
        raise CurrencyNotFoundError(from_code)
    if to_code not in rates:
        raise CurrencyNotFoundError(to_code)

    return rates[from_code] / rates[to_code]
'''

'''
def get_exchange_rate(from_code: str, to_code: str) -> float:
    """
    Получить курс обмена: 1 единица from_code = ? единиц to_code.
    Расчёт идёт через USD (например: BTC → EUR = BTC→USD / EUR→USD).
    """
    settings = SettingsLoader()
    db = DatabaseManager()

    # Загружаем курсы (с логикой TTL внутри database.py)
    rates = db.load_rates()

    from_code = from_code.strip().upper()
    to_code = to_code.strip().upper()

    # Валидация: валюта поддерживается?
    if from_code not in rates:
        raise CurrencyNotFoundError(from_code)
    if to_code not in rates:
        raise CurrencyNotFoundError(to_code)

    # Расчёт через USD
    rate_from_usd = rates[from_code]  # сколько USD стоит 1 from_code
    rate_to_usd = rates[to_code]      # сколько USD стоит 1 to_code

    # Курс: 1 from_code = ? to_code
    exchange_rate = rate_from_usd / rate_to_usd

    return exchange_rate
'''
'''
def get_exchange_rate(from_currency: str, to_currency: str) -> Optional[float]:
    settings = SettingsLoader.load()
    ttl = settings.get("exchange_rate_cache_ttl", 300)  # секунды

    file_path = os.path.join("data", "rates.json")
    if not os.path.exists(file_path):
        return None

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        pair_key = f"{from_currency}_{to_currency}"
        pair_data = data.get("pairs", {}).get(pair_key)
        if not pair_data:
            return None

        updated_at = datetime.fromisoformat(pair_data["updated_at"].replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        if now - updated_at > timedelta(seconds=ttl):
            return None  # устарело

        return float(pair_data["rate"])
    except Exception:
        return None
'''
'''
def get_exchange_rate(from_code: str, to_code: str) -> float:
    print(f"🔍 get_exchange_rate: ищем курс {from_code} → {to_code}")
    db = DatabaseManager()
    rates = db.load_rates()
    print(f"📊 Доступные курсы: {list(rates.keys())}")
    print("🔍 DEBUG: Доступные курсы в rates:", rates)
    print(f"🔍 DEBUG: Ищем валюты: {from_code} и {to_code}")
    from_code = from_code.strip().upper()
    to_code = to_code.strip().upper()

    if from_code not in rates:
        raise CurrencyNotFoundError(from_code)
    if to_code not in rates:
        raise CurrencyNotFoundError(to_code)
    print(f"✅ Вернули курс: {rate}")
    return rates[from_code] / rates[to_code]
'''

def get_exchange_rate(from_code: str, to_code: str) -> float:
    print(f"🔍 get_exchange_rate: ищем курс {from_code} → {to_code}")
    db = DatabaseManager()
    rates = db.load_rates()
    print(f"📊 Доступные курсы: {list(rates.keys())}")
    print("🔍 DEBUG: Доступные курсы в rates:", rates)
    print(f"🔍 DEBUG: Ищем валюты: {from_code} и {to_code}")

    from_code = from_code.strip().upper()
    to_code = to_code.strip().upper()

    if from_code not in rates:
        raise CurrencyNotFoundError(from_code)
    if to_code not in rates:
        raise CurrencyNotFoundError(to_code)

    # Сначала вычисляем курс
    rate = rates[from_code] / rates[to_code]
    
    # Потом уже выводим
    print(f"✅ Вернули курс: {rate}")

    return rate

'''
def get_exchange_rate(from_curr: str, to_curr: str) -> float:
    if from_curr == to_curr:
        return 1.0

    # Прямой курс
    direct = pairs.get(f"{from_curr}_{to_curr}")
    if direct:
        return direct["rate"]

    # Обратный: есть to_curr → from_curr?
    reverse = pairs.get(f"{to_curr}_{from_curr}")
    if reverse:
        return 1 / reverse["rate"]

    # Через USD
    via_from_usd = pairs.get(f"{from_curr}_USD") or (1 / pairs[f"USD_{from_curr}"]["rate"] if f"USD_{from_curr}" in pairs else None)
    via_to_usd = pairs.get(f"USD_{to_curr}")

    if via_from_usd and via_to_usd:
        return via_from_usd["rate"] * via_to_usd["rate"]

    raise ValueError(f"Курс {from_curr}→{to_curr} не найден")
'''
'''
def get_exchange_rate(from_curr: str, to_curr: str) -> float:
    """
    Получить курс обмена: 1 from_curr = ? to_curr
    Использует данные из базы (rates.json) с поддержкой прямых, обратных и кросс-курсов.
    """
    if from_curr == to_curr:
        return 1.0

    # Загружаем курсы через DatabaseManager
    db = DatabaseManager()
    rates = db.load_rates()
    # snapshot = db.load_rates_snapshot()  # ← возвращает весь JSON, включая pairs
    # rates = snapshot.get("pairs", {})

    # Прямой курс: EUR_RUB
    pair_key = f"{from_curr}_{to_curr}"
    if pair_key in rates:
        return float(rates[pair_key]["rate"])

    # Обратный курс: RUB_EUR → 1 / rate
    reverse_key = f"{to_curr}_{from_curr}"
    if reverse_key in rates:
        return 1 / float(rates[reverse_key]["rate"])

    # Кросс-курс через USD
    try:
        # from_curr → USD
        if f"{from_curr}_USD" in rates:
            rate1 = float(rates[f"{from_curr}_USD"]["rate"])
        else:
            # Попробуем USD → from_curr и обратим
            rate1 = 1 / float(rates[f"USD_{from_curr}"]["rate"])

        # USD → to_curr
        if f"USD_{to_curr}" in rates:
            rate2 = float(rates[f"USD_{to_curr}"]["rate"])
        else:
            rate2 = 1 / float(rates[f"{to_curr}_USD"]["rate"])

        return rate1 * rate2
    except KeyError:
        raise CurrencyNotFoundError(f"Курс {from_curr}→{to_curr} не найден в базе")
'''
'''
@log_action("BUY", verbose=True)
def buy_currency(portfolio, currency_code: str, amount: float, rate: float) -> None:
    usd_cost = amount * rate
    usd_wallet = portfolio.get_wallet('USD')
    if not usd_wallet or usd_wallet.balance < usd_cost:
        raise InsufficientFundsError(available=usd_wallet.balance if usd_wallet else 0, required=usd_cost, code='USD')

    portfolio.add_currency(currency_code, amount)
    usd_wallet.withdraw(usd_cost)
'''

@log_action("BUY", verbose=True)
def buy(user_id: int, currency_code: str, amount: float) -> None:
    """Покупка валюты."""
    if amount <= 0:
        raise ValueError("Количество должно быть больше 0.")

    db = DatabaseManager()
    portfolio = db.load_portfolio(user_id)

    rates = db.load_rates()
    if currency_code not in rates:
        raise CurrencyNotFoundError(currency_code)

    rate = rates[currency_code]  # курс к USD
    usd_cost = amount * rate

    usd_wallet = portfolio.get_wallet("USD")
    if not usd_wallet or usd_wallet.balance < usd_cost:
        raise InsufficientFundsError(
            available=usd_wallet.balance if usd_wallet else 0,
            required=usd_cost,
            code="USD"
        )

    # Пополняем валюту (кошелёк создаётся автоматически)
    '''
    target_wallet = portfolio.get_wallet(currency_code)
    if not target_wallet:
        target_wallet = Wallet(currency_code, 0.0)
        portfolio.add_wallet(target_wallet)
    target_wallet.deposit(amount)
    '''
    if currency_code not in portfolio.wallets:
        portfolio.add_currency(currency_code, 0.0)
    portfolio.get_wallet(currency_code).deposit(amount)
    
    # Снимаем USD
    usd_wallet.withdraw(usd_cost)

    db.save_portfolio(portfolio)

'''
@log_action("SELL", verbose=True)
def sell_currency(portfolio, currency_code: str, amount: float, rate: float) -> None:
    wallet = portfolio.get_wallet(currency_code)
    if not wallet:
        raise ValueError(f"Нет кошелька для {currency_code}")
    wallet.withdraw(amount)

    usd_wallet = portfolio.get_wallet('USD')
    if not usd_wallet:
        portfolio.add_currency('USD', 0.0)
        usd_wallet = portfolio.get_wallet('USD')

    revenue = amount * rate
    usd_wallet.deposit(revenue)
'''

@log_action("SELL", verbose=True)
def sell(user_id: int, currency_code: str, amount: float) -> float:
    """Продажа валюты. Возвращает выручку в USD."""
    if amount <= 0:
        raise ValueError("Количество должно быть больше 0.")

    db = DatabaseManager()
    portfolio = db.load_portfolio(user_id)

    wallet = portfolio.get_wallet(currency_code)
    if not wallet or wallet.balance < amount:
        raise InsufficientFundsError(
            available=wallet.balance if wallet else 0,
            required=amount,
            code=currency_code
        )

    rates = db.load_rates()
    if currency_code not in rates:
        raise CurrencyNotFoundError(currency_code)

    rate = rates[currency_code]
    revenue_usd = amount * rate

    # Снимаем валюту
    wallet.withdraw(amount)

    # Пополняем USD
    '''
    usd_wallet = portfolio.get_wallet("USD")
    if not usd_wallet:
        usd_wallet = Wallet("USD", 0.0)
        portfolio.add_wallet(usd_wallet)
    usd_wallet.deposit(revenue_usd)
    '''
    if "USD" not in portfolio.wallets:
        portfolio.add_currency("USD", initial_balance=0.0)
    portfolio.get_wallet("USD").deposit(revenue_usd)

    db.save_portfolio(portfolio)
    return revenue_usd
