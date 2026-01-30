# main.py

import sys
from valutatrade_hub.cli.interface import main
from valutatrade_hub.logging_config import setup_logging

if __name__ == "__main__":
    setup_logging()
    main()


'''
# Отладка 1

if __name__ == "__main__":
    from valutatrade_hub.core.models import User
    from datetime import datetime
    from valutatrade_hub.core.models import User, Wallet, Portfolio

    setup_logging()
    # === Тесты ===
    print(True)
    print(False)

    # Создание пользователя
    user = User(1, "alice", "1234", "salt", datetime.now())
    print(user.verify_password("1234"))  # True
    print(user.verify_password("123"))   # False (короткий)
    print(user.verify_password("5678"))  # False (неверный)
    print("Пароль изменён:", user.change_password("5678"))
    print(user.verify_password("5678"))  # True
    print(user.to_dict())

    # Загрузка
    loaded_user = User.from_dict(user.to_dict())
    print("Загружен:", loaded_user.to_dict())

    # === Тест Wallet ===
    btc_wallet = Wallet("BTC", 0.05)
    btc_wallet.deposit(0.01)
    print(f"Пополнение: +0.01 BTC. Текущий баланс: {btc_wallet.balance} BTC")
    btc_wallet.withdraw(0.02)
    print(f"Снятие: -0.02 BTC. Текущий баланс: {btc_wallet.balance} BTC")

    # === Тест Portfolio ===
    # Сначала создаём кошельки
    eur_wallet = Wallet("EUR", 200.0)   # ✅ Создаём ДО добавления
    usd_wallet = Wallet("USD", 1500.0)
    btc_wallet = Wallet("BTC", 0.05)    # можно переиспользовать или создать новый

    # Создаём портфель
    portfolio = Portfolio(user_id=1)

    # Добавляем кошельки (только объекты!)
    portfolio.add_currency("USD", 1500.0)  # ✅ Создаст кошелёк и добавит
    portfolio.add_currency("EUR", 200.0)
    portfolio.add_currency("BTC", 0.05)

    # Печатаем результат
    print(portfolio)  # например: <Portfolio user_id=1 | EUR: 200.0, USD: 1500.0, BTC: 0.05>
    print(f"Общая стоимость: ${portfolio.get_total_value():,.2f} USD")

    # Попытка покупки (ошибку видим — это нормально)
    try:
        portfolio.buy_currency("ETH", amount=2.0, price_in_usd=3000.0)
    except ValueError as e:
        print("Ожидалась ошибка:", e)

    # Покупка с меньшей суммой — должна пройти
    try:
        portfolio.buy_currency("ETH", amount=0.5, price_in_usd=3000.0)  # 1500 USD
        print("Покупка 0.5 ETH прошла успешно!")
    except ValueError as e:
        print("Ошибка при покупке 0.5 ETH:", e)

    # Купим 0.01 BTC по 60 000 USD
    # portfolio.buy_currency("BTC", amount=0.01, price_in_usd=60000.0)
    # Попробуем купить BTC, когда нет денег
    try:
        portfolio.buy_currency("BTC", amount=0.01, price_in_usd=60000.0)
        print("❌ Ошибка: покупка прошла, хотя не должна была!")
    except ValueError as e:
        if "Недостаточно средств" in str(e):
            print("✅ ОК: отказано в покупке из-за нехватки средств")
        else:
            print(f"❌ Неожиданная ошибка: {e}")


    # Продадим 50 EUR по 1.07 USD
    portfolio.sell_currency("EUR", amount=50.0, price_in_usd=1.07)

    print(f"Новый баланс: ${portfolio.get_total_value():,.2f} USD")
'''

'''
Ниже примеры использования
'''

'''
# Отладка 2

if __name__ == "__main__":
    # === Тесты ===
    
    from valutatrade_hub.core.models import User, Wallet, Portfolio
    from datetime import datetime
    import json
    # Создание нового пользователя
    user = User(
        user_id=1,
        username="alice",
        hashed_password="b2b99ffdea5401f49c99c9953f8b865a477fdab92a9e121b269e5a4f259c62f4",
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
        loaded_user = User.from_dict (data[0])

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
    # portfolio.buy_currency("ETH", amount=2.0, price_in_usd=3000.0)  # Покупаем 2 ETH
    # Попробуем купить 2 ETH — должно не хватить денег
    try:
        portfolio.buy_currency("ETH", amount=2.0, price_in_usd=3000.0)
        print("❌ Ошибка: покупка прошла, хотя не должна была!")
    except ValueError as e:
        if "Недостаточно средств" in str(e):
            print("✅ ОК: отказано в покупке — нет денег")
        else:
            print(f"❌ Не та ошибка: {e}")

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
'''

'''
Альтернативный вид файла для сравнения
'''

'''
# main.py
from valutatrade_hub.cli.interface import main

if __name__ == "__main__":
    # === Тесты (только при прямом запуске) ===
    from valutatrade_hub.core.models import User, Portfolio, Wallet
    from datetime import datetime
    import json

    # Создаём тестовый портфель
    portfolio = Portfolio(user_id=1)
    portfolio.add_currency("USD", 1500.0)
    portfolio.add_currency("BTC", 0.05)
    portfolio.add_currency("EUR", 200.0)

    # Попытка купить ETH — обрабатываем ошибку
    try:
        portfolio.buy_currency("ETH", amount=2.0, price_in_usd=3000.0)
        print("✅ Куплено 2 ETH")
    except ValueError as e:
        print(f"❌ Ошибка: {e}")

    # Это сработает
    try:
        portfolio.buy_currency("ETH", amount=0.5, price_in_usd=3000.0)  # 1500 USD
        print("✅ Куплено 0.5 ETH")
    except ValueError as e:
        print(f"❌ Ошибка: {e}")

    # Продолжаем
    print("Тесты завершены.")

    # === Запуск CLI ===
    # main()  # Раскомментируй, когда будешь готов

'''

'''
# 3.1. Иерархия валют (наследование и полиморфизм)

# Примеры вывода
print(get_currency("USD"))  # [FIAT] USD — US Dollar (Issuing: United States)
print(get_currency("BTC"))  # [CRYPTO] BTC — Bitcoin (Algo: SHA-256, MCAP: 1.12e+12)

# Обработка неизвестного кода
try:
    get_currency("XYZ")
except CurrencyNotFoundError as e:
    print(e)  # Валюта с кодом 'XYZ' не найдена.

# Ошибки при создании
try:
    FiatCurrency("Euro", "eur", "Eurozone")  # ❌ не в верхнем регистре
except ValueError as e:
    print(e)

try:
    CryptoCurrency("", "BTC", "SHA-256", 1e12)  # ❌ пустое имя
except ValueError as e:
    print(e)
'''