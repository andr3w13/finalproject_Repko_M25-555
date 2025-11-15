from valutatrade_hub.core import models, constants, utils, exceptions
import json
from valutatrade_hub import decorators


def process_trade(user, currency, amount, is_buy):
    wallets, user_id = utils.find_wallet_by_username(user)

    with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
        rates = json.load(f)

    pairs = rates['pairs']
    convert_string = f'{currency}_USD'

    if not is_buy:
        if currency not in wallets:
            print(f'У вас нет кошелька "{currency}". ' + 
                  'Добавьте валюту: она создаётся автоматически при первой покупке.')
            return 

        if amount > wallets[currency]['balance']:
            print('Недостаточно средств: ' +
                  f'доступно {wallets[currency]['balance']} {currency}, требуется {amount} {currency}')
            return

    if convert_string not in pairs:
        print(f'Нет курса {currency} → USD.')
        return 

    rate = pairs[convert_string]['rate']
    amount_usd = amount * rate 

    if currency not in wallets:
        portfolio = models.Portfolio(user_id, wallets)
        portfolio.add_currency(currency)
        wallets = portfolio.wallets

    if 'USD' not in wallets:
        return print('Сначала создайте кошелёк в USD.')

    if is_buy:
        try:
            wallet = models.Wallet('USD', wallets['USD']['balance'])
            wallet.withdraw(amount_usd)
        except exceptions.InsufficientFundsError as e:
            raise e
        before = wallets[currency]['balance']
        wallets[currency]['balance'] += amount
        wallets['USD']['balance'] = wallet.balance
        print(f'Покупка выполнена: {amount:.4f} {currency} ' +
              f'по курсу {rate:.2f} {currency}/USD')
        s = 'стоимость покупки'
    else:
        try:
            wallet = models.Wallet(currency, wallets[currency]['balance'])
            wallet.withdraw(amount)      
        except exceptions.InsufficientFundsError as e:
            raise e
        before = wallets[currency]['balance']
        wallets[currency]['balance'] = wallet.balance
        wallets['USD']['balance'] += amount_usd
        print(f'Продажа выполнена: {amount:.4f} {currency} ' +
              f'по курсу {rate:.2f} {currency}/USD')
        s = 'выручка'

    print('Измененения в портфеле:')
    print(f'- {currency}: было {before:.4f} → стало {wallets[currency]["balance"]:.4f}')
    print(f'Оценочная {s}: {amount_usd:,.2f} USD')

    new_p = models.Portfolio(user_id, wallets)
    portfolios = utils.safe_load_json(constants.PORTFOLIOS_PATH)
    for p in portfolios:
        if p['user_id'] == user_id:
            p.update(new_p.new_portfolio)
            break

    with open(constants.PORTFOLIOS_PATH, 'w', encoding='utf-8') as f:
        json.dump(portfolios, f, indent=4, ensure_ascii=False)


@decorators.log_action('BUY_CURRENCY')
def buy(currency_code, amount):
    if currency_code == 'USD':
        print('Нельзя покупать USD.')
        return

    if amount <= 0:
        print('"amount" должен быть положительным числом.')
        return
    try:
        process_trade(constants.CURRENT_SESSION, currency_code, amount, is_buy=True)
    except exceptions.InsufficientFundsError as e:
        print(e)


@decorators.log_action('SELL_CURRENCY')
def sell(currency_code, amount):
    if currency_code == 'USD':
        print('Нельзя продавать USD.')
        return

    if amount <= 0:
        print('"amount" должен быть положительным числом.')
        return

    try:
        process_trade(constants.CURRENT_SESSION, currency_code, amount, is_buy=False)
    except exceptions.InsufficientFundsError as e:
        print(e)


def get_rate(from_code, to_code):
    with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pair_key = f'{from_code}_{to_code}'
    reverse_key = f'{to_code}_{from_code}'

    if pair_key in data['pairs']:
        pair = data['pairs'][pair_key]
        date, updated_at = pair['updated_at'].split('T')
        updated_at = updated_at.rstrip('Z')

        if utils.is_fresh(pair['updated_at']):
            rate = pair['rate']
        else:
            new_rate, date, updated_at = utils.fetch_from_parser(from_code, to_code)
            if new_rate is None:
                raise exceptions.CurrencyNotFoundError(pair_key)
    elif reverse_key in data['pairs']:
        pair = data['pairs'][reverse_key]
        date, updated_at = pair['updated_at'].split('T')
        updated_at = updated_at.rstrip('Z')

        if utils.is_fresh(pair['updated_at']):
            rate = 1 / pair['rate']
        else:
            new_rate, date, updated_at = utils.fetch_from_parser(to_code, from_code)
            if new_rate is None:
                raise exceptions.CurrencyNotFoundError(pair_key)
            new_rate = 1 / new_rate
    else:
        new_rate, date, updated_at = utils.fetch_from_parser(from_code, to_code)
        if new_rate is None:
            raise exceptions.CurrencyNotFoundError(pair_key)

    print(f'Курс {from_code} → {to_code}: {rate:.8f} (обновлено: {date} {updated_at})')
    print(f'Обратный курс {to_code} → {from_code}: {1/rate:.8f}')