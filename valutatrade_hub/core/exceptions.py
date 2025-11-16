class CurrencyNotFoundError(Exception):
    """Вызывается, если валюта с указанным кодом не найдена в системе."""
    def __init__(self, code: str):
        super().__init__(f'Неизвестная валюта "{code}"')


class InsufficientFundsError(Exception):
    """Вызывается при попытке снять больше средств, чем есть на кошельке."""
    def __init__(self, available: float, code: str, required: float):
        super().__init__('Недостаточно средств: ' +
                         f'доступно {available:,.2f} {code}, ' +
                         f'требуется {required:,.2f} {code}')


class ApiRequestError(Exception):
    """Вызывается при ошибке обращения к внешнему API (сеть, статус, парсинг)."""
    def __init__(self, reason: str):
        super().__init__(f'Ошибка при обращении к внешнему API: {reason}')