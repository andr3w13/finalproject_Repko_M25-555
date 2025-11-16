import hashlib
from valutatrade_hub.core import constants, exceptions
import json
from copy import deepcopy


class User:
    """Представляет пользователя системы с хэшированным паролем и метаданными."""

    def __init__(self, user_id: int, username: str, 
                 hashed_password: str, salt: str, registration_date: str):
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date

        self.new_user = {
            'user_id': self._user_id,
            'username': self._username,
            'hashed_password': self._hashed_password,
            'salt': self._salt,
            'registration_date': self._registration_date
        }
    
    def get_user_info(self) -> None:
        """Выводит информацию о пользователе."""
        print(f'ID: {self._user_id}\n'
              f'Имя пользователя: {self._username}\n' 
              f'Соль: {self._salt}\n' 
              f'Дата регистрации: {self._registration_date}')
    
    def change_password(self, new_password: str) -> None:
        """Меняет пароль, используя текущую соль."""
        self._hashed_password = hashlib.sha256((new_password + self._salt)
                                               .encode('utf-8')).hexdigest()
    
    def verify_password(self, password: str) -> bool:
        """Проверяет введённый пароль."""
        return hashlib.sha256((password + self._salt)
                              .encode('utf-8')).hexdigest() == self._hashed_password
    
    def get_user_id(self) -> int:
        """Возвращает ID пользователя."""
        return self._user_id
    
    def get_username(self) -> str:
        """Возвращает имя пользователя."""
        return self._username
    
    def set_username(self, new_username: str) -> None:
        """Устанавливает новое имя (не пустое)."""
        if new_username:
            self._username = new_username
        else:
            print('Имя не может быть пустым.')
    
    def get_hashed_password(self) -> tuple[str, str]:
        """Возвращает хэш и соль."""
        return (self._hashed_password, self._salt)
    
    def set_hashed_password(self, new_password: str) -> None:
        """Меняет пароль (мин. 4 символа)."""
        if len(new_password) >= 4:
            self.change_password(new_password)
        else:
            print('Длина пароля должна быть не меньше 4 символов.')
    
    def get_salt(self) -> str:
        """Возвращает соль."""
        return self._salt
    
    def get_registration_date(self) -> str:
        """Возвращает дату регистрации."""
        return self._registration_date


class Wallet:
    """Кошелёк для хранения баланса в конкретной валюте."""

    def __init__(self, currency_code: str, balance: float = 0.0):
        self._currency_code = currency_code
        self._balance = balance
        self.wallet = {
            currency_code: {
                'currency_code': self._currency_code,
                'balance': self._balance
            }
        }
    
    def deposit(self, amount: float) -> None:
        """Пополняет баланс."""
        self._balance += amount
    
    def get_balance_info(self) -> None:
        """Выводит текущий баланс."""
        print(f'Текущий баланс: {self._balance}')
    
    @property
    def balance(self) -> float:
        """Геттер баланса."""
        return self._balance
    
    @balance.setter
    def balance(self, value: float) -> None:
        """Сеттер баланса."""
        self._balance = value
    
    def withdraw(self, amount: float) -> None:
        """Снимает средства, если достаточно."""
        if amount <= self._balance:
            self.balance -= amount
        else:
            raise exceptions.InsufficientFundsError(
                self.balance,
                self._currency_code,
                amount
            )


class Portfolio:
    """Портфель пользователя с кошельками и пересчётом в базовую валюту."""

    def __init__(self, user_id: int, wallets: dict):
        self._user_id = user_id
        self._wallets = wallets

        self.new_portfolio = {
            'user_id': self._user_id,
            'wallets': self._wallets
        }
    
    def add_currency(self, currency_code: str) -> None:
        """Добавляет кошелёк для новой валюты."""
        if currency_code not in self._wallets:
            new_wallet = Wallet(currency_code)
            self._wallets.update({
                currency_code: new_wallet.wallet[currency_code]
            })
    
    def get_total_value(self, rates: dict, base: str) -> tuple[float | None, dict | None]:
        """Возвращает общую стоимость и детали в базовой валюте."""
        pairs = rates["pairs"]
        total = 0
        details = {}

        for currency, data in self._wallets.items():
            balance = data["balance"]

            if currency == base:
                converted = balance
            else:
                pair_name = f"{currency}_{base}"
                if pair_name not in pairs:
                    return None, None
                rate = pairs[pair_name]["rate"]
                converted = balance * rate

            total += converted
            details[currency] = {
                "original": balance,
                "converted": converted
            }

        return total, details

    def get_wallet(self, currency_code: str) -> dict:
        """Возвращает данные кошелька по коду валюты."""
        return self._wallets[currency_code]

    @property
    def user(self) -> User:
        """Загружает и возвращает объект User по user_id."""
        with open(constants.USERS_PATH, 'r', encoding='utf-8') as f:
            users = json.load(f)
            for user in users:
                if self._user_id == user['user_id']:
                    return User(
                        self._user_id,
                        user['username'],
                        user['hashed_password'],
                        user['salt'],
                        user['registration_date']
                    )
        raise ValueError(f"User with id {self._user_id} not found")

    @property
    def wallets(self) -> dict:
        """Возвращает глубокую копию кошельков."""
        return deepcopy(self._wallets)