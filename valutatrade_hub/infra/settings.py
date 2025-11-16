import json
from pathlib import Path


class SettingsLoader:
    """
    Singleton для загрузки и хранения конфигурации проекта.

    Гарантирует создание директорий и файлов по умолчанию.
    Использует __new__ для единственного экземпляра.
    """

    _instance = None

    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    DATA_PATH = PROJECT_ROOT / 'data'
    USERS_PATH = DATA_PATH / 'users.json'
    PORTFOLIOS_PATH = DATA_PATH / 'portfolios.json'
    RATES_PATH = DATA_PATH / 'rates.json'
    EXCHANGE_RATES_PATH = DATA_PATH / 'exchange_rates.json'

    LOG_DIR = PROJECT_ROOT / 'logs'
    ACTIONS_LOG = LOG_DIR / 'actions.log'

    DEFAULT_CONFIG = {
        'DATA_PATH': str(DATA_PATH),
        'USERS_PATH': str(USERS_PATH),
        'PORTFOLIOS_PATH': str(PORTFOLIOS_PATH),
        'RATES_PATH': str(RATES_PATH),
        'EXCHANGE_RATES_PATH': str(EXCHANGE_RATES_PATH),
        'RATES_TTL_SECONDS': 300,
        "LOG_DIR": str(LOG_DIR),
        "ACTIONS_LOG_PATH": str(ACTIONS_LOG),
        "LOG_FORMAT": "[{time}] {level}: {message}",
        "BASE_CURRENCY": "USD"
    }

    def __new__(cls, config_path=None):
        """Создаёт единственный экземпляр."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, config_path=None):
        """Инициализирует пути, создаёт файлы и загружает конфиг."""
        if getattr(self, '_initialized', False):
            return

        self.config_path = Path(config_path) if config_path else self.PROJECT_ROOT / 'infra' / 'config.json'
        self._ensure_structure()
        self.reload()
        self._initialized = True

    def _ensure_structure(self):
        """Создаёт директории и файлы по умолчанию."""
        self.DATA_PATH.mkdir(parents=True, exist_ok=True)
        self.LOG_DIR.mkdir(parents=True, exist_ok=True)

        for path, default in [
            (self.USERS_PATH, '[]'),
            (self.PORTFOLIOS_PATH, '[]'),
            (self.RATES_PATH, '{"pairs": {}, "last_refresh": null}'),
            (self.EXCHANGE_RATES_PATH, '[]'),
        ]:
            if not path.exists():
                path.write_text(default, encoding='utf-8')

        if not self.ACTIONS_LOG.exists():
            self.ACTIONS_LOG.write_text('', encoding='utf-8')

        if not self.config_path.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.DEFAULT_CONFIG, f, indent=4, ensure_ascii=False)

    def reload(self):
        """Перезагружает конфиг из файла."""
        with open(self.config_path, 'r', encoding='utf-8') as f:
            self._config = json.load(f)

    def get(self, key, default=None):
        """Получает значение из конфига."""
        return self._config.get(key, default)

    def __repr__(self):
        return f'SettingsLoader(config_path="{self.config_path}")'