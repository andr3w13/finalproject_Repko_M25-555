import shlex
from valutatrade_hub.core import models, constants, utils
from datetime import date
import prompt
import json
import os
import hashlib
from pathlib import Path


def main():
    if not Path.exists(constants.DATA_PATH):
        os.mkdir(constants.DATA_PATH)
        for file_path in (constants.PORTFOLIOS_PATH, 
                          constants.RATES_PATH, 
                          constants.USERS_PATH):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')

    while True:
        user_input = prompt.string('> ')
        args = shlex.split(user_input)
        match args[0]:
            
            case 'register':
                if len(args) != 5:
                    print('Команда введена неправильно.')
                else:
                    if not '--username' in args or not '--password' in args:
                        print('Имя пользователя и/или пароль не были заданы.')
                    else:
                        username = args[args.index('--username') + 1]
                        password = args[args.index('--password') + 1]

                        users = utils.safe_load_json(constants.USERS_PATH)

                        user_already_exists = any(u['username'] == username for u in users)

                        if user_already_exists:
                            print(f'Имя пользователя {username} уже занято.')
                        elif len(password) < 4:
                            print('Пароль должен быть не короче 4 символов.')
                        else:
                            user_id = max((u['user_id'] for u in users), default=0) + 1
                            salt = os.urandom(16).hex()
                            hashed_password = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
                            registration_date = date.today().isoformat()

                            new_user = models.User(user_id, username, hashed_password, salt, registration_date)
                            users.append(new_user.new_user)
                            with open(constants.USERS_PATH, 'w', encoding='utf-8') as f:
                                json.dump(users, f, indent=4, ensure_ascii=False)

                            portfolios = utils.safe_load_json(constants.PORTFOLIOS_PATH)

                            new_portfolio = models.Portfolio(user_id, {})
                            portfolios.append(new_portfolio.new_portfolio)

                            with open(constants.PORTFOLIOS_PATH, 'w', encoding='utf-8') as f:
                                json.dump(portfolios, f, indent=4, ensure_ascii=False)
                            
                            print(f'Пользователь {username} зарегистрирован (id = {user_id}). ' + 
                                f'Войдите: login --username {username} --password ****')
            
            case 'login':
                if len(args) != 5:
                    print('Команда введена неправильно.')
                else:
                    if not '--username' in args or not '--password' in args:
                        print('Имя пользователя и/или пароль не были заданы.')
                    else:
                        username = args[args.index('--username') + 1]
                        password = args[args.index('--password') + 1]

                        users = utils.safe_load_json(constants.USERS_PATH)
                        user_found = False
                        for user in users:
                            if user['username'] == username:
                                hashed_password = user['hashed_password']
                                salt = user['salt']
                                user_found = True
                                break
                        
                        if not user_found:
                            print(f'Пользователь {username} не найден.')
                        else:
                            if hashlib.sha256((password + salt).encode('utf-8')).hexdigest() != hashed_password:
                                print('Неверный пароль.')
                            else:
                                constants.CURRENT_SESSION = username
                                print(f'Вы вошли как {username}')

            case 'show-portfolio':
                if len(args) != 1 and len(args) != 3:
                        print('Команда введена неправильно.')
                else:
                    if not constants.CURRENT_SESSION:
                        print('Сначала выполните login.')
                    else:
                        wallets, user_id = utils.find_wallet_by_username(constants.CURRENT_SESSION)
                        if not wallets:
                            print('У вас пока нет открытых кошельков.')
                        else:
                            base_ind = args.index('--base') + 1 if '--base' in args else None
                            base = args[base_ind].upper() if base_ind else 'USD'

                            with open(constants.RATES_PATH, 'r', encoding='utf-8') as f:
                                rates = json.load(f)
                            
                            pairs = rates['pairs']
                            available_for_convert = base in [pair.split('_')[1] for pair in pairs.keys()]
                            if not available_for_convert:
                                print(f'Неизвестная базовая валюта: {base}.')
                            else:
                                portfolio = models.Portfolio(user_id, wallets)
                                total, details = portfolio.get_total_value(rates, base)
                                if total is None:
                                    print(f'Нет курса для пересчёта в {base}.')

                                print(f'Портфель пользователя "{constants.CURRENT_SESSION}" (база: {base}):')
                                for currency, info in details.items():
                                    print(f'- {currency}: {info["original"]:,.2f} → {info["converted"]:,.2f} {base}')
                                print('-' * 35)
                                print(f'ИТОГО: {total:,.2f} {base}')
     
            case 'buy':
                if not constants.CURRENT_SESSION:
                    print('Сначала выполните login.')
                    continue

                if '--currency' not in args or '--amount' not in args or len(args) != 5:
                    print('Команда введена неправильно.')
                    continue

                currency = args[args.index('--currency') + 1].upper()
                amount = float(args[args.index('--amount') + 1])

                if currency == 'USD':
                    print('Нельзя покупать USD.')
                    continue

                if amount <= 0:
                    print('"amount" должен быть положительным числом.')
                    continue

                utils.process_trade(constants.CURRENT_SESSION, currency, amount, is_buy=True)
                    
            case 'sell':
                if not constants.CURRENT_SESSION:
                    print('Сначала выполните login.')
                    continue

                if '--currency' not in args or '--amount' not in args or len(args) != 5:
                    print('Команда введена неправильно.')
                    continue

                currency = args[args.index('--currency') + 1].upper()
                amount = float(args[args.index('--amount') + 1])

                if currency == 'USD':
                    print('Нельзя продавать USD.')
                    continue

                if amount <= 0:
                    print('"amount" должен быть положительным числом.')
                    continue

                utils.process_trade(constants.CURRENT_SESSION, currency, amount, is_buy=False)
            
            case 'get-rate':
                if len(args) != 5 or '--from' not in args or '--to' not in args:
                    print('Команда введена неправильно.')
                    continue

                source = args[args.index('--from') + 1].upper()
                to = args[args.index('--to') + 1].upper()

                rate, date, updated_at = utils.get_rate(source, to)

                print(f'Курс {source} → {to}: {rate:.8f} (обновлено: {date} {updated_at})')
                print(f'Обратный курс {to} → {source}: {1/rate:.8f}')


            case 'exit':
                break
            case _:
                print('Неизвестная команда.')


if __name__ == '__main__':
    main()