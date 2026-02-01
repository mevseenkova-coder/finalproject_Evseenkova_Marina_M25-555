# valutatrade_hub/cli/interface.py

import argparse
import json
import os
import secrets
import threading
from datetime import datetime
from typing import Optional

from valutatrade_hub.core.models import Portfolio, User

# from valutatrade_hub.core.usecases import *
from valutatrade_hub.core.usecases import buy as usecase_buy
from valutatrade_hub.core.usecases import get_exchange_rate as usecase_get_rate
from valutatrade_hub.core.usecases import get_portfolio
from valutatrade_hub.core.usecases import sell as usecase_sell

'''
from valutatrade_hub.core.usecases import (
    register_user, login, get_portfolio, update_portfolio,
    get_exchange_rate
)
'''
from valutatrade_hub.core.exceptions import ApiRequestError, CurrencyNotFoundError
from valutatrade_hub.infra.database import DatabaseManager

# Попробуем импортировать компоненты парсера (если доступны)
try:
    import threading

    from valutatrade_hub.parser_service.api_clients import (
        CoinGeckoClient,
        ExchangeRateApiClient,
    )
    from valutatrade_hub.parser_service.config import config
    from valutatrade_hub.parser_service.scheduler import start_scheduler
    from valutatrade_hub.parser_service.updater import (  # noqa: E501
        RatesUpdater,
        update_rates,
    )
    PARSER_AVAILABLE = bool(config.EXCHANGERATE_API_KEY)
    # PARSER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Не удалось загрузить Parser Service: {e}")
    PARSER_AVAILABLE = False
    # Резервный путь — если parser_service не загружен
    DATA_DIR = os.path.join("data")
    RATES_FILE_PATH = os.path.join(DATA_DIR, "rates.json")
    # Перенесено из Константы
    RATES_FILE = os.path.join(DATA_DIR, "rates.json")
    CACHE_TTL_SECONDS = 300  # 5 минут

'''
# Проверка наличия parser_service
PARSER_AVAILABLE = os.path.exists("parser_service")

# Если parser_service есть — подключаем
if PARSER_AVAILABLE:
    try:
        from parser_service.updater import RatesUpdater
        from parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
    except Exception as e:
        print(f"⚠️  Не удалось загрузить parser_service: {e}")
        PARSER_AVAILABLE = False
'''
'''
# Константы
DATA_DIR = "data"
RATES_FILE = os.path.join(DATA_DIR, "rates.json")
CACHE_TTL_SECONDS = 300  # 5 минут
'''
# команды

current_user: Optional['User'] = None
db = DatabaseManager()
'''
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
'''

def print_help():
    print("""
Доступные команды:
  register --username <имя> --password <пароль>  — зарегистрироваться
  login --username <имя> --password <пароль>     — войти
  show-portfolio [--base <валюта>]               — показать портфель
  buy --currency <валюта> --amount <число>       — купить валюту
  sell --currency <валюта> --amount <число>      — продать валюту
  get-rate --from <валюта> --to <валюта>         — узнать курс
  update-rates                                   — обновить курсы вручную
  start-scheduler                                — запустить автообновление
  exit                                           — выйти
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
        print(f"✅ Пользователь {username} успешно зарегистрирован(ID: {user.user_id})")
    except ValueError as e:
        print(f"Ошибка: {e}")
"""

'''
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
'''

def parse_args(args: list) -> dict:
    """
    Разбирает аргументы командной строки.
    Поддерживает:
        --key value     → result['key'] = 'value'
        --flag          → result['flag'] = True
        --flag true     → result['flag'] = 'true' (но можно обработать как bool)
    """
    result = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]  # убираем --
            # Проверяем, есть ли следующий аргумент и НЕ является ли он флагом
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                result[key] = args[i + 1]
                i += 2
            else:
                # Нет значения → считаем, что это флаг (включён)
                result[key] = True
                i += 1
        else:
            raise ValueError(f"Некорректный аргумент: {args[i]}")
    return result
