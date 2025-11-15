import hashlib
from valutatrade_hub.core import constants
import json
from copy import deepcopy
import pathlib


class User():
    def __init__(self, user_id, username, 
                 hashed_password, salt, registration_date):
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
    
    def get_user_info(self):
        print(f'ID: {self._user_id}\n' +
              f'Имя пользователя: {self._username}\n' + 
              f'Соль: {self._salt}\n' + 
              f'Дата регистрации: {self._registration_date}')
    
    def change_password(self, new_password):
        self._hashed_password = hashlib.sha256((new_password + self._salt).
                                               encode('utf-8')).hexdigest()
    
    def verify_password(self, password):
        return hashlib.sha256((password + self._salt).
                              encode('utf-8')).hexdigest() == self._hashed_password
    
    def get_user_id(self):
        return self._user_id
    
    def get_username(self):
        return self._username
    
    def set_username(self, new_username):
        if new_username:
            self._username = new_username
        else:
            print('Имя не может быть пустым.')
    
    def get_hashed_password(self):
        return (self._hashed_password, self._salt)
    
    def set_hashed_password(self, new_password):
        if len(new_password) >= 4:
            self.change_password(self, new_password)
        else:
            print('Длина пароля должна быть не меньше 4 символов.')
    
    def get_salt(self):
        return self._salt
    
    def get_registration_date(self):
        return self._registration_date


class Wallet():
    def __init__(self, currency_code, balance=.0):
        self._currency_code = currency_code
        self._balance = balance
        self.wallet = {
            currency_code: {
                'currency_code': self._currency_code,
                'balance': self._balance
            }
        }
    
    def deposit(self, amount):
        self._balance += amount
    
    def get_balance_info(self):
        print(f'Текущий баланс: {self._balance}')
    
    @property
    def balance(self):
        return self._balance
    
    @balance.setter
    def balance(self, value):
        self._balance = value
    
    def withdraw(self, amount):
        if amount <= self._balance:
            self.balance -= amount
        else:
            print('Сумма превышает баланс аккаунта.')


class Portfolio():
    def __init__(self, user_id, wallets):
        self._user_id = user_id
        self._wallets = wallets

        self.new_portfolio = {
            'user_id': self._user_id,
            'wallets': self._wallets
        }
    
    def add_currency(self, currency_code):
        if currency_code not in self._wallets.keys():
            new_wallet = Wallet(currency_code)
            self._wallets.update({
                currency_code: new_wallet.wallet[currency_code]
            })
    
    def get_total_value(self, rates, base):
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

    def get_wallet(self, currency_code):
        return self._wallets[currency_code]

    @property
    def user(self):
        with open(constants.USERS_PATH, 'r', encoding='utf-8') as f:
            users = json.load(f)
            for user in users:
                if self._user_id == user['user_id']:
                    username = user['username']
                    hashed_password = user['hashed_password']
                    salt = user['salt']
                    registration_date = user['registration_date']
        
        return User(self._user_id, username, hashed_password, 
                    salt, registration_date)
    
    @property
    def wallets(self):
        return deepcopy(self._wallets)
    

