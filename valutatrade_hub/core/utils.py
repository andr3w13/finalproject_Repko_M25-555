import json
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from valutatrade_hub.core import constants
from valutatrade_hub.parser_service.updater import RatesUpdater


def safe_load_json(path: str) -> list:
    """Безопасно загружает JSON → список."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
            elif not isinstance(data, list):
                data = []
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return data


def find_wallet_by_username(username: str) -> tuple[dict, int]:
    """Находит кошельки и ID по имени."""
    portfolios = safe_load_json(constants.PORTFOLIOS_PATH)
    users = safe_load_json(constants.USERS_PATH)

    user_id = None
    for user in users:
        if user.get('username') == username:
            user_id = user['user_id']
            break

    if user_id is None:
        raise ValueError(f"Пользователь '{username}' не найден.")

    for portfolio in portfolios:
        if portfolio.get('user_id') == user_id:
            return portfolio['wallets'], user_id

    raise ValueError(f"Портфель для пользователя ID {user_id} не найден.")


def is_fresh(updated_at_str: str) -> bool:
    """Проверяет свежесть курсов"""
    try:
        dt = datetime.fromisoformat(updated_at_str.replace('Z', '+00:00'))
        now_utc = datetime.now(timezone.utc)
        return now_utc - dt <= timedelta(minutes=5)
    except Exception as e:
        print(f"[DEBUG] is_fresh error: {e}, updated_at: {updated_at_str}")
        return False


def load_cached_rate(source: str, to: str) -> Optional[Dict[str, Any]]:
    """Ищет курс в кэше. Возвращает {'rate', 'updated_at'} или None."""
    try:
        with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

    pairs = data.get('pairs', {})
    key = f'{source.upper()}_{to.upper()}'
    reverse_key = f'{to.upper()}_{source.upper()}'

    if key in pairs:
        return {
            'rate': pairs[key]['rate'],
            'updated_at': pairs[key]['updated_at']
        }
    if reverse_key in pairs:
        return {
            'rate': 1 / pairs[reverse_key]['rate'],
            'updated_at': pairs[reverse_key]['updated_at']
        }
    return None


def fetch_from_parser(source: str, to: str):
    """Запрашивает данные с сервера, если кэш устарел"""
    source, to = source.upper(), to.upper()

    cached = load_cached_rate(source, to)
    if cached and is_fresh(cached['updated_at']):
        rate = cached['rate']
        updated_at = cached['updated_at']
        date = updated_at.split('T')[0]
        print(f"Из кэша (свежий): {source}→{to} = {rate}")
        return rate, date, updated_at

    print("Кэш устарел → обновляю...")
    updater = RatesUpdater()
    updater.run_update()

    cached = load_cached_rate(source, to)
    if not cached:
        return None, None, None

    rate = cached['rate']
    updated_at = cached['updated_at']
    date = updated_at.split('T')[0]
    print(f"Обновлено: {source} → {to} = {rate}")
    return rate, date, updated_at