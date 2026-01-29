# valutatrade_hub/core/models.py

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional

# реализация классов

class User:
    def __init__(self, user_id: int, username: str, password: str, salt: str, registration_date: datetime):
        self._user_id = user_id
        self._username = username
        self._salt = salt
        self._registration_date = registration_date
        # Хэшируем пароль при создании
        self._hashed_password = self._hash_password(password)

    # === Геттеры ===
    @property
    def user_id(self) -> int:
        return self._user_id

    @property
    def username(self) -> str:
        return self._username

    @username.setter
    def username(self, value: str):
        if not value or not value.strip():
            raise ValueError("Имя пользователя не может быть пустым.")
        self._username = value.strip()

    @property
    def hashed_password(self) -> str:
        return self._hashed_password

    @property
    def salt(self) -> str:
        return self._salt

    @property
    def registration_date(self) -> datetime:
        return self._registration_date

    # === Методы ===
    def get_user_info(self) -> Dict:
        """Возвращает информацию о пользователе (без пароля в открытом виде)"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date.isoformat(),
            "salt": self._salt
        }

    def _hash_password(self, password: str) -> str:
        """Хэширует пароль с солью с помощью SHA-256"""
        if len(password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов.")
        salted_password = password + self._salt
        return hashlib.sha256(salted_password.encode('utf-8')).hexdigest()

    def change_password(self, new_password: str):
        """Изменяет пароль после проверки длины"""
        self._hashed_password = self._hash_password(new_password)

    def verify_password(self, password: str) -> bool:
        """Проверяет, совпадает ли введённый пароль с хэшированным"""
        try:
            return self._hash_password(password) == self._hashed_password
        except ValueError:
            return False  # Если пароль короче 4 символов — точно не подходит

    # === JSON сериализация ===
    def to_dict(self) -> Dict:
        """Подготовка к сохранению в JSON"""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "hashed_password": self._hashed_password,
            "salt": self._salt,
            "registration_date": self._registration_date.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """Создание пользователя из словаря (например, из JSON)"""
        return cls(
            user_id=data['user_id'],
            username=data['username'],
            password="dummy",  # Не используется — пароль уже хэширован
            salt=data['salt'],
            registration_date=datetime.fromisoformat(data['registration_date'])
        )
        # Но Чтобы не передавать dummy, лучше — отдельный метод или хранить пароль отдельно
        # Альтернатива: добавим флаг skip_hash

    @classmethod
    def from_json_record(cls, data: Dict) -> 'User':
        """Создание пользователя из JSON-записи с уже хэшированным паролем"""
        user = cls.__new__(cls)  # Создаём экземпляр без вызова __init__
        user._user_id = data['user_id']
        user._username = data['username']
        user._hashed_password = data['hashed_password']
        user._salt = data['salt']
        user._registration_date = datetime.fromisoformat(data['registration_date'])
        return user

class Wallet:
    def __init__(self, currency_code: str, initial_balance: float = 0.0):
        self._currency_code = currency_code.strip().upper()
        self._balance = 0.0
        # Используем сеттер для валидации начального баланса
        self.balance = initial_balance

    # === Свойство balance с валидацией ===
    @property
    def balance(self) -> float:
        """Возвращает текущий баланс"""
        return self._balance

    @balance.setter
    def balance(self, value: float):
        """Устанавливает баланс, проверяя тип и неотрицательность"""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом.")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным.")
        self._balance = float(value)

    @property
    def currency_code(self) -> str:
        """Геттер для кода валюты"""
        return self._currency_code

    # === Методы ===
    def deposit(self, amount: float) -> None:
        """Пополнение баланса"""
        self._validate_amount(amount)
        self.balance += amount
        print(f"Пополнение: +{amount} {self._currency_code}. Текущий баланс: {self.balance} {self._currency_code}")

    def withdraw(self, amount: float) -> None:
        """Снятие средств, если достаточно средств"""
        self._validate_amount(amount)
        if amount > self.balance:
            raise ValueError(f"Недостаточно средств. Доступно: {self.balance} {self._currency_code}")
        self.balance -= amount
        print(f"Снятие: -{amount} {self._currency_code}. Текущий баланс: {self.balance} {self._currency_code}")

    def get_balance_info(self) -> Dict[str, float]:
        """Возвращает информацию о балансе"""
        return {
            "currency_code": self._currency_code,
            "balance": self.balance
        }

    def _validate_amount(self, amount: float) -> None:
        """Проверяет, что сумма — положительное число"""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом.")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной.")

    def to_dict(self) -> Dict:
        """Подготовка к сохранению в JSON"""
        return {
            "currency_code": self._currency_code,
            "balance": float(self.balance)  # ✅ Превращаем Decimal в float
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Wallet':
        """Создание кошелька из словаря (например, из JSON)"""
        return cls(
            currency_code=data['currency_code'],
            initial_balance=data['balance']
        )


# Импортируем Wallet, если он в другом файле
# from wallet import Wallet  # Раскомментировать при использовании

class Portfolio:
    # Простой словарь с фиктивными курсами для демонстрации
    _exchange_rates = {
        "USD": 1.0,
        "EUR": 1.07,      # 1 EUR = 1.07 USD
        "GBP": 1.25,      # 1 GBP = 1.25 USD
        "JPY": 0.0067,    # 1 JPY = 0.0067 USD
        "BTC": 60000.0,   # 1 BTC = 60 000 USD (условно)
        "ETH": 3000.0,    # 1 ETH = 3 000 USD
    }

    def __init__(self, user_id: int, wallets: Dict[str, 'Wallet'] = None):
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = {}

        if wallets:
            for currency, wallet in wallets.items():
                if not isinstance(wallet, Wallet):
                    raise TypeError(f"Объект для валюты {currency} должен быть экземпляром Wallet.")
                self._wallets[currency.upper()] = wallet

    # === Свойства ===
    @property
    def user_id(self) -> int:
        """Геттер: возвращает ID пользователя (только для чтения)"""
        return self._user_id

    @property
    def wallets(self) -> Dict[str, 'Wallet']:
        """Геттер: возвращает копию словаря кошельков (защита от внешнего изменения)"""
        return self._wallets.copy()

    # === Методы ===
    def add_currency(self, currency_code: str, initial_balance: float = 0.0) -> None:
        """Добавляет новый кошелёк в портфель, если валюта ещё не добавлена"""
        currency_code = currency_code.strip().upper()

        if currency_code in self._wallets:
            raise ValueError(f"Валюта {currency_code} уже есть в портфеле.")

        if not currency_code.isalpha() or len(currency_code) != 3:
            raise ValueError("Код валюты должен быть трёхбуквенным (например, USD, BTC).")

        wallet = Wallet(currency_code=currency_code, initial_balance=initial_balance)
        self._wallets[currency_code] = wallet
        print(f"Добавлена валюта: {currency_code} с балансом {initial_balance}")

    def get_wallet(self, currency_code: str) -> Optional['Wallet']:
        """Возвращает кошелёк по коду валюты или None, если не найден"""
        return self._wallets.get(currency_code.strip().upper())

    def get_total_value(self, base_currency: str = 'USD') -> float:
        """
        Возвращает общую стоимость портфеля в указанной базовой валюте.
        Пока поддерживается только USD как базовая валюта (для упрощения).
        """
        base_currency = base_currency.strip().upper()

        if base_currency != 'USD':
            raise NotImplementedError("Пока поддерживается только конвертация в USD.")

        total = 0.0
        for code, wallet in self._wallets.items():
            rate = self._exchange_rates.get(code)
            if rate is None:
                print(f"⚠️  Нет курса для {code}, пропускаем.")
                continue
            total += wallet.balance * rate
        return total

    # === Операции с портфелем ===
    def buy_currency(self, currency_code: str, amount: float, price_in_usd: float) -> None:
        """
        Покупка валюты: списание USD, пополнение кошелька валюты.
        price_in_usd — сколько стоит одна единица валюты в USD.
        """
        currency_code = currency_code.strip().upper()

        # Проверка: есть ли USD-кошелёк
        usd_wallet = self.get_wallet('USD')
        if not usd_wallet:
            raise ValueError("Нет USD-кошелька для списания средств.")

        total_cost = amount * price_in_usd
        if usd_wallet.balance < total_cost:
            raise ValueError(f"Недостаточно средств в USD. Требуется: {total_cost}, доступно: {usd_wallet.balance}")

        # Списываем USD
        usd_wallet.withdraw(total_cost)

        # Добавляем валюту (если кошелька нет — создаём)
        if currency_code not in self._wallets:
            self.add_currency(currency_code, initial_balance=0.0)

        # Пополняем кошелёк
        wallet = self.get_wallet(currency_code)
        wallet.deposit(amount)

        print(f"Куплено {amount} {currency_code} по цене {price_in_usd} USD за единицу.")

    def sell_currency(self, currency_code: str, amount: float, price_in_usd: float) -> None:
        """
        Продажа валюты: списание из кошелька, зачисление на USD.
        """
        currency_code = currency_code.strip().upper()

        wallet = self.get_wallet(currency_code)
        if not wallet:
            raise ValueError(f"Нет кошелька для валюты {currency_code}.")

        wallet.withdraw(amount)  # Проверка баланса

        # Зачисляем выручку в USD
        usd_wallet = self.get_wallet('USD')
        if not usd_wallet:
            self.add_currency('USD', 0.0)
            usd_wallet = self.get_wallet('USD')

        revenue = amount * price_in_usd
        usd_wallet.deposit(revenue)

        print(f"Продано {amount} {currency_code} по цене {price_in_usd} USD за единицу.")

    # === JSON сериализация ===
    def to_dict(self) -> Dict:
        """Подготовка к сохранению в JSON"""
        return {
            "user_id": self._user_id,
            "wallets": {code: wallet.to_dict() for code, wallet in self._wallets.items()}
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Portfolio':
        """Создание портфеля из словаря (например, из JSON)"""
        wallets = {}
        for code, wallet_data in data['wallets'].items():
            wallets[code] = Wallet.from_dict(wallet_data)
        return cls(user_id=data['user_id'], wallets=wallets)

    def __repr__(self):
        wallets_str = ", ".join(f"{code}: {wallet.balance}" for code, wallet in self.wallets.items())
        return f"Portfolio(user_id={self.user_id}, wallets={{{wallets_str}}})"