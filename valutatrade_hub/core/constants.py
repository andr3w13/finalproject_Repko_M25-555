from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATA_PATH = PROJECT_ROOT / 'data'
USERS_PATH = DATA_PATH / 'users.json'
PORTFOLIOS_PATH = DATA_PATH / 'portfolios.json'
RATES_PATH = DATA_PATH / 'rates.json'

CURRENT_SESSION = None