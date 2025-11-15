import json
from valutatrade_hub.core import constants, models, exceptions
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
    prob = random.uniform(0, 1)

    if prob > 0.7:
        # raise exceptions.ApiRequestError
        return None, None, None

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
    



