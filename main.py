# main.py

import sys
from valutatrade_hub.cli.interface import main

if __name__ == "__main__":
    main()

'''
# Отладка 1

if __name__ == "__main__":
    # === Тесты ===
    print(True)
    print(False)

    # Создание пользователя
    user = User(1, "alice", "1234", "salt", datetime.now())
    print("Пароль изменён:", user.change_password("1234", "5678"))
    print(user.to_dict())

    # Загрузка
    loaded_user = User.from_dict(user.to_dict())
    print("Загружен:", loaded_user.to_dict())

    # Тест Wallet
    btc_wallet = Wallet("BTC", 0.05)
    btc_wallet.deposit(0.01)
    print(f"Пополнение: +0.01 BTC. Текущий баланс: {btc_wallet.balance} BTC")
    btc_wallet.withdraw(0.02)
    print(f"Снятие: -0.02 BTC. Текущий баланс: {btc_wallet.balance} BTC")

    # Тест Portfolio
    portfolio = Portfolio(user_id=1)
    portfolio.add_wallet("USD", 1500.0)
    portfolio.add_wallet("BTC", 0.05)
    portfolio.add_wallet("EUR", 200.0)

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

'''

'''
Ниже примеры использования
'''

'''
# Отладка 2

if __name__ == "__main__":
    # === Тесты ===
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
