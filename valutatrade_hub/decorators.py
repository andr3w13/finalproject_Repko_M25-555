import logging
from functools import wraps
from datetime import datetime
from valutatrade_hub.core import constants

logger = logging.getLogger('actions_logger')
if not logger.hasHandlers():
    handler = logging.FileHandler(constants.ACTIONS_LOG_PATH, encoding='utf-8')
    formatter = logging.Formatter('{levelname} {asctime} {message}', style='{', datefmt='%Y-%m-%dT%H:%M:%S')
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


def log_action(action_name, verbose=False):
    """
    Декоратор для логирования доменных действий (BUY/SELL/REGISTER/LOGIN).
    action_name: str — имя действия, например 'BUY' или 'SELL'.
    verbose: bool — если True, добавляет контекст «было→стало».
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            timestamp = datetime.now().isoformat(sep='T', timespec='seconds')
            user = kwargs.get('user') or (args[0] if args else 'unknown')
            currency = kwargs.get('currency_code') or (args[0] if args else 'unknown')
            amount = kwargs.get('amount') or (args[1] if len(args) > 1 else 0)
            rate = kwargs.get('rate', None)
            base = constants.BASE_CURRENCY
            
            try:
                result = func(*args, **kwargs)
                log_line = (
                    f"{action_name} user='{user}' currency='{currency}' amount={amount:.4f} "
                    f"rate={rate if rate is not None else 0:.2f} base='{base}' result=OK"
                )
                logger.info(log_line)
                return result
            except Exception as e:
                log_line = (
                    f"{action_name} user='{user}' currency='{currency}' amount={amount:.4f} "
                    f"rate={rate if rate is not None else 0:.2f} base='{base}' result=ERROR "
                    f"error_type={type(e).__name__} error_message='{e}'"
                )
                logger.info(log_line)
                raise
        return wrapper
    return decorator
