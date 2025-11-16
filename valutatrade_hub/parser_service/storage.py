import json
import os
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any
from valutatrade_hub.core import exceptions, utils, constants
from valutatrade_hub.parser_service.config import ParserConfig

cfg = ParserConfig()


def _now_iso() -> str:
    """Возвращает текущее время в UTC (ISO + Z)."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat() + 'Z'


def _atomic_write(path: Path, data: Any) -> None:
    """Атомарно записывает JSON в файл через .tmp."""
    tmp = path.with_suffix('.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


class ExchangeRatesRepo:
    """Репозиторий истории курсов (exchange_rates.json → список записей)."""

    def __init__(self, path: str = cfg.HISTORY_FILE_PATH):
        """Инициализирует путь и создаёт пустой файл при отсутствии."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            self.path.write_text('[]', encoding='utf-8')

    @staticmethod
    def _validate_code(code: str) -> None:
        """Проверяет код валюты: 2–5 букв, только латиница."""
        if not (isinstance(code, str) and code.isalpha() and 2 <= len(code) <= 5):
            raise exceptions.ApiRequestError(f'Invalid currency code: {code}')

    def save_measurement(
        self,
        from_currency: str,
        to_currency: str,
        rate: float,
        source: str,
        meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Сохраняет одну запись курса в историю.
        Возвращает созданную запись.
        """
        from_code = from_currency.upper()
        to_code = to_currency.upper()

        self._validate_code(from_code)
        self._validate_code(to_code)

        if not isinstance(rate, (int, float)):
            raise exceptions.ApiRequestError('Rate must be numeric')

        timestamp = _now_iso()
        uid = f'{from_code}_{to_code}_{timestamp}'

        entry = {
            'id': uid,
            'from_currency': from_code,
            'to_currency': to_code,
            'rate': float(rate),
            'timestamp': timestamp,
            'source': source,
            'meta': meta or {}
        }

        try:
            history = utils.safe_load_json(constants.EXCHANGE_RATES_PATH)
        except Exception as e:
            raise exceptions.ApiRequestError(f'Failed to read history file: {e}')

        if any(item.get('id') == uid for item in history):
            return entry  

        history.append(entry)

        try:
            _atomic_write(self.path, history)
        except Exception as e:
            raise exceptions.ApiRequestError(f'Failed to write history file: {e}')

        return entry


class RatesCache:
    """Кэш актуальных курсов (rates.json → snapshot)."""

    def __init__(self, path: str = cfg.RATES_FILE_PATH):
        """Инициализирует путь и создаёт начальный файл при отсутствии."""
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if not self.path.exists():
            initial = {'pairs': {}, 'last_refresh': None}
            self.path.write_text(json.dumps(initial, ensure_ascii=False, indent=2), encoding='utf-8')

    def read(self) -> Dict[str, Any]:
        """Читает кэш. Возвращает пустой при ошибке JSON."""
        try:
            with self.path.open('r', encoding='utf-8') as f:
                return json.load(f)
        except json.JSONDecodeError:
            return {'pairs': {}, 'last_refresh': None}

    def write(self, pairs: Dict[str, Dict[str, Any]], last_refresh: str) -> None:
        """Записывает в rates.json с правильной структурой."""
        if not pairs:
            raise ValueError("pairs cannot be empty")
        if not last_refresh:
            raise ValueError("last_refresh required")

        payload = {"pairs": pairs, "last_refresh": last_refresh}
        try:
            _atomic_write(self.path, payload)
        except Exception as e:
            raise exceptions.ApiRequestError(f'Cache write error: {e}')