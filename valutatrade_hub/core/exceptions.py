class CurrencyNotFoundError(Exception):
    def __init__(self, code):
        super().__init__(f'Неизвестная валюта "{code}"')


class InsufficientFundsError(Exception):
    def __init__(self, available, code, required):
        super().__init__('Недостаточно средств: ' +
                         f'доступно {available:,.2f} {code}, ' +
                         f'требуется {required:,.2f} {code}')


class ApiRequestError(Exception):
    def __init__(self, reason):
        super().__init__(f'Ошибка при обращении к внешнему API: {reason}')
