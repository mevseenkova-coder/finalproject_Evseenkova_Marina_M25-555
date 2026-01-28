
# core/usecases.py

import json
import os
from datetime import datetime
from typing import Optional, Dict

from models.user import User
from models.portfolio import Portfolio

DATA_DIR = "data"
USERS_FILE = os.path.join(DATA_DIR, "users.json")
PORTFOLIOS_FILE = os.path.join(DATA_DIR, "portfolios.json")
RATES_FILE = os.path.join(DATA_DIR, "rates.json")


def load_users() -> Dict[int, User]:
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    users = {}
    for item in data:
        user = User.from_json_record(item)
        users[user.user_id] = user
    return users


def save_users(users: Dict[int, User]):
    data = [user.to_dict() for user in users.values()]
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_portfolios() -> Dict[int, Portfolio]:
    if not os.path.exists(PORTFOLIOS_FILE):
        return {}
    with open(PORTFOLIOS_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    portfolios = {}
    for item in data:
        portfolio = Portfolio.from_dict(item)
        portfolios[portfolio.user_id] = portfolio
    return portfolios


def save_portfolios(portfolios: Dict[int, Portfolio]):
    data = [p.to_dict() for p in portfolios.values()]
    with open(PORTFOLIOS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


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


def get_portfolio(user_id: int) -> Portfolio:
    portfolios = load_portfolios()
    if user_id not in portfolios:
        portfolios[user_id] = Portfolio(user_id=user_id)
        # Добавим USD-кошелёк по умолчанию
        portfolios[user_id].add_currency("USD", 1000.0)  # Стартовый капитал
        save_portfolios(portfolios)
    return portfolios[user_id]


def update_portfolio(portfolio: Portfolio):
    portfolios = load_portfolios()
    portfolios[portfolio.user_id] = portfolio
    save_portfolios(portfolios)


def get_exchange_rate(currency: str) -> Optional[float]:
    rates = load_rates()
    return rates.get(currency.upper())

'''
Ниже примеры использования
'''

# Создание нового пользователя
user = User(
    user_id=1,
    username="alice",
    password="secret123",
    salt="x5T9!",
    registration_date=datetime.now()
)

# Проверка пароля
print(user.verify_password("secret123"))  # True
print(user.verify_password("wrong"))      # False

# Смена пароля
user.change_password("newpass456")
print("Пароль изменён:", user.verify_password("newpass456"))  # True

# Информация о пользователе
print(user.get_user_info())

# Сохранение в JSON
with open("users.json", "w", encoding="utf-8") as f:
    json.dump([user.to_dict()], f, indent=2, ensure_ascii=False)

# Загрузка из JSON
with open("users.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    loaded_user = User.from_json_record(data[0])

print("Загружен:", loaded_user.get_user_info())


# Создание кошельков
btc_wallet = Wallet("BTC", 0.05)
usd_wallet = Wallet("USD", 1200.0)

# Операции
btc_wallet.deposit(0.01)      # +0.01 BTC
btc_wallet.withdraw(0.02)     # -0.02 BTC

usd_wallet.deposit(300.0)
usd_wallet.withdraw(50.5)

# Информация
print(btc_wallet.get_balance_info())  # {'currency_code': 'BTC', 'balance': 0.04}
print(usd_wallet.get_balance_info())

# Сохранение в JSON (например, как часть портфеля)
portfolio = {
    btc_wallet.currency_code: btc_wallet.to_dict(),
    usd_wallet.currency_code: usd_wallet.to_dict()
}

with open("portfolio.json", "w", encoding="utf-8") as f:
    json.dump(portfolio, f, indent=2, ensure_ascii=False)

# Загрузка из JSON
with open("portfolio.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    loaded_btc = Wallet.from_dict(data["BTC"])
    loaded_usd = Wallet.from_dict(data["USD"])

print("Загружено из JSON:", loaded_btc.get_balance_info())


# Создаём портфель
portfolio = Portfolio(user_id=1)

# Добавляем валюты
portfolio.add_currency("USD", 1500.0)
portfolio.add_currency("BTC", 0.05)
portfolio.add_currency("EUR", 200.0)

# Покупка
portfolio.buy_currency("ETH", amount=2.0, price_in_usd=3000.0)  # Покупаем 2 ETH

# Продажа
portfolio.sell_currency("BTC", amount=0.01, price_in_usd=60000.0)  # Продаём часть BTC

# Общая стоимость
total_usd = portfolio.get_total_value()
print(f"Общая стоимость портфеля: ${total_usd:,.2f}")

# Информация по кошелькам
for code, wallet in portfolio.wallets.items():
    print(wallet.get_balance_info())

# Сохранение в JSON
with open("portfolios.json", "w", encoding="utf-8") as f:
    json.dump([portfolio.to_dict()], f, indent=2, ensure_ascii=False)

# Загрузка из JSON
with open("portfolios.json", "r", encoding="utf-8") as f:
    data = json.load(f)
    loaded_portfolio = Portfolio.from_dict(data[0])

print("Загружен портфель пользователя", loaded_portfolio.user_id)