"""
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
    # users = load_users()
    users = db.load_users_dict()

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
    user = User.create_user(
        user_id=user_id,
        username=username,
        password=password, # ← передаём "сырой" пароль — внутри он захэшируется
        salt=salt,
        registration_date=datetime.now()
    )
    
    # Сохраняем пользователя
    users[user_id] = user
    # save_users(users)
    db.save_user(user)

    '''
    # Создаём пустой портфель
    portfolios = load_portfolios()
    portfolios[user_id] = Portfolio(user_id=user_id)
    save_portfolios(portfolios)
    '''
    
    # Создаём пустой портфель через db
    portfolio = Portfolio(user_id=user_id)
    db.save_portfolio(portfolio)
    print(f"✅ Портфель для пользователя '{username}' создан.")

    global current_user
    current_user = user  # ✅ сохраняем объект User
    print(f"🔧 Регистрация успешна. Текущий пользователь: {current_user.username} 
        (id={current_user.user_id})") # noqa: E501

    # Успешный ответ
    print(f"Пользователь '{username}' зарегистрирован (id={user_id}). Войдите: login 
        --username {username} --password ****") # noqa: E501
"""
def cmd_register(args):
    # global current_user

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
    if len(password) < 4:
        print("Пароль должен быть не короче 4 символов")
        return

    # Загружаем пользователей
    users = db.load_users_dict()

    # Проверка уникальности
    if any(user.username == username for user in users.values()):
        print(f"Имя пользователя '{username}' уже занято")
        return

    # Генерация ID и соли
    user_id = max(users.keys(), default=0) + 1
    salt = secrets.token_urlsafe(8)

    # Создаём пользователя (пароль хэшируется внутри)
    user = User.create_user(
        user_id=user_id,
        username=username,
        password=password,
        salt=salt,
        registration_date=datetime.now()
    )

    # Сохраняем пользователя
    db.save_user(user)

    # Создаём портфель
    portfolio = Portfolio(user_id=user_id)
    db.save_portfolio(portfolio) # Сохраняем пустой портфель
    print(f"✅ Портфель для пользователя '{username}' создан.")

    # ✅ Добавляем начальный капитал
    try:
        portfolio.add_currency("USD", 1000.0)
        db.save_portfolio(portfolio)  # Сохраняем с USD
        print(f"✅ Начальный баланс: 1000 USD добавлен для '{username}'")
    except ValueError as e:
        print(f"⚠️ Не удалось добавить USD: {e}")

    # ✅ Регистрация = автоматический вход    
    global current_user
    current_user = user
    print(f"✅ Привет, {username} Вы успешно зарегистрированы и вошли в систему.")

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
    # users = load_users()
    users = db.load_users_dict()

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
    print(f"\n📊 Портфель пользователя {current_user.username} (ID: 
        {current_user.user_id}):") # noqa: E501
    for code, wallet in portfolio.wallets.items():
        print(f"  {code}: {wallet.balance}")
    total = portfolio.get_total_value()
    print(f"Общая стоимость (в USD): ${total:,.2f}")
'''

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
    
    # Загружаем курсы через DatabaseManager
    rates_data, last_updated = db.load_rates_with_timestamp()
    supported_rates = {k: v for k, v in rates_data.items() if k != "last_updated"}

    # Проверка, что базовая валюта поддерживается
    # supported_rates = load_rates()
    if base_currency not in supported_rates:
        print(f"Неизвестная базовая валюта '{base_currency}'")
        return

    # Загружаем портфель пользователя
    # portfolio = get_portfolio(current_user.user_id)
    portfolio = get_portfolio(current_user)  # ✅ объект User
    if portfolio is None:
        print("🔧 Портфель не найден — создаём пустой...")
        portfolio = Portfolio(user_id=current_user.user_id)
        db.save_portfolio(portfolio)

    # Получаем кошельки
    wallets = portfolio.wallets

    if not wallets:
        print(f"Портфель пользователя '{current_user.username}' пуст.")
        return

    # print(f"Портфель пользователя '{current_user.username}' (база: {base_currency}):")
    base_info = "" if base_currency == "USD" else f" (в {base_currency})"
    print(f"Портфель пользователя '{current_user.username}'{base_info}:")

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
        print(f"- {code}: {wallet.balance:,.6f} → {value_in_base:,.2f} {base_currency}")

    print("-" * 40)
    print(f"ИТОГО: {total_value:,.2f} {base_currency}")
'''
'''
def cmd_show_portfolio(args):
    global current_user

    if not current_user:
        print("Сначала выполните login")
        return

    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: show-portfolio [--base <валюта>]")
        return

    base_currency = parsed.get("base", "USD").strip().upper()

    # Загружаем портфель
    portfolio = get_portfolio(current_user)
    if portfolio is None:
        print("🔧 Портфель не найден — создаём пустой...")
        portfolio = Portfolio(user_id=current_user.user_id)
        db.save_portfolio(portfolio)

    wallets = portfolio.wallets
    if not wallets:
        print(f"Портфель пользователя '{current_user.username}' пуст.")
        return

    base_info = "" if base_currency == "USD" else f" (в {base_currency})"
    print(f"Портфель пользователя '{current_user.username}'{base_info}:")

    total_value = 0.0

    # ✅ Импортируем get_exchange_rate и CurrencyNotFoundError
    from valutatrade_hub.core.usecases import get_exchange_rate, CurrencyNotFoundError

    for wallet in wallets.values():
        code = wallet.currency_code
        try:
            # ✅ Единый способ получения курса
            rate = get_exchange_rate(code, base_currency)
            value_in_base = wallet.balance * rate
            total_value += value_in_base
            print(f"- {code}: {wallet.balance:,.6f}  → {value_in_base:,.2f} 
                {base_currency}") # noqa: E501
        except CurrencyNotFoundError as e:
            print(f"- {code}: {wallet.balance:,.6f}  → курс {code}→{base_currency} 
                неизвестен, пропущено") # noqa: E501
            continue

    print("-" * 40)
    print(f"ИТОГО: {total_value:,.2f} {base_currency}")
'''

