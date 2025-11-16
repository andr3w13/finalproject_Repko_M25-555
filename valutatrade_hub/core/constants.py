from pathlib import Path
from valutatrade_hub.infra import settings


VALUTATRADE_HUB_PATH = Path(__file__).resolve().parents[1]

config = settings.SettingsLoader(
        VALUTATRADE_HUB_PATH / 'infra' / 'config.json'
    )

USERS_PATH = config.get('USERS_PATH')
RATES_PATH = config.get('RATES_PATH')
PORTFOLIOS_PATH = config.get('PORTFOLIOS_PATH')
BASE_CURRENCY = config.get('BASE_CURRENCY')
EXCHANGE_RATES_PATH = config.get('EXCHANGE_RATES_PATH')
RATES_TTL_SECONDS = config.get('RATES_TTL_SECONDS')
ACTIONS_LOG_PATH = config.get('ACTIONS_LOG_PATH')
LOGS_RAW_FORMAT = config.get('LOG_FORMAT')

CURRENT_SESSION = None