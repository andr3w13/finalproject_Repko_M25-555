# ValutaTrade Hub

## Запуск
1. make project
2. poetry run project

## CLI-команды
1. register --username alice --password 12345 -- регистрация (стартовый баланс 10 000 USD)
2. login --username alice --password 12345 -- Вход
3. buy --currency BTC --amount 0.5 -- Покупка за USD
4. sell --currency BTC --amount 0.1 -- Продажа за USD
5. show-portfolio --base EUR
6. update-rates -- принудительное обновление курсов
7. show-rates --top 3 --base USD -- топ-3 курсов
8. get-rate --from EUR --to USD -- текущий курс
9. exit -- выход