def cmd_show_portfolio(args):
    global current_user

    if not current_user:
        print("Сначала выполните login")
        return

    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: show-portfolio [--base <валюта>] [--pretty]")
        return

    base_currency = parsed.get("base", "USD").strip().upper()
    pretty = bool(parsed.get("pretty"))

    # Загружаем портфель
    portfolio = get_portfolio(current_user)
    if portfolio is None:
        print("🔧 Портфель не найден — создаём пустой...")
        portfolio = Portfolio(user_id=current_user.user_id)
        db.save_portfolio(portfolio)

    wallets = portfolio.wallets
    if not wallets:
        if pretty:
            print("💼 Пустой портфель")
        else:
            print(f"Портфель пользователя '{current_user.username}' пуст.")
        return

    # Эмодзи для популярных валют
    EMOJI = {"USD": "💵", "EUR": "💶", "BTC": "🪙", "ETH": "🔷", "RUB": "🇷🇺"}
    total_value = 0.0

    from valutatrade_hub.core.usecases import CurrencyNotFoundError, get_exchange_rate

    if pretty:
        # ✅ Красивый режим
        print(f"💼 Портфель '{current_user.username}':")
        for wallet in wallets.values():
            code = wallet.currency_code
            emoji = EMOJI.get(code, "💰")
            try:
                rate = get_exchange_rate(code, base_currency)
                value_in_base = wallet.balance * rate
                total_value += value_in_base
                print(f"{emoji} {code}: {value_in_base:,.2f}")
            except CurrencyNotFoundError:
                print(f"{emoji} {code}: курс {base_currency} неизвестен")
        print("──────────────────────")
        print(f"🎯 ИТОГО: {total_value:,.2f} {base_currency}")
    else:
        # Стандартный режим — как было
        base_info = "" if base_currency == "USD" else f" (в {base_currency})"
        print(f"Портфель пользователя '{current_user.username}'{base_info}:")

        for wallet in wallets.values():
            code = wallet.currency_code
            try:
                rate = get_exchange_rate(code, base_currency)
                value_in_base = wallet.balance * rate
                total_value += value_in_base
                print(f"- {code}: {wallet.balance:,.6f}  → {value_in_base:,.2f} {base_currency}") # noqa: E501
            except CurrencyNotFoundError:
                print(f"- {code}: {wallet.balance:,.6f}  → курс {code}→{base_currency} неизвестен, пропущено") # noqa: E501

        print("-" * 40)
        print(f"ИТОГО: {total_value:,.2f} {base_currency}")

