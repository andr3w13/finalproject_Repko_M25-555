from abc import ABC, abstractmethod
import requests
from typing import Tuple, Dict
from time import perf_counter
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.core import exceptions

cfg = ParserConfig()


class BaseApiClient(ABC):
    """Абстрактный клиент для получения курсов. Возвращает rates + meta."""

    @abstractmethod
    def fetch_rates(self) -> Tuple[Dict[str, float], Dict[str, dict]]:
        """
        Возвращает:
         - rates: {'BTC_USD': 59337.21, ...}
         - meta:  {'BTC_USD': {'raw_id': 'bitcoin', 'request_ms': 123, 'status_code': 200}, ...}
        """
        raise NotImplementedError


class CoinGeckoClient(BaseApiClient):
    """Клиент CoinGecko: криптовалюты → BASE_CURRENCY."""

    def __init__(self, config: ParserConfig = cfg):
        self.config = config
        self.base = config.BASE_CURRENCY.lower()

    def fetch_rates(self) -> Tuple[Dict[str, float], Dict[str, dict]]:
        """Получает курсы криптовалют через CoinGecko."""
        ids = ','.join(self.config.CRYPTO_ID_MAP.values())
        params = {'ids': ids, 'vs_currencies': self.base}
        url = self.config.COINGECKO_URL

        started = perf_counter()
        try:
            resp = requests.get(url, params=params, timeout=self.config.REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise exceptions.ApiRequestError(f'CoinGecko request error: {e}')

        request_ms = int((perf_counter() - started) * 1000)
        status = resp.status_code

        try:
            body = resp.json()
        except ValueError:
            raise exceptions.ApiRequestError('CoinGecko returned invalid JSON')

        rates: Dict[str, float] = {}
        meta: Dict[str, dict] = {}
        for symbol, cg_id in self.config.CRYPTO_ID_MAP.items():
            price = body.get(cg_id, {}).get(self.base)
            if price is None:
                continue
            key = f'{symbol}_{self.config.BASE_CURRENCY}'
            rates[key] = float(price)
            meta[key] = {
                'raw_id': cg_id,
                'request_ms': request_ms,
                'status_code': status,
                'source': 'CoinGecko'
            }

        return rates, meta


class ExchangeRateApiClient(BaseApiClient):
    """Клиент ExchangeRate-API: фиат → BASE_CURRENCY."""

    def __init__(self, config: ParserConfig = cfg):
        self.config = config
        self.base = config.BASE_CURRENCY

    def fetch_rates(self) -> Tuple[Dict[str, float], Dict[str, dict]]:
        """Получает курсы фиата через ExchangeRate-API."""
        key = self.config.EXCHANGERATE_API_KEY
        if not key:
            raise exceptions.ApiRequestError('ExchangeRate API key is not set (EXCHANGERATE_API_KEY)')

        url = f'{self.config.EXCHANGERATE_API_URL}/{key}/latest/{self.base}'
        started = perf_counter()
        try:
            resp = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            resp.raise_for_status()
        except requests.RequestException as e:
            raise exceptions.ApiRequestError(f'ExchangeRate request error: {e}')

        request_ms = int((perf_counter() - started) * 1000)
        status = resp.status_code

        try:
            body = resp.json()
        except ValueError:
            raise exceptions.ApiRequestError('ExchangeRate API returned invalid JSON')

        if body.get('result') != 'success':
            reason = body.get('error-type') or body.get('result', 'unknown')
            raise exceptions.ApiRequestError(f'ExchangeRate API error: {reason}')

        rates_src = body.get('conversion_rates') or {}
        if not isinstance(rates_src, dict):
            raise exceptions.ApiRequestError('ExchangeRate API returned unexpected rates structure')

        rates: Dict[str, float] = {}
        meta: Dict[str, dict] = {}
        for fiat in self.config.FIAT_CURRENCIES:
            if fiat not in rates_src:
                continue
            value = rates_src[fiat]
            key = f'{fiat}_{self.base}'
            rates[key] = float(value)
            meta[key] = {
                'raw_id': fiat,
                'request_ms': request_ms,
                'status_code': status,
                'source': 'ExchangeRate-API'
            }

        return rates, meta