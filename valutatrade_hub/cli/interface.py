import shlex
from valutatrade_hub.core import models, constants, utils, usecases, exceptions
import prompt
import json
import os
import hashlib
import datetime
from valutatrade_hub.parser_service.updater import RatesUpdater
from valutatrade_hub.parser_service.storage import RatesCache


def main() -> None:
    """
    Основная функция CLI-интерфейса торговой платформы ValutaTrade Hub.

    Реализует интерактивную консольную оболочку для управления пользователями,
    портфелем, курсами валют и обновлением данных из внешних API.
    """
    while True:
        user_input = prompt.string('> ').lower()
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
                            registration_date = datetime.date.today().isoformat()

                            new_user = models.User(user_id, username, hashed_password, salt, registration_date)
                            users.append(new_user.new_user)
                            with open(constants.USERS_PATH, 'w', encoding='utf-8') as f:
                                json.dump(users, f, indent=4, ensure_ascii=False)

                            portfolios = utils.safe_load_json(constants.PORTFOLIOS_PATH)

                            new_portfolio = models.Portfolio(user_id, {'USD': {'balance': 10000.0}})
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
                            base = args[base_ind].upper() if base_ind else constants.BASE_CURRENCY

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

                usecases.buy(currency, amount)
       
            case 'sell':
                if not constants.CURRENT_SESSION:
                    print('Сначала выполните login.')
                    continue

                if '--currency' not in args or '--amount' not in args or len(args) != 5:
                    print('Команда введена неправильно.')
                    continue

                currency = args[args.index('--currency') + 1].upper()
                amount = float(args[args.index('--amount') + 1])

                usecases.sell(currency, amount)

            case 'update-rates':
                if len(args) != 1 and len(args) != 2:
                    print('Команда введена неправильно')
                else:
                    source = args[args.index('--source') + 1] if '--source' in args else None
                    rates_updater = RatesUpdater()
                    try:
                        summary = rates_updater.run_update(source=source)
                        print(f"Обновление завершено. Курсов обновлено: {summary['total_fetched']}")
                        if summary['errors']:
                            print("Ошибки:")
                            for client, err in summary['errors']:
                                print(f"  - {client}: {err}")
                        else:
                            print("Все источники обновлены успешно.")
                    except Exception as e:
                        print(f"Критическая ошибка: {e}")

            case 'get-rate':
                if len(args) != 5 or '--from' not in args or '--to' not in args:
                    print('Команда введена неправильно.')
                    continue

                source = args[args.index('--from') + 1].upper()
                to = args[args.index('--to') + 1].upper()
                
                try:
                    usecases.get_rate(source, to)
                except exceptions.CurrencyNotFoundError as e:
                    print(e)
            
            case 'show-rates':
                cache = RatesCache()
                data = cache.read()
                pairs = data.get('pairs', {})
                last_refresh = data.get('last_refresh', 'неизвестно')

                if not pairs:
                    print("Локальный кэш курсов пуст. Выполните 'update-rates'.")
                    continue

                currency_filter = None
                top_n = None
                base = constants.BASE_CURRENCY

                i = 1
                while i < len(args):
                    if args[i] == '--currency' and i + 1 < len(args):
                        currency_filter = args[i + 1].upper()
                        i += 2
                    elif args[i] == '--top' and i + 1 < len(args):
                        try:
                            top_n = int(args[i + 1])
                            i += 2
                        except ValueError:
                            print("Параметр --top должен быть числом.")
                            continue
                    elif args[i] == '--base' and i + 1 < len(args):
                        base = args[i + 1].upper()
                        i += 2
                    else:
                        i += 1

                filtered = {}
                for key, info in pairs.items():
                    from_curr, to_curr = key.split('_')
                    if currency_filter and from_curr != currency_filter:
                        continue
                    if to_curr != base:
                        continue
                    filtered[key] = info

                if currency_filter and not filtered:
                    print(f"Курс для '{currency_filter}' не найден в кэше.")
                    continue

                if top_n:
                    sorted_items = sorted(
                        filtered.items(),
                        key=lambda x: x[1]['rate'],
                        reverse=True
                    )[:top_n]
                else:
                    sorted_items = sorted(filtered.items(), key=lambda x: x[0])

                print(f"Курсы из кэша (обновлено: {last_refresh}):")
                for key, info in sorted_items:
                    rate = info['rate']
                    updated = info['updated_at'].split('T')[1][:8]
                    source = info.get('source', 'unknown')
                    print(f"- {key}: {rate:,.8f} (↑ {updated}, {source})")

            case 'exit':
                break
            case _:
                print('Неизвестная команда.')


if __name__ == '__main__':
    main()