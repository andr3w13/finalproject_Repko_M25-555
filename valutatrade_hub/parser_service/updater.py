import logging
from datetime import datetime, timezone
from typing import List
from valutatrade_hub.parser_service.api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from valutatrade_hub.parser_service.storage import ExchangeRatesRepo, RatesCache
from valutatrade_hub.parser_service.config import ParserConfig
from valutatrade_hub.core import exceptions

cfg = ParserConfig()
logger = logging.getLogger('parser')
if not logger.handlers:
    h = logging.StreamHandler()
    fmt = '%(levelname)s %(asctime)s %(message)s'
    h.setFormatter(logging.Formatter(fmt, datefmt='%Y-%m-%dT%H:%M:%S'))
    logger.addHandler(h)
    logger.setLevel(logging.INFO)


class RatesUpdater:
    """Обновляет курсы валют из API, сохраняет в кэш и историю."""

    def __init__(
        self,
        clients: List[BaseApiClient] = None,
        history_repo: ExchangeRatesRepo = None,
        cache: RatesCache = None,
        config: ParserConfig = cfg
    ):
        """Инициализирует клиенты, репозитории и конфиг."""
        self.config = config
        self.clients = clients or [CoinGeckoClient(config), ExchangeRateApiClient(config)]
        self.history = history_repo or ExchangeRatesRepo(config.HISTORY_FILE_PATH)
        self.cache = cache or RatesCache(config.RATES_FILE_PATH)

    @staticmethod
    def _utc_iso_now() -> str:
        return datetime.now(timezone.utc).replace(microsecond=0).isoformat() + 'Z'

    def run_update(self, source: str = None) -> dict:
        """
        Запускает обновление курсов.

        Args:
            source: 'coingecko' или 'exchangerate' — обновить только один источник.

        Returns:
            dict: summary с total_fetched, written_history, last_refresh, errors.
        """
        logger.info('Starting rates update...')
        collected_rates = {}
        collected_meta = {}
        total_fetched = 0
        errors = []

        for client in self.clients:
            client_name = client.__class__.__name__
            if source and source.lower() not in client_name.lower():
                logger.info(f'Skipping {client_name} (not matching source filter)')
                continue

            logger.info(f'Fetching from {client_name}...')
            try:
                rates, meta = client.fetch_rates()
                fetched = len(rates)
                total_fetched += fetched
                logger.info(f'OK ({fetched} rates)')
                collected_rates.update(rates)
                collected_meta.update(meta)
            except exceptions.ApiRequestError as e:
                logger.error(f'Failed to fetch from {client_name}: {e}')
                errors.append((client_name, str(e)))
                continue

        last_refresh = self._utc_iso_now()

        updated_pairs = {}
        for key, rate in collected_rates.items():
            from_code, to_code = key.split('_')
            updated_at = last_refresh
            source_name = collected_meta.get(key, {}).get('source', 'unknown')

            updated_pairs[key] = {
                'rate': float(rate),
                'updated_at': last_refresh, 
                'source': source_name
            }

        self.cache.write(updated_pairs, last_refresh)

        for key, rate in collected_rates.items():
            from_code, to_code = key.split('_')
            self.history.save_measurement(
                from_currency=from_code,
                to_currency=to_code,
                rate=rate,
                source=collected_meta.get(key, {}).get('source', 'unknown'),
                meta=collected_meta.get(key, {})
            )