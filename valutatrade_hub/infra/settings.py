import json
from pathlib import Path


class SettingsLoader:
    """
    Singleton, отвечающий за загрузку и хранение конфигурации проекта.

    Причина выбора подхода через __new__:
    - максимально простой и читаемый способ
    - легко контролировать единственный экземпляр
    - корректно работает при любых импортах (модуль создаёт объект один раз)
    """

    _instance = None

    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    DATA_PATH = PROJECT_ROOT / 'data'
    USERS_PATH = DATA_PATH / 'users.json'
    PORTFOLIOS_PATH = DATA_PATH / 'portfolios.json'
    RATES_PATH = DATA_PATH / 'rates.json'

    LOG_DIR = PROJECT_ROOT / 'logs'
    ACTIONS_LOG = LOG_DIR / 'actions.log'

    DEFAULT_CONFIG = {
        'DATA_PATH': str(DATA_PATH),
        'USERS_PATH': str(USERS_PATH),
        'PORTFOLIOS_PATH': str(PORTFOLIOS_PATH),
        'RATES_PATH': str(RATES_PATH),
        'RATES_TTL_SECONDS': 300,
        "LOG_DIR": str(LOG_DIR),
        "ACTIONS_LOG_PATH": str(ACTIONS_LOG),
        "LOG_FORMAT": "[{time}] {level}: {message}",
        "BASE_CURRENCY": "USD"
    }

    def __new__(cls, config_path):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path):
        if getattr(self, '_initialized', False):
            return

        if not hasattr(self, '_initialized'):
            self._initialized = True
            self.config_path = Path(config_path) if config_path else Path('config.json')
            self.DATA_PATH.mkdir(parents=True, exist_ok=True)
            self.LOG_DIR.mkdir(parents=True, exist_ok=True)
            self._ensure_config_file()
            self.reload()

        self._initialized = True

        self.config_path = Path(config_path) if config_path else Path('config.json')

        self._ensure_config_file()

        self.reload()

    def get(self, key, default=None):
        return self._config.get(key, default)

    def reload(self):
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

    def _ensure_config_file(self):
        """Создаёт config.json, если он отсутствует."""
        if self.config_path.exists():
            return

        for path in [self.USERS_PATH, self.PORTFOLIOS_PATH, self.RATES_PATH, self.ACTIONS_LOG]:
            if not path.exists():
                if path == self.ACTIONS_LOG:
                    path.write_text('', encoding='utf-8')
                else:
                    path.write_text('{}', encoding='utf-8')

        with open(self.config_path, 'w', encoding='utf-8') as f:
            json.dump(self.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)

    def __repr__(self):
        return f'SettingsLoader(config_path="{self.config_path}")'