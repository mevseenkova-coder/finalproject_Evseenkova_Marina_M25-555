# valutatrade_hub/core/usecases.py

import json
import os
from datetime import datetime
from typing import Dict, Optional
from valutatrade_hub.core.models import User, Portfolio, Wallet

# бизнес-логика

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


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


def save_users(users: Dict[int, User]):
    data = [user.to_dict() for user in users.values()]
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

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
            p = Portfolio.from_dict(item)
            portfolios[p.user_id] = p
            print(f"✅ Загружен портфель user_id={p.user_id}")
        except Exception as e:
            print(f"⚠️ Пропущен портфель: {e}")
            continue

    print(f"📊 Всего загружено: {len(portfolios)}")
    return portfolios


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


def login(username: str, password: str) -> Optional[User]:
    users = load_users()
    for user in users.values():
        if user.username == username and user.verify_password(password):
            return user
    return None

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

def update_portfolio(portfolio: Portfolio):
    portfolios = load_portfolios()
    portfolios[portfolio.user_id] = portfolio
    save_portfolios(portfolios)


def get_exchange_rate(currency: str) -> Optional[float]:
    rates = load_rates()
    return rates.get(currency.upper())
