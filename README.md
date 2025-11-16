# ValutaTrade Hub

## Запуск
1. make project
2. poetry run project

## CLI-команды
1. register --username alice --password 12345 &mdash; регистрация (стартовый баланс 10 000 USD)
2. login --username alice --password 12345 &mdash; Вход
3. buy --currency BTC --amount 0.5 &mdash; покупка за USD
4. sell --currency BTC --amount 0.1 &mdash; продажа за USD
5. show-portfolio --base EUR &mdash; портфель в EUR
6. update-rates --- принудительное обновление курсов
7. show-rates --top 3 --base USD &mdash; топ-3 курсов
8. get-rate --from EUR --to USD &mdash; текущий курс
9. exit &mdash; выход

