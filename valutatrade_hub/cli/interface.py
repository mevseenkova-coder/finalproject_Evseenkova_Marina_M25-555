# valutatrade_hub/cli/interface.py

import argparse
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Optional, Any
from valutatrade_hub.core.models import User, Portfolio
import sys
import secrets

# from valutatrade_hub.core.usecases import *
from valutatrade_hub.core.usecases import (
    buy as usecase_buy,
    sell as usecase_sell,
    get_exchange_rate as usecase_get_rate
)

from valutatrade_hub.core.exceptions import CurrencyNotFoundError, ApiRequestError
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.infra.database import DatabaseManager

# Константы
DATA_DIR = "data"
RATES_FILE = os.path.join(DATA_DIR, "rates.json")
CACHE_TTL_SECONDS = 300  # 5 минут

# команды

'''
from valutatrade_hub.core.usecases import (
    register_user, login, get_portfolio, update_portfolio,
    get_exchange_rate
)
'''

current_user: Optional['User'] = None

def print_help():
    print("""
Доступные команды:
  register <username> <password>    — зарегистрироваться
  login <username> <password>       — войти
  show-portfolio                    — показать портфель
  buy <currency> <amount>           — купить валюту
  sell <currency> <amount>          — продать валюту
  get-rate <currency>               — узнать курс
  exit                              — выйти
    """)


def validate_amount(amount_str: str) -> float:
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
        return amount
    except ValueError:
        raise ValueError("Сумма должна быть положительным числом.")


def require_login():
    global current_user
    if not current_user:
        print("Ошибка: войдите в систему, чтобы выполнить эту команду.")
        return False
    return True

"""
def cmd_register(args):
    if len(args) != 2:
        print("Использование: register <username> <password>")
        return
    username, password = args
    try:
        user = register_user(username, password)
        print(f"✅ Пользователь {username} успешно зарегистрирован (ID: {user.user_id})")
    except ValueError as e:
        print(f"Ошибка: {e}")
"""

def parse_args(args: list) -> dict:
    """Разбирает аргументы вида --key value"""
    result = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]  # убираем --
            if i + 1 >= len(args) or args[i + 1].startswith("--"):
                raise ValueError(f"У параметра '{key}' отсутствует значение.")
            result[key] = args[i + 1]
            i += 2
        else:
            raise ValueError(f"Некорректный аргумент: {args[i]}")
    return result


