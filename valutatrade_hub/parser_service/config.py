import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from valutatrade_hub.core import constants


@dataclass
class ParserConfig:
    """
    Конфигурация парсера курсов.
    Загружает .env, использует default_factory для изменяемых типов.
    """
    load_dotenv() 

    # API-ключ из .env
    EXCHANGERATE_API_KEY: str = field(default_factory=lambda: os.getenv("EXCHANGERATE_API_KEY") or "")

    # Эндпоинты
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"

    # Валюты
    BASE_CURRENCY: str = "USD"
    FIAT_CURRENCIES: tuple = field(default_factory=lambda: ("EUR", "GBP", "RUB"))
    CRYPTO_CURRENCIES: tuple = field(default_factory=lambda: ("BTC", "ETH", "SOL"))
    CRYPTO_ID_MAP: dict = field(default_factory=lambda: {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
    })

    # Пути к файлам
    RATES_FILE_PATH: str = constants.RATES_PATH
    HISTORY_FILE_PATH: str = constants.EXCHANGE_RATES_PATH

    # Таймаут запросов
    REQUEST_TIMEOUT: int = 10