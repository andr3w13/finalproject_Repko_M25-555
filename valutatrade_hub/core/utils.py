import json
from valutatrade_hub.core import constants, models
from datetime import datetime, timedelta


def safe_load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
            if isinstance(data, dict):
                data = [data]
        except json.JSONDecodeError:
            data = []
    
    return data


def find_wallet_by_username(username):
    portfolios = safe_load_json(constants.PORTFOLIOS_PATH)
    users = safe_load_json(constants.USERS_PATH)

    for user in users:
        if user['username'] == username:
            user_id = user['user_id']
            break
    
    for portfolio in portfolios:
        if user_id == portfolio['user_id']:
            wallets = portfolio['wallets']
            break
    return wallets, user_id

def process_trade(user, currency, amount, is_buy: bool):
    wallets, user_id = find_wallet_by_username(user)

    rates = safe_load_json(constants.RATES_PATH)

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
        if amount_usd > wallets['USD']['balance']:
            return print('Недостаточно USD.')
        before = wallets[currency]['balance']
        wallets[currency]['balance'] += amount
        wallets['USD']['balance'] -= amount_usd
        print(f'Покупка выполнена: {amount:.4f} {currency} ' +
              f'по курсу {rate:.2f} {currency}/USD')
        s = 'стоимость покупки'
    else:
        if amount > wallets[currency]['balance']:
            print(f'Недостаточно {currency}.')
            return
        before = wallets[currency]['balance']
        wallets[currency]['balance'] -= amount
        wallets['USD']['balance'] += amount_usd
        print(f'Продажа выполнена: {amount:.4f} {currency} ' +
              f'по курсу {rate:.2f} {currency}/USD')
        s = 'выручка'

    print('Измененения в портфеле:')
    print(f'- {currency}: было {before:.4f} → стало {wallets[currency]["balance"]:.4f}')
    print(f'Оценочная {s}: {amount_usd:,.2f} USD')

    new_p = models.Portfolio(user_id, wallets)
    portfolios = safe_load_json(constants.PORTFOLIOS_PATH)
    for p in portfolios:
        if p['user_id'] == user_id:
            p.update(new_p.new_portfolio)
            break

    with open(constants.PORTFOLIOS_PATH, 'w', encoding='utf-8') as f:
        json.dump(portfolios, f, indent=4, ensure_ascii=False)


def check_time(time_str):
    target_dt = datetime.combine(datetime.today(), 
                             datetime.strptime(time_str, "%H:%M:%S").time())
    now = datetime.now()
    diff = now - target_dt

    return timedelta(0) <= diff <= timedelta(minutes=5)


def is_fresh(updated_at_str):
    updated_at = datetime.fromisoformat(updated_at_str.replace('Z', ''))
    return datetime.now() - updated_at < timedelta(minutes=5)


def load_cached_rate(source, to):
    with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pairs = data['pairs']

    direct = f'{source}_{to}'
    reverse = f'{to}_{source}'

    if direct in pairs:
        return {
            'rate': pairs[direct]['rate'],
            'updated_at': pairs[direct]['updated_at']
        }

    if reverse in pairs:
        return {
            'rate': 1 / pairs[reverse]['rate'],
            'updated_at': pairs[reverse]['updated_at']
        }

    return None


def fetch_from_parser(source, to):
    import random

    rate = round(random.uniform(0.1, 5.0), 5)

    now = datetime.now()
    date = now.date().isoformat()
    updated_at = now.time().replace(microsecond=0).isoformat()

    print('Parser Service... получаю свежий курс')

    return rate, date, updated_at



# def update_cache(source, to, rate, updated_at):
#     with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
#         data = json.load(f)

#     pair = f"{source}_{to}"

#     data['pairs'][pair] = {
#         'rate': rate,
#         'updated_at': updated_at
#     }

#     with open(constants.RATES_PATH, 'w', encoding='utf-8') as f:
#         json.dump(data, f, indent=4, ensure_ascii=False)


def get_rate(source, target):
    with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)

    pair_key = f'{source}_{target}'
    reverse_key = f'{target}_{source}'

    if pair_key in data['pairs']:
        pair = data['pairs'][pair_key]
        date, updated_at = pair['updated_at'].split('T')
        updated_at = updated_at.rstrip('Z')

        if is_fresh(pair['updated_at']):
            return pair['rate'], date, updated_at
        else:
            new_rate, date, updated_at = fetch_from_parser(source, target)
            return new_rate, date, updated_at

    if reverse_key in data['pairs']:
        pair = data['pairs'][reverse_key]
        date, updated_at = pair['updated_at'].split('T')
        updated_at = updated_at.rstrip('Z')

        if is_fresh(pair['updated_at']):
            rate = 1 / pair['rate']
            return rate, date, updated_at
        else:
            new_rate, date, updated_at = fetch_from_parser(target, source)
            return 1 / new_rate, date, updated_at

    new_rate, date, updated_at = fetch_from_parser(source, target)
    return new_rate, date, updated_at