def cmd_register(args):
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: register --username <имя> --password <пароль>")
        return

    username = parsed.get("username")
    password = parsed.get("password")

    if not username:
        print("Ошибка: параметр --username обязателен.")
        return
    if not password:
        print("Ошибка: параметр --password обязателен.")
        return

    # Валидация длины пароля
    if len(password) < 4:
        print("Пароль должен быть не короче 4 символов")
        return

    # Загружаем пользователей
    users = load_users()

    # Проверка уникальности username
    for user in users.values():
        if user.username == username:
            print(f"Имя пользователя '{username}' уже занято")
            return

    # Генерация user_id
    user_id = max(users.keys(), default=0) + 1

    # Генерация соли
    salt = secrets.token_urlsafe(8)  # например, 'x5T9aBc'

    # Создаём пользователя
    user = User(
        user_id=user_id,
        username=username,
        password=password,
        salt=salt,
        registration_date=datetime.now()
    )

    # Сохраняем пользователя
    users[user_id] = user
    save_users(users)

    # Создаём пустой портфель
    portfolios = load_portfolios()
    portfolios[user_id] = Portfolio(user_id=user_id)
    save_portfolios(portfolios)

    global current_user
    current_user = user  # ✅ сохраняем объект User
    print(f"🔧 Регистрация успешна. Текущий пользователь: {current_user.username} (id={current_user.user_id})")

    # Успешный ответ
    print(f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login --username {username} --password ****")

'''
def cmd_login(args):
    global current_user
    if len(args) != 2:
        print("Использование: login <username> <password>")
        return
    username, password = args
    user = login(username, password)
    if user:
        current_user = user
        print(f"✅ Вы вошли как {username}")
    else:
        print("❌ Неверное имя пользователя или пароль")
'''

def cmd_login(args):
    global current_user

    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: login --username <имя> --password <пароль>")
        return

    username = parsed.get("username")
    password = parsed.get("password")

    if not username:
        print("Ошибка: параметр --username обязателен.")
        return
    if not password:
        print("Ошибка: параметр --password обязателен.")
        return

    # Загружаем пользователей
    users = load_users()

    # Поиск по username
    user = None
    for u in users.values():
        if u.username == username:
            user = u
            break

    if not user:
        print(f"Пользователь '{username}' не найден")
        return

    # Проверка пароля
    if not user.verify_password(password):
        print("Неверный пароль")
        return

    # Успех — фиксируем сессию
    current_user = user
    print(f"Вы вошли как '{username}'")

'''
def cmd_show_portfolio(args):
    if not require_login():
        return
    portfolio = get_portfolio(current_user.user_id)
    print(f"\n📊 Портфель пользователя {current_user.username} (ID: {current_user.user_id}):")
    for code, wallet in portfolio.wallets.items():
        print(f"  {code}: {wallet.balance}")
    total = portfolio.get_total_value()
    print(f"Общая стоимость (в USD): ${total:,.2f}")
'''

def cmd_show_portfolio(args):
    global current_user

    # Проверка, что пользователь залогинен
    if not current_user:
        print("Сначала выполните login")
        return

    # Парсим аргументы
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: show-portfolio [--base <валюта>]")
        return

    base_currency = parsed.get("base", "USD").strip().upper()

    # Проверка, что базовая валюта поддерживается
    supported_rates = load_rates()
    if base_currency not in supported_rates:
        print(f"Неизвестная базовая валюта '{base_currency}'")
        return

    # Загружаем портфель пользователя
    # portfolio = get_portfolio(current_user.user_id)
    portfolio = get_portfolio(current_user)  # ✅ объект User

    # Получаем кошельки
    wallets = portfolio.wallets

    if not wallets:
        print(f"Портфель пользователя '{current_user.username}' пуст.")
        return

    print(f"Портфель пользователя '{current_user.username}' (база: {base_currency}):")

    total_value = 0.0
    for code, wallet in wallets.items():
        # Получаем курс в USD
        rate_to_usd = supported_rates.get(code)
        if rate_to_usd is None:
            print(f"- {code}: {wallet.balance:,.6f}  → курс неизвестен, пропущено")
            continue

        # Конвертируем баланс в USD
        value_in_usd = wallet.balance * rate_to_usd

        # Если база не USD — конвертируем из USD в base
        base_rate = supported_rates[base_currency]
        value_in_base = value_in_usd / base_rate

        total_value += value_in_base

        # Форматируем вывод
        print(f"- {code}: {wallet.balance:,.6f}  → {value_in_base:,.2f} {base_currency}")

    print("-" * 40)
    print(f"ИТОГО: {total_value:,.2f} {base_currency}")

'''
def cmd_buy(args):
    if not require_login():
        return
    if len(args) != 2:
        print("Использование: buy <currency> <amount>")
        return
    currency, amount_str = args
    try:
        amount = validate_amount(amount_str)
        currency = currency.upper()
        rate = get_exchange_rate(currency)
        if not rate:
            print(f"❌ Нет данных о курсе для {currency}")
            return
        portfolio = get_portfolio(current_user.user_id)
        portfolio.buy_currency(currency, amount, rate)
        update_portfolio(portfolio)
    except Exception as e:
        print(f"Ошибка: {e}")
'''

'''
def cmd_buy(args):
    global current_user

    # Проверка логина
    if not current_user:
        print("Сначала выполните login")
        return

    # Парсим аргументы
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: buy --currency <валюта> --amount <число>")
        return

    currency = parsed.get("currency")
    amount_str = parsed.get("amount")

    # Валидация аргументов
    if not currency:
        print("Ошибка: параметр --currency обязателен.")
        return
    if not amount_str:
        print("Ошибка: параметр --amount обязателен.")
        return

    # Валидация currency
    currency = currency.strip().upper()
    if not currency.isalpha() or len(currency) < 2 or len(currency) > 5:
        print(f"'{currency}' — некорректный код валюты")
        return

    # Валидация amount
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    # Загружаем портфель
    # portfolio = get_portfolio(current_user.user_id)
    portfolio = get_portfolio(current_user)

    # Получаем курс в USD
    rates = load_rates()
    rate = rates.get(currency)
    if rate is None:
        print(f"Не удалось получить курс для {currency}→USD")
        return

    # Получаем текущий баланс до операции
    wallet = portfolio.get_wallet(currency)
    old_balance = wallet.balance if wallet else 0.0

    # Выполняем покупку (кошелёк создаётся автоматически при необходимости)
    try:
        portfolio.buy_currency(currency, amount, rate)
        update_portfolio(portfolio)  # Сохраняем изменения в JSON
        print(f"✅ Успешно куплено {amount} {currency} по курсу {rate} USD.")
    except ValueError as e:
        # Ожидаемые ошибки: не хватает средств, нет USD и т.п.
        print(f"❌ Ошибка при покупке: {e}")
        return
    except Exception as e:
        # Неожиданные ошибки (например, ошибка в логике или системе)
        print(f"🚨 Неожиданная ошибка: {type(e).__name__}: {e}")
        return

    # Формируем отчёт
    new_wallet = portfolio.get_wallet(currency)
    new_balance = new_wallet.balance

    total_cost_usd = amount * rate

    print(f"Покупка выполнена: {amount:,.4f} {currency} по курсу {rate:,.2f} USD/{currency}")
    print("Изменения в портфеле:")
    print(f"  {currency}: было {old_balance:,.4f} → стало {new_balance:,.4f}")
    print(f"Оценочная стоимость покупки: {total_cost_usd:,.2f} USD")
'''

def cmd_buy(args):
    global current_user

    if not current_user:
        print("Сначала выполните login")
        return

    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: buy --currency <валюта> --amount <число>")
        return

    currency = parsed.get("currency")
    amount_str = parsed.get("amount")

    if not currency:
        print("Ошибка: параметр --currency обязателен.")
        return
    if not amount_str:
        print("Ошибка: параметр --amount обязателен.")
        return

    currency = currency.strip().upper()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    # Получаем курс через usecase — он уже проверит валюту
    try:
        rate = usecase_get_rate(currency, "USD")
        usd_cost = amount * rate
        print(f"🔍 Курс {currency}/USD: {rate:.6f} → Стоимость: {usd_cost:.2f} USD")
        confirm = input(f"🛒 Подтвердите покупку {amount} {currency} за {usd_cost:.2f} USD? (y/n): ")
        if confirm.lower() != 'y':
            print("ℹ️ Покупка отменена.")
            return

        usecase_buy(current_user.user_id, currency, amount)
        print(f"✅ Успешно куплено: {amount} {currency}")

    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except InsufficientFundsError as e:
        print(f"❌ Недостаточно средств: доступно {e.available:.2f} USD, требуется {e.required:.2f} USD")
    except Exception as e:
        print(f"❌ Ошибка при покупке: {e}")

'''
def cmd_sell(args):
    if not require_login():
        return
    if len(args) != 2:
        print("Использование: sell <currency> <amount>")
        return
    currency, amount_str = args
    try:
        amount = validate_amount(amount_str)
        currency = currency.upper()
        rate = get_exchange_rate(currency)
        if not rate:
            print(f"❌ Нет данных о курсе для {currency}")
            return
        portfolio = get_portfolio(current_user.user_id)
        portfolio.sell_currency(currency, amount, rate)
        update_portfolio(portfolio)
    except Exception as e:
        print(f"Ошибка: {e}")
'''

'''
def cmd_sell(args):
    global current_user

    # Проверка логина
    if not current_user:
        print("Сначала выполните login")
        return

    # Парсим аргументы
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: sell --currency <валюта> --amount <число>")
        return

    currency = parsed.get("currency")
    amount_str = parsed.get("amount")

    # Валидация аргументов
    if not currency:
        print("Ошибка: параметр --currency обязателен.")
        return
    if not amount_str:
        print("Ошибка: параметр --amount обязателен.")
        return

    # Валидация currency
    currency = currency.strip().upper()
    if not currency.isalpha() or not (2 <= len(currency) <= 5):
        print(f"'{currency}' — некорректный код валюты")
        return

    # Валидация amount
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    # Загружаем портфель
    portfolio = get_portfolio(current_user.user_id)

    # Проверяем, существует ли кошелёк
    wallet = portfolio.get_wallet(currency)
    if not wallet:
        print(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.")
        return

    # Получаем курс
    try:
        rates = load_rates()
        rate = rates[currency]  # ← может вызвать KeyError
    except KeyError:
        print(f"Курс для {currency} недоступен. Повторите попытку позже.")
        return

    # Выполняем продажу — бизнес-логика в портфеле
    try:
        portfolio.sell_currency(currency, amount, rate)
        update_portfolio(portfolio)  # сохраняем изменения
    except InsufficientFundsError as e:
        print(e)  # ← единообразное сообщение: "Недостаточно средств: доступно ..."
        return
    except Exception as e:
        print(f"Неожиданная ошибка при продаже: {e}")
        return

    # Формируем отчёт
    new_balance = wallet.balance  # ← актуальное значение после withdraw
    revenue_usd = amount * rate

    print(f"Продажа выполнена: {amount:,.4f} {currency} по курсу {rate:,.2f} USD/{currency}")
    print("Изменения в портфеле:")
    print(f"  {currency}: было {new_balance + amount:,.4f} → стало {new_balance:,.4f}")
    print(f"Оценочная выручка: {revenue_usd:,.2f} USD")
'''

def cmd_sell(args):
    global current_user

    if not current_user:
        print("Сначала выполните login")
        return

    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: sell --currency <валюта> --amount <число>")
        return

    currency = parsed.get("currency")
    amount_str = parsed.get("amount")

    if not currency:
        print("Ошибка: параметр --currency обязателен.")
        return
    if not amount_str:
        print("Ошибка: параметр --amount обязателен.")
        return

    currency = currency.strip().upper()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    try:
        rate = usecase_get_rate(currency, "USD")
        revenue_usd = amount * rate
        print(f"🔍 Курс {currency}/USD: {rate:.6f} → Выручка: {revenue_usd:.2f} USD")
        confirm = input(f"💰 Подтвердите продажу {amount} {currency} за {revenue_usd:.2f} USD? (y/n): ")
        if confirm.lower() != 'y':
            print("ℹ️ Продажа отменена.")
            return

        revenue = usecase_sell(current_user.user_id, currency, amount)
        print(f"✅ Продано: {amount} {currency} → получено {revenue:.2f} USD")

    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except InsufficientFundsError as e:
        print(f"❌ Недостаточно {currency}: доступно {e.available:.6f}, требуется {e.required:.6f}")
    except Exception as e:
        print(f"❌ Ошибка при продаже: {e}")

'''
def cmd_sell(args):
    global current_user

    # Проверка логина
    if not current_user:
        print("Сначала выполните login")
        return

    # Парсим аргументы
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: sell --currency <валюта> --amount <число>")
        return

    currency = parsed.get("currency")
    amount_str = parsed.get("amount")

    # Валидация аргументов
    if not currency:
        print("Ошибка: параметр --currency обязателен.")
        return
    if not amount_str:
        print("Ошибка: параметр --amount обязателен.")
        return

    # Валидация currency
    currency = currency.strip().upper()
    if not currency.isalpha() or len(currency) < 2 or len(currency) > 5:
        print(f"'{currency}' — некорректный код валюты")
        return

    # Валидация amount
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("'amount' должен быть положительным числом")
        return

    # Загружаем портфель
    portfolio = get_portfolio(current_user.user_id)

    # Проверяем, существует ли кошелёк
    wallet = portfolio.get_wallet(currency)
    if not wallet:
        print(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся автоматически при первой покупке.")
        return

    # Проверяем баланс
    if wallet.balance < amount:
        print(f"Недостаточно средств: доступно {wallet.balance:,.4f} {currency}, требуется {amount:,.4f} {currency}")
        return

    # Получаем курс
    rates = load_rates()
    rate = rates.get(currency)
    if rate is None:
        print(f"Не удалось получить курс для {currency}→USD")
        return

    # Сохраняем старый баланс для отчёта
    old_balance = wallet.balance

    # Выполняем продажу
    try:
        portfolio.sell_currency(currency, amount, rate)
        update_portfolio(portfolio)
    except Exception as e:
        print(f"Ошибка при продаже: {e}")
        return

    # Формируем отчёт
    new_balance = wallet.balance - amount  # или portfolio.get_wallet(currency).balance
    revenue_usd = amount * rate

    print(f"Продажа выполнена: {amount:,.4f} {currency} по курсу {rate:,.2f} USD/{currency}")
    print("Изменения в портфеле:")
    print(f"  {currency}: было {old_balance:,.4f} → стало {new_balance:,.4f}")
    print(f"Оценочная выручка: {revenue_usd:,.2f} USD")
'''

'''
def cmd_get_rate(args):
    if len(args) != 1:
        print("Использование: get-rate <currency>")
        return
    currency = args[0].upper()
    rate = get_exchange_rate(currency)
    if rate:
        print(f"Курс {currency} = {rate} USD")
    else:
        print(f"❌ Курс для {currency} не найден.")
'''

'''
# Перенос в модуль database.py
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

def save_rates_with_timestamp(rates: dict):
    """Сохраняет курсы с отметкой времени"""
    data = rates.copy()
    data["last_updated"] = datetime.now().isoformat()
    with open(RATES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def fetch_rates_stub() -> dict:
    """
    Заглушка вместо Parser Service.
    В реальности здесь был бы HTTP-запрос к API.
    """
    return {
        "USD": 1.0,
        "EUR": 1.07,
        "GBP": 1.25,
        "JPY": 0.0067,
        "BTC": 59337.21,
        "ETH": 3010.50,
        "SOL": 145.70,
    }

# valutatrade_hub/cli/interface.py
from datetime import datetime, timedelta
from typing import Dict, Any

from valutatrade_hub.core.exceptions import CurrencyNotFoundError, ApiRequestError
from valutatrade_hub.core.currencies import get_currency
from valutatrade_hub.infra.settings import SettingsLoader
from valutatrade_hub.infra.database import DatabaseManager

'''
def cmd_get_rate(args):
    settings = SettingsLoader()
    db = DatabaseManager()

    try:
        # Парсим аргументы
        parsed = parse_args(args)
        from_curr = parsed.get("from")
        to_curr = parsed.get("to")

        if not from_curr:
            raise ValueError("Параметр --from обязателен.")
        if not to_curr:
            raise ValueError("Параметр --to обязателен.")

        from_curr = from_curr.strip().upper()
        to_curr = to_curr.strip().upper()

        # Валидация через реестр валют → выбросит CurrencyNotFoundError при ошибке
        get_currency(from_curr)
        get_currency(to_curr)

        # Загружаем курсы и время последнего обновления
        rates, last_updated = db.load_rates_with_timestamp()
        now = datetime.now()

        # Проверяем TTL из конфига
        ttl = settings.get("rates_ttl_seconds", 300)
        if now - last_updated > timedelta(seconds=ttl):
            print("🔄 Курсы устарели — обновляем из источника...")
            try:
                fresh_rates = fetch_rates_stub()  # ← здесь будет Parser Service
                db.save_rates_with_timestamp(fresh_rates)
                rates = fresh_rates
                last_updated = now
                print("✅ Курсы успешно обновлены.")
            except Exception as e:
                raise ApiRequestError(f"Не удалось обновить курсы: {str(e)}")

        # Проверяем наличие курсов
        if from_curr not in rates:
            raise CurrencyNotFoundError(from_curr)
        if to_curr not in rates:
            raise CurrencyNotFoundError(to_curr)

        # Расчёт курса через USD
        rate_from_usd = rates[from_curr]
        rate_to_usd = rates[to_curr]
        forward_rate = rate_from_usd / rate_to_usd
        reverse_rate = 1 / forward_rate

        updated_str = last_updated.strftime("%Y-%m-%d %H:%M:%S")

        # Вывод
        print(f"Курс {from_curr}→{to_curr}: {forward_rate:.8f} (обновлено: {updated_str})")
        print(f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.8f}")

    except ValueError as e:
        print(e)
        print("Использование: get-rate --from <валюта> --to <валюта>")
        return

    except CurrencyNotFoundError as e:
        print(e)
        print("Поддерживаемые валюты: USD, EUR, BTC, ETH, RUB, GBP, BTS")
        return

    except ApiRequestError as e:
        print(e)
        print("Используем кешированные курсы. Повторите запрос позже.")
        return

    except Exception as e:
        print(f"Неожиданная ошибка: {e}")
        return
'''

'''
def cmd_get_rate(args):
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: get-rate --from <валюта> --to <валюта>")
        return

    from_curr = parsed.get("from")
    to_curr = parsed.get("to")

    if not from_curr:
        print("Ошибка: параметр --from обязателен.")
        return
    if not to_curr:
        print("Ошибка: параметр --to обязателен.")
        return

    from_curr = from_curr.strip().upper()
    to_curr = to_curr.strip().upper()

    # Валидация кодов валют
    if not (from_curr.isalpha() and len(from_curr) in range(2, 6)):
        print(f"'{from_curr}' — некорректный код валюты")
        return
    if not (to_curr.isalpha() and len(to_curr) in range(2, 6)):
        print(f"'{to_curr}' — некорректный код валюты")
        return

    # Загружаем курсы и время обновления
    rates, last_updated = load_rates_with_timestamp()
    now = datetime.now()

    # Проверяем, нужно ли обновлять курсы
    if now - last_updated > timedelta(seconds=CACHE_TTL_SECONDS):
        print("🔄 Курсы устарели — обновляем из источника...")
        try:
            fresh_rates = fetch_rates_stub()  # Здесь будет Parser Service
            save_rates_with_timestamp(fresh_rates)
            rates = fresh_rates
            last_updated = now
            print("✅ Курсы успешно обновлены.")
        except Exception as e:
            print("⚠️  Не удалось обновить курсы, используем кеш.")
            # Оставляем старые курсы

    # Проверяем наличие валют в кеше
    if from_curr not in rates:
        print(f"Курс {from_curr}→{to_curr} недоступен. Повторите попытку позже.")
        return
    if to_curr not in rates:
        print(f"Курс {from_curr}→{to_curr} недоступен. Повторите попытку позже.")
        return

    # Рассчитываем прямой курс: from → to
    # Например: USD → BTC = 1 / (BTC → USD) * (USD → USD)
    rate_from_usd = rates[from_curr]  # сколько USD стоит 1 единица from_curr
    rate_to_usd = rates[to_curr]      # сколько USD стоит 1 единица to_curr

    # Курс: 1 единица from_curr = ? единиц to_curr
    forward_rate = rate_from_usd / rate_to_usd

    # Обратный курс: 1 to_curr = ? from_curr
    reverse_rate = 1 / forward_rate

    # Форматируем время
    updated_str = last_updated.strftime("%Y-%m-%d %H:%M:%S")

    # Вывод
    print(f"Курс {from_curr}→{to_curr}: {forward_rate:.8f} (обновлено: {updated_str})")
    print(f"Обратный курс {to_curr}→{from_curr}: {reverse_rate:.2f}")
'''

def cmd_get_rate(args):
    try:
        parsed = parse_args(args)
        from_curr = parsed.get("from")
        to_curr = parsed.get("to")

        if not from_curr:
            raise ValueError("Параметр --from обязателен.")
        if not to_curr:
            raise ValueError("Параметр --to обязателен.")

        from_curr = from_curr.strip().upper()
        to_curr = to_curr.strip().upper()

        # ← Вся валидация и TTL — внутри usecase
        rate = usecase_get_rate(from_curr, to_curr)

        print(f"💱 {from_curr}/{to_curr} = {rate:.8f}")
        print(f"🔄 1 {from_curr} = {rate:.8f} {to_curr}")

    except ValueError as e:
        print(e)
        print("Использование: get-rate --from <валюта> --to <валюта>")
    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except ApiRequestError as e:
        print(f"🌐 Ошибка API: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

def main():
    # CLI-интерфейс
    print("Добро пожаловать в ValutaTrade Hub!")
    print_help()

    global current_user
    while True:
        try:
            command = input("\n> ").strip()
            if not command:
                continue

            parts = command.split()
            cmd, *args = parts

            if cmd == "exit":
                print("👋 До свидания!")
                break
            elif cmd == "help":
                print_help()
            elif cmd == "register":
                cmd_register(args)
            elif cmd == "login":
                cmd_login(args)
            elif cmd == "show-portfolio":
                cmd_show_portfolio(args)
            elif cmd == "buy":
                cmd_buy(args)
            elif cmd == "sell":
                cmd_sell(args)
            elif cmd == "get-rate":
                cmd_get_rate(args)
            else:
                print("Неизвестная команда. Введите 'help' для справки.")
        except KeyboardInterrupt:
            print("\n👋 Программа завершена.")
            break
        except Exception as e:
            print(f"Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()
