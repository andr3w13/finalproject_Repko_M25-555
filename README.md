# ValutaTrade Hub

**ValutaTrade Hub** — консольный симулятор торговли криптовалютами и фиатом с **реальными курсами** из CoinGecko и ExchangeRate-API.  
Поддерживает регистрацию, покупку/продажу, портфель, кэш курсов и логирование.

## Структура каталогов
finalproject_Repko_M25-555/ \
│  \
├── data/ \
│    ├── users.json \         
│    ├── portfolios.json \       
│    ├── rates.json \          
│    └── exchange_rates.json \                 
├── valutatrade_hub/ \
│    ├── __init__.py \
│    ├── logging_config.py  \       
│    ├── decorators.py      \      
│    ├── core/ \
│    │    ├── __init__.py \
│    │    ├── currencies.py \        
│    │    ├── exceptions.py   \      
│    │    ├── models.py         \  
│    │    ├── usecases.py \
│    │    ├── constants.py \
│    │    └── utils.py      \      
│    ├── infra/ \
│    │    ├── __init__.py \
│    │    ├── config.json \
│    │    └── settings.py \                 
│    ├── parser_service/ \
│    │    ├── __init__.py \
│    │    ├── config.py     \        
│    │    ├── api_clients.py  \      
│    │    ├── updater.py       \     
│    │    └── storage.py       \               
│    └── cli/ \
│         ├─ __init__.py \
│         └─ interface.py  \   
│ \
├── main.py \
├── Makefile \
├── poetry.lock \
├── pyproject.toml \
├── README.md \
└── .gitignore \             

## Установка
1. make install
2. poetry install

## Запуск
1. make project
2. poetry run project

## CLI-команды
1. register --username alice --password 12345 &mdash; регистрация (стартовый баланс 10 000 USD)
2. login --username alice --password 12345 &mdash; вход
3. buy --currency BTC --amount 0.5 &mdash; покупка за USD
4. sell --currency BTC --amount 0.1 &mdash; продажа за USD
5. show-portfolio --base EUR &mdash; портфель в EUR
6. update-rates --- принудительное обновление курсов
7. show-rates --top 3 --base USD &mdash; топ-3 курсов
8. get-rate --from EUR --to USD &mdash; текущий курс
9. exit &mdash; выход

## Кэш и TTL
rates.json — кэш актуальных курсов
* TTL: 5 минут
* Поле updated_at: 2025-11-16T18:07:07Z
* Автоматическое обновление при get-rate, buy, sell

exchange_rates.json — полная история (по записям)

* Курс берётся из кэша, если не старше 5 минут.
* Иначе — запускается RatesUpdater.

## Parser Service
1. Включение:
    * Сервис автоматически включается при:
        + update-rates
        + get-rate (если курс устарел)
        + buy / sell (если нет курса)
2. Источники:
    * CoinGecko
    * ExchangeRate-API
3. API-ключ:
    * Получите ключ на exchangerate-api.com
    * Создайте .env в корне:
        + EXCHANGERATE_API_KEY=your_api_key_here