# Описание
Демо-Бот по продаже морепродуктов в телеграм. Телеграм бот интегрируется с CMS [Strapi](https://strapi.io/) с помощью их API, в которой предварительно создано хранилище с товарами.

## Скачивание проекта

Скачайте проект на свою локальную машину:

```sh
git clone git@github.com:owwwl666/seafood_sales_bot.git
```

## Установка зависимостей

Введите команду для установки необходимых пакетов:

```sh
pip install -r requirements.txt
```

## Переменные окружения

```
STRAPI_TOKEN=<API STRAPI>
TELEGRAM_BOT_TOKEN=<API TOKEN TELEGRAM BOT'S>
```

## CMS

- [Инструкция](https://docs.strapi.io/dev-docs/installation/cli) по установке и запуску Strapi.

- Используются 3 модели для хранения данных:
  - `Product` - модель с товарами(продуктами) магазина.
  - `Cart` - модель корзины для каждого пользователя, пришедшего в бот.
  - `CartProdcut` - промужеточная модель между Cart и Product, в которой хранятся id товара и его количество для заказа.

- Поля модели `Product`
  - title (Text)
  - description (Text)
  - price (Number)
  - image (Media)
 
- Поля модели `CartProduct`
  - product (Relation - **CartProduct has one Product**)
  - weight (Number - **Decimal**)
 
- Поля модели `Cart`
  - tg_id - (Text - telegram id user's)
  - cart_products - (Relation - **Cart has many CartProducts**)
  - email - (Email)


## Запуск бота

Введите команду

```sh
python bot.py
```

# Результат


<img src="https://github.com/owwwl666/seafood_sales_bot/assets/131767856/7feb6df7-60be-41cb-94d3-f2ead04f9057" width="400" height="650">

