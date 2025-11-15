from abc import ABC, abstractmethod
from valutatrade_hub.core import exceptions


class Currency(ABC):
    def __init__(self, name, code):
        if 2 <= len(code) <= 5 and ' ' not in code and name:
            self.name = name.upper()
            self.code = code
        else:
            print('Неверное заданы имя и/или код.')
    
    @abstractmethod
    def get_display_info(self):
        pass


class CryptoCurrency(Currency):
    def __init__(self, name, code, algorithm, market_cap):
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
    
    def get_display_info(self):
        print(f'[CRYPTO] {self.code} — {self.name} ' +
              f'(Algo: {self.algorithm}, MCAP: {self.market_cap:.2e})')
    

class FiatCurrency(Currency):
    def __init__(self, name, code, issuing_country):
        super().__init__(name, code)
        self.issuing_country = issuing_country

    def get_display_info(self):
        print(f'[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})')


CURRENCIES = {
    'USD': FiatCurrency('United States Dollar', 'USD', 'USA'),
    'EUR': FiatCurrency('Euro', 'EUR', 'EU'),
    'JPY': FiatCurrency('Japanese Yen', 'JPY', 'Japan'),
    'BTC': CryptoCurrency('Bitcoin', 'BTC', 'SHA-256', 4.5e11),
    'ETH': CryptoCurrency('Ethereum', 'ETH', 'Ethash', 2.3e11),
}


def get_currency(code):
    code = code.upper()
    if code in CURRENCIES:
        return CURRENCIES[code]
    else:
        raise exceptions.CurrencyNotFoundError