'''
def cmd_show_portfolio(args):
    global current_user

    if not current_user:
        print("Сначала выполните login")
        return

    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        return

    pretty = bool(parsed.get("pretty"))

    try:
        portfolio = db.get_portfolio(current_user.user_id)
        total_usd = 0.0

        if pretty:
            # ✅ Красивый режим
            print(f"💼 Портфель пользователя '{current_user.username}':")
            for wallet in portfolio.wallets:
                value_usd = wallet.balance * get_exchange_rate(wallet.currency_code, 
                    "USD") # noqa: E501
                total_usd += value_usd
                # Эмодзи по валюте
                emoji = {"USD": "💵", "EUR": "💶", "BTC": "🪙"}
                    .get(wallet.currency_code, "💰")# noqa: E501
                print(f"{emoji} {wallet.currency_code}: {value_usd:,.2f}")
            print("──────────────────────")
            print(f"💼 ИТОГО: {total_usd:,.2f} USD")
        else:
            # Стандартный режим — с деталями
            print(f"Портфель пользователя '{current_user.username}':")
            for wallet in portfolio.wallets:
                rate = get_exchange_rate(wallet.currency_code, "USD")
                value_usd = wallet.balance * rate
                total_usd += value_usd
                print(f"- {wallet.currency_code}: {wallet.balance:.6f}  → 
                    {value_usd:.2f} USD") # noqa: E501
            print("----------------------------------------")
            print(f"ИТОГО: {total_usd:,.2f} USD")

    except Exception as e:
        print(f"❌ Ошибка при отображении портфеля: {e}")
'''
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

    print(f"Покупка выполнена: {amount:,.4f} {currency} по курсу {rate:,.2f} 
        USD/{currency}") # noqa: E501
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
        confirm = input(f"🛒 Подтвердите покупку {amount} {currency} за {usd_cost:.2f} USD? (y/n): ") # noqa: E501
        if confirm.lower() != 'y':
            print("ℹ️ Покупка отменена.")
            return

        usecase_buy(current_user.user_id, currency, amount)
        print(f"✅ Успешно куплено: {amount} {currency}")

    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except InsufficientFundsError as e:
        print(f"❌ Недостаточно средств: доступно {e.available:.2f} USD, требуется {e.required:.2f} USD") # noqa: E501
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
        print(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся 
            автоматически при первой покупке.") # noqa: E501
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

    print(f"Продажа выполнена: {amount:,.4f} {currency} по курсу {rate:,.2f} 
        USD/{currency}") # noqa: E501
    print("Изменения в портфеле:")
    print(f"  {currency}: было {new_balance + amount:,.4f} → стало {new_balance:,.4f}")
    print(f"Оценочная выручка: {revenue_usd:,.2f} USD")
'''
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
        confirm = input(f"💰 Подтвердите продажу {amount} {currency} за 
            {revenue_usd:.2f} USD? (y/n): ") # noqa: E501
        if confirm.lower() != 'y':
            print("ℹ️ Продажа отменена.")
            return

        revenue = usecase_sell(current_user.user_id, currency, amount)
        print(f"✅ Продано: {amount} {currency} → получено {revenue:.2f} USD")

    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except InsufficientFundsError as e:
        print(f"❌ Недостаточно {currency}: доступно {e.available:.6f}, 
            требуется {e.required:.6f}") # noqa: E501
    except Exception as e:
        print(f"❌ Ошибка при продаже: {e}")
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
        print("Использование: sell --currency <валюта> --amount <число> [--pretty]")
        return

    currency = parsed.get("currency")
    amount_str = parsed.get("amount")
    pretty = bool(parsed.get("pretty"))

    if not currency:
        print("❌ Параметр --currency обязателен." if pretty else "Ошибка: параметр --currency обязателен.") # noqa: E501
        return
    if not amount_str:
        print("❌ Параметр --amount обязателен." if pretty else "Ошибка: параметр --amount обязателен.") # noqa: E501
        return

    currency = currency.strip().upper()
    try:
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError
    except ValueError:
        print("❌ 'amount' должен быть положительным числом")
        return

    try:
        rate = usecase_get_rate(currency, "USD")
        revenue_usd = amount * rate

        if pretty:
            # ✅ Красивый режим
            print(f"🪙 Продаём: {amount:,.6f} {currency}")
            print(f"💱 Курс: 1 {currency} = {rate:,.6f} USD")
            print(f"💵 Получим: {revenue_usd:,.2f} USD")
            confirm = input("✅ Подтвердите продажу? (y/n): ")
        else:
            # Обычный режим
            print(f"🔍 Курс {currency}/USD: {rate:.6f} → Выручка: {revenue_usd:.2f} USD") # noqa: E501
            confirm = input(f"💰 Подтвердите продажу {amount} {currency} за {revenue_usd:.2f} USD? (y/n): ") # noqa: E501

        if confirm.lower() != 'y':
            if pretty:
                print("ℹ️ Отменено")
            else:
                print("ℹ️ Продажа отменена.")
            return

        # Выполняем продажу
        usecase_sell(current_user.user_id, currency, amount)

        if pretty:
            print("✅ Успешно!")
            print(f"🪙 {amount:,.6f} {currency} продано")
            print(f"💵 +{revenue_usd:,.2f} USD зачислено")
        else:
            print(f"✅ Продано: {amount} {currency} → получено {revenue_usd:.2f} USD")

    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except InsufficientFundsError as e:
        msg = f"🪙 Недостаточно: есть {e.available:.6f}, нужно {e.required:.6f}" \
                if pretty  else f"❌ Недостаточно {currency}: доступно {e.available:.6f}, требуется {e.required:.6f}" # noqa: E501
        print(msg)
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
        print(f"У вас нет кошелька '{currency}'. Добавьте валюту: она создаётся 
            автоматически при первой покупке.") # noqa: E501
        return

    # Проверяем баланс
    if wallet.balance < amount:
        print(f"Недостаточно средств: доступно {wallet.balance:,.4f} {currency}, 
            требуется {amount:,.4f} {currency}") # noqa: E501
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

    print(f"Продажа выполнена: {amount:,.4f} {currency} по курсу {rate:,.2f} 
        USD/{currency}") # noqa: E501
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
        print(f"Курс {from_curr}→{to_curr}: {forward_rate:.8f} (обновлено: 
            {updated_str})") # noqa: E501
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
        # rate = get_exchange_rate(from_curr, to_curr)
        if rate is None:
            print("⚠️ Курсы устарели или недоступны. Запустите: update-rates")
        else:
            print(f"💱 {from_curr}/{to_curr} = {rate:,.2f}")

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
'''

def cmd_get_rate(args):
    try:
        parsed = parse_args(args)
        from_curr = parsed.get("from")
        to_curr = parsed.get("to")
        pretty = "pretty" in parsed  # ✅ Проверяем флаг --pretty

        if not from_curr:
            raise ValueError("Параметр --from обязателен.")
        if not to_curr:
            raise ValueError("Параметр --to обязателен.")

        from_curr = from_curr.strip().upper()
        to_curr = to_curr.strip().upper()

        # Вся логика — в usecase
        rate = usecase_get_rate(from_curr, to_curr)

        if rate is None:
            print("⚠️ Курсы устарели или недоступны. Запустите: update-rates")
            return
        '''
        if pretty:
            # ✅ Только красивый вывод
            print(f"1 {from_curr} = {rate:,.2f} {to_curr}")
        else:
            # Подробный режим — как раньше
            print(f"💱 {from_curr}/{to_curr} = {rate:,.2f}")
            print(f"💱 {from_curr}/{to_curr} = {rate:.8f}")
            print(f"🔄 1 {from_curr} = {rate:.8f} {to_curr}")
        '''
        if pretty:
            # 🌟 Красивый режим
            if rate < 0.01:
                # Маленькие числа — с 8 знаками или в экспоненте
                print(f"💱 {from_curr} → {to_curr}")
                print(f"📊 1 {from_curr} = {rate:.8f} {to_curr}")
            else:
                print(f"💱 {from_curr} → {to_curr}")
                print(f"✅ 1 {from_curr} = {rate:.2f} {to_curr}")
        else:
            # Стандартный режим
            print(f"Курс {from_curr}/{to_curr}: {rate:.6f}")

    except ValueError as e:
        print(e)
        print("Использование: get-rate --from <валюта> --to <валюта> [--pretty]")
    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except ApiRequestError as e:
        print(f"🌐 Ошибка API: {e}")
    except Exception as e:
        print(f"❌ Ошибка: {e}")

'''
def cmd_get_rate(args):
    try:
        parsed = parse_args(args)
    except ValueError as e:
        print(e)
        print("Использование: get-rate --from <валюта> --to <валюта> [--pretty]")
        return

    from_currency = parsed.get("from")
    to_currency = parsed.get("to")
    pretty = "pretty" in parsed  # ✅ Проверяем флаг --pretty

    if not from_currency or not to_currency:
        print("Ошибка: --from и --to обязательны.")
        return

    from_currency = from_currency.strip().upper()
    to_currency = to_currency.strip().upper()

    try:
        rate = get_exchange_rate(from_currency, to_currency)

        if pretty:
            # ✅ Только красивый вывод
            print(f"1 {from_currency} = {rate:,.2f} {to_currency}")
        else:
            # Стандартный режим с деталями
            print(f"💱 {from_currency}/{to_currency} = {rate:,.6f}")
            print(f"💱 {from_currency}/{to_currency} = {rate}")
            print(f"🔄 1 {from_currency} = {rate} {to_currency}")

    except CurrencyNotFoundError as e:
        print(f"❌ Валюта '{e.code}' не поддерживается.")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
'''

def create_update_rates_parser(subparsers) -> None:
    """Создаёт парсер для команды update-rates"""
    parser = subparsers.add_parser(
        "update-rates",
        help="Запустить немедленное обновление курсов валют"
    )
    parser.add_argument(
        "--source",
        choices=["coingecko", "exchangerate"],
        help="Обновить данные только из указанного источника"
    )

'''
def cmd_update_rates(args: argparse.Namespace) -> None:
    """Обработчик команды update-rates"""
    if not PARSER_AVAILABLE:
        print("❌ Parser Service не доступен. Убедитесь, что папка parser_service 
            существует и зависимости установлены.") # noqa: E501
        return

    print("INFO: Starting rates update...")

    clients: List = []
    source_map: Dict[str, Any] = {
        "coingecko": CoinGeckoClient,
        "exchangerate": ExchangeRateApiClient
    }

    selected_sources = []

    # Формируем список клиентов по аргументу --source
    if args.source is None:
        clients = [ExchangeRateApiClient(), CoinGeckoClient()]
        selected_sources = ["ExchangeRate-API", "CoinGecko"]
    else:
        source_key = args.source
        client_class = source_map[source_key]
        clients.append(client_class())
        selected_sources = [source_key.replace("coingecko", "CoinGecko").replace
            ("exchangerate", "ExchangeRate-API")] # noqa: E501

    # Создаём обновляльщик
    updater = RatesUpdater(clients)

    # Запускаем обновление (уже встроено логирование в RatesUpdater)
    success = updater.run_update()

    # Формируем итоговое сообщение
    if success:
        total = len(updater.pairs)
        last_refresh = updater.timestamp
        print(f"INFO: Writing {total} rates to {config.RATES_FILE_PATH}...")
        print(f"Update successful. Total rates updated: {total}. Last refresh: 
            {last_refresh}") # noqa: E501
    else:
        print("Update completed with errors. Check logs/parser.log for details.")
'''

def cmd_update_rates(args: argparse.Namespace) -> None:
    """Обработчик команды update-rates — с поддержкой офлайн-режима 
    и безопасным импортом"""
    
    # Проверка доступности парсера (по API-ключам)
    if not PARSER_AVAILABLE:
        print("❌ Обновление курсов недоступно: нет API-ключа.")
        print("💡 Укажите EXCHANGERATE_API_KEY в .env, чтобы включить обновление.")
        return

    #Отложенная загрузка модулей — чтобы не падать, если parser_service не импортируется
    try:
        from valutatrade_hub.parser_service.api_clients import (
            CoinGeckoClient,
            ExchangeRateApiClient,
        )
        from valutatrade_hub.parser_service.config import config
        from valutatrade_hub.parser_service.updater import RatesUpdater
    except ImportError as e:
        print(f"❌ Не удалось загрузить модули парсера: {e}")
        print("💡 Убедитесь, что папка parser_service и все зависимости установлены.")
        return

    print("INFO: Starting rates update...")

    clients = []
    source_map = {
        "coingecko": CoinGeckoClient,
        "exchangerate": ExchangeRateApiClient
    }

    selected_sources = []

    # Формируем список клиентов по аргументу --source
    if args.source is None:
        # Оба источника
        try:
            clients.append(ExchangeRateApiClient())
            clients.append(CoinGeckoClient())
            selected_sources = ["ExchangeRate-API", "CoinGecko"]
        except Exception as e:
            print(f"❌ Не удалось инициализировать клиент: {e}")
            return
    else:
        # Один источник
        if args.source not in source_map:
            print(f"❌ Неизвестный источник: {args.source}. Доступные: coingecko, exchangerate") # noqa: E501
            return
        client_class = source_map[args.source]
        try:
            clients.append(client_class())
            selected_source_name = args.source.replace("coingecko", "CoinGecko").replace("exchangerate", "ExchangeRate-API") # noqa: E501
            selected_sources = [selected_source_name]
        except Exception as e:
            print(f"❌ Ошибка при создании клиента {args.source}: {e}")
            return

    # Создаём обновляльщик
    try:
        # updater = RatesUpdater(clients=clients)
        updater = RatesUpdater()
    except Exception as e:
        print(f"❌ Не удалось создать RatesUpdater: {e}")
        return

    # Запускаем обновление
    try:
        success = updater.run_update()
    except Exception as e:
        print(f"❌ Ошибка при выполнении обновления: {e}")
        print("💡 Проверьте подключение к интернету и корректность API-ключей.")
        return

    # Формируем итоговое сообщение
    if success:
        total = len(updater.pairs)
        last_refresh = updater.timestamp
        print(f"INFO: Writing {total} rates to {config.RATES_FILE_PATH}...")
        print(f"✅ Update successful. Total rates updated: {total}. Last refresh: {last_refresh}") # noqa: E501
    else:
        print("⚠️ Update completed with errors or no new data. Check logs/parser.log for details.") # noqa: E501

'''
def create_show_rates_parser(subparsers) -> None:
    """Создаёт парсер для команды show-rates"""
    parser = subparsers.add_parser(
        "show-rates",
        aliases=["show", "rates"],
        help="Показать актуальные курсы из локального кеша"
    )
    parser.add_argument(
        "--currency", "-c",
        type=str.upper,
        help="Показать курсы только для указанной валюты (напр. BTC)"
    )
    parser.add_argument(
        "--top", "-n",
        type=int,
        help="Показать N самых дорогих криптовалют по отношению к базе"
    )
    parser.add_argument(
        "--base", "-b",
        type=str.upper,
        default="USD",
        help="Базовая валюта для отображения (по умолчанию: USD)"
    )
'''

def create_show_rates_parser(subparsers) -> None:
    """Создаёт парсер для команды show-rates с алиасами и группировкой"""
    parser = subparsers.add_parser(
        "show-rates",
        aliases=["show", "rates"],
        help="Показать актуальные курсы из локального кеша"
    )
    parser.description = "Отображает сохранённые курсы из файла rates.json. Поддерживает фильтрацию и сортировку." # noqa: E501

    # Фильтрация
    filter_group = parser.add_argument_group("фильтрация")
    filter_group.add_argument("--currency", "-c", type=str.upper, help="Показать курсы только для указанной валюты (напр. BTC)") # noqa: E501
    filter_group.add_argument("--base", "-b", type=str.upper, default="USD", help="Базовая валюта (по умолчанию: USD)") # noqa: E501

    # Сортировка
    sort_group = parser.add_argument_group("сортировка")
    sort_group.add_argument("--top", "-n", type=int, help="Показать топ-N самых дорогих активов по отношению к базе") # noqa: E501

'''
def cmd_show_rates(args: argparse.Namespace) -> None:
    """Обработчик команды show-rates"""
    if not PARSER_AVAILABLE and not os.path.exists("data/rates.json"):
        print("❌ Локальный кеш курсов пуст. Выполните 'update-rates', 
            чтобы загрузить данные.") # noqa: E501
        return

    # Определяем путь к файлу
    rates_file = config.RATES_FILE_PATH if PARSER_AVAILABLE else RATES_FILE_PATH

    if not os.path.exists(rates_file):
        print("❌ Локальный кеш курсов пуст. Выполните 'update-rates', 
            чтобы загрузить данные.") # noqa: E501
        return

    # Читаем кеш
    try:
        with open(rates_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (json.JSONDecodeError, Exception):
        print("❌ Ошибка чтения файла кеша. Файл повреждён.")
        return

    pairs = data.get("pairs", {})
    last_refresh = data.get("last_refresh", "неизвестно")

    if not pairs:
        print("❌ Локальный кеш курсов пуст. Выполните 'update-rates', 
            чтобы загрузить данные.") # noqa: E501
        return

    # Фильтрация по валюте: ищем пары, где валюта в начале (например, BTC_USD)
    filtered_pairs = {}
    currency = args.currency
    base = args.base

    for pair, info in pairs.items():
        from_cur, to_cur = pair.split("_", 1) if "_" in pair else (pair, "")

        # Фильтр: --currency BTC → ищем пары, начинающиеся с BTC
        if currency and not from_cur == currency:
            continue

        # Фильтр: --base EUR → конвертируем только те, что в USD, если нужно
        if to_cur != base:
            # Пока просто пропускаем — у нас курсы только к USD
            # (в будущем можно добавить кросс-курсы)
            continue

        filtered_pairs[pair] = info

    # Если есть --top: сортируем по rate и берём топ-N
    if args.top is not None:
        sorted_pairs = sorted(
            filtered_pairs.items(),
            key=lambda x: x[1]["rate"],
            reverse=True
        )[:args.top]
        filtered_pairs = dict(sorted_pairs)

    # Если после фильтрации нет данных
    if not filtered_pairs:
        if currency:
            print(f"❌ Курс для '{currency}' не найден в кеше.")
        else:
            print("❌ По заданным фильтрам ничего не найдено.")
        return

    # Вывод
    print(f"Rates from cache (updated at {last_refresh}):")
    for pair, info in filtered_pairs.items():
        rate = info["rate"]
        print(f"- {pair}: {rate:,.6f}".rstrip("0").rstrip("."))
'''

def cmd_show_rates(args: argparse.Namespace) -> None:
    """Обработчик команды show-rates — с поддержкой офлайн-режима 
    и безопасным доступом к данным"""
    
    # Отложенная загрузка config — чтобы не падать, если parser_service недоступен
    try:
        from valutatrade_hub.parser_service.config import config
        rates_file = config.RATES_FILE_PATH
    except (ImportError, AttributeError):
        # fallback: используем локальный путь
        import os
        rates_file = os.path.join("data", "rates.json")

    # Проверяем, существует ли файл
    if not os.path.exists(rates_file):
        print("❌ Локальный кеш курсов не найден. Выполните 'update-rates', чтобы загрузить данные.") # noqa: E501
        return

    # Читаем кеш
    try:
        with open(rates_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError:
        print("❌ Ошибка: файл rates.json повреждён или пуст.")
        return
    except Exception as e:
        print(f"❌ Ошибка при чтении файла: {e}")
        return

    pairs = data.get("pairs", {})
    last_refresh = data.get("last_refresh", "неизвестно")

    if not pairs:
        print("❌ Кеш курсов пуст. Выполните 'update-rates', чтобы загрузить данные.")
        return

    # Фильтрация
    filtered_pairs = {}

    for pair, info in pairs.items():
        if "rate" not in info:
            continue

        # Разбиваем пару: например, BTC_USD
        if "_" not in pair:
            continue
        from_cur, to_cur = pair.split("_", 1)

        # Фильтр: --currency BTC → показываем только пары с этим активом
        if args.currency and from_cur.upper() != args.currency.upper():
            continue

        # Фильтр: --base USD → показываем только курсы к этой валюте
        if args.base and to_cur.upper() != args.base.upper():
            continue

        filtered_pairs[pair] = info

    # Сортировка: --top N
    if args.top is not None:
        try:
            n = int(args.top)
            sorted_pairs = sorted(
                filtered_pairs.items(),
                key=lambda x: x[1]["rate"],
                reverse=True
            )[:n]
            filtered_pairs = dict(sorted_pairs)
        except (ValueError, TypeError):
            print("⚠️ Некорректное значение для --top. Используется без ограничений.")

    # Проверка результата
    if not filtered_pairs:
        filters = []
        if args.currency:
            filters.append(f"актив '{args.currency.upper()}'")
        if args.base:
            filters.append(f"база '{args.base.upper()}'")
        filters_str = ", ".join(filters) if filters else "фильтры"
        print(f"❌ Нет данных по заданным: {filters_str}.")
        return

    # Вывод
    print(f"\n📊 Курсы из кеша (обновлено: {last_refresh})")
    print("-" * 50)
    for pair, info in filtered_pairs.items():
        rate = info["rate"]
        # Форматируем число: убираем лишние нули
        formatted_rate = f"{rate:,.10f}".rstrip("0").rstrip(".")
        print(f"{pair:12} → {formatted_rate}")
    print()  # пустая строка для читаемости

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
            elif cmd == "update-rates":
                if not PARSER_AVAILABLE:
                    print("❌ Нет API-ключа...")
                    continue
                source = args[0] if args else None
                cmd_update_rates(argparse.Namespace(source=source))
                '''
                elif cmd == "update-rates":
                    # Проверяем, доступен ли парсер
                    if not PARSER_AVAILABLE:
                        print("❌ Обновление курсов недоступно: нет API-ключа или 
                            ошибка конфигурации") # noqa: E501
                        print("💡 Укажите EXCHANGERATE_API_KEY в .env, чтобы включить 
                            обновление курсов") # noqa: E501
                        continue

                    # Импортируем только если нужно (опциональная зависимость)
                    try:
                        from valutatrade_hub.parser_service.updater import update_rates
                        from valutatrade_hub.cli.interface import 
                            create_update_rates_parser, cmd_update_rates # noqa: E501
                    except ImportError as e:
                        print(f"❌ Не удалось загрузить модуль обновления: {e}")
                        continue

                    # Настраиваем парсер
                    parser = argparse.ArgumentParser(prog="update-rates")
                    create_update_rates_parser(parser)

                    # Разбиваем ввод (например: "update-rates --force")
                    args_str = input("> update-rates ").strip()
                    args = args_str.split() if args_str else []

                    try:
                        parsed_args = parser.parse_args(args)
                        cmd_update_rates(parsed_args)
                    except SystemExit:
                        # Перехватываем выход из-за --help или ошибки
                        pass  # Просто возвращаемся в основной цикл
                '''
            elif cmd == "show-rates":
                try:
                    from valutatrade_hub.cli.interface import (
                        cmd_show_rates,
                        create_show_rates_parser,
                    )
                except ImportError as e:
                    print(f"⚠️ Не удалось загрузить парсер show-rates: {e}")
                    continue

                parser = argparse.ArgumentParser(prog="show-rates")
                create_show_rates_parser(parser)

                args_str = input("> show-rates ").strip()
                args = args_str.split() if args_str else []

                try:
                    parsed_args = parser.parse_args(args)
                    cmd_show_rates(parsed_args)
                except SystemExit:
                    pass  # --help или ошибка — просто возвращаемся
                """
                elif cmd == "update-rates":
                    # cmd_update_rates(args)
                    # Передаём строку в argparse
                    import sys
                    from valutatrade_hub.cli.interface import 
                        create_update_rates_parser, cmd_update_rates # noqa: E501

                    # Создаём парсер только для update-rates
                    parser = argparse.ArgumentParser()
                    subparsers = parser.add_subparsers(dest="command")
                    create_update_rates_parser(subparsers)

                    try:
                        args = parser.parse_args(args)
                        if args.command == "update-rates":
                            cmd_update_rates(args)
                    except SystemExit:
                        # argparse вызывает exit() при --help и ошибках
                        continue
                    '''
                    if PARSER_AVAILABLE:
                        print("🔄 Запуск обновления курсов...")
                        success = update_rates()
                        if success:
                            print("✅ Курсы успешно обновлены и сохранены в 
                                exchange_rates.json") # noqa: E501
                        else:
                            print("❌ Не удалось обновить курсы. Проверьте подключение 
                                и ключи API.") # noqa: E501
                    else:
                        print("❌ Parser Service недоступен. Убедитесь, что папка 
                            parser_service существует.") # noqa: E501
                    '''
                elif cmd == "show-rates":
                    # cmd_show_rates(args)
                    # Парсим аргументы
                    parser = argparse.ArgumentParser()
                    subparsers = parser.add_subparsers(dest="command")
                    create_show_rates_parser(subparsers)

                    try:
                        args = parser.parse_args(args)
                        if args.command == "show-rates":
                            cmd_show_rates(args)
                    except SystemExit:
                        # При --help
                        continue
                """
            elif cmd == "start-scheduler":
                if PARSER_AVAILABLE:
                    def run_scheduler():
                        try:
                            start_scheduler()
                        except Exception as e:
                            print(f"❌ Ошибка в планировщике: {e}")

                    thread = threading.Thread(target=run_scheduler, daemon=True)
                    thread.start()
                    print("⏰ Фоновый планировщик запущен. Курсы будут обновляться каждые 10 минут.") # noqa: E501
                else:
                    print("❌ Parser Service недоступен. Убедитесь, что папка parser_service существует.") # noqa: E501
            else:
                print("Неизвестная команда. Введите 'help' для справки.")
        except KeyboardInterrupt:
            print("\n👋 Программа завершена.")
            break
        except Exception as e:
            print(f"❌ Неожиданная ошибка: {e}")


if __name__ == "__main__":
    main()
