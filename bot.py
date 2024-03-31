import logging
from io import BytesIO

import redis
from email_validate import validate
from environs import Env
from telegram.ext import (
    Updater,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    Filters,
)

from keyboards import (
    display_keyboard_menu,
    display_keyboard_product_description,
    display_keyboard_cart,
)
from strapi import (
    get_name_products,
    get_product_by_id,
    get_products_from_cart,
    add_email,
    get_product_image,
    add_new_user,
    clean_cart,
    add_product_in_cart,
)

logging.basicConfig(format="%(levelname)s::%(message)s", level=logging.ERROR)
logger = logging.getLogger("logger")


def display_menu(update, context, user_reply):
    """Отображает меню магазина."""
    products = get_name_products(headers,strapi_url)
    update.effective_chat.send_message(
        text="Выеберите, что хотите заказать\n\n",
        reply_markup=display_keyboard_menu(products),
    )


def start(update, context, user_reply):
    """Команда запуска бота /start."""
    add_new_user(update.effective_chat.id, headers, carts_redis,strapi_url)
    display_menu(update, context, user_reply)
    return "HANDLE_MENU"


def handle_menu(update, context, user_reply):
    """Меню магазина.

    Если пользователь выбрал кнопку 'В меню' - бот отображает меню.
    Если выбрал кнопку 'Моя корзина' - отображает список товаров в корзине и переводит в состояние 'HANDLE_CART'.
    Если выбрал товар - отображает описание и переводит в состояние 'HANDLE_DESCRIPTION'."""
    if user_reply == "menu":
        display_menu(update, context, user_reply)
    elif user_reply == "my_cart":
        handle_cart(update, context, user_reply)
        return "HANDLE_CART"
    else:
        handle_description_product(update, context, user_reply)
        return "HANDLE_DESCRIPTION"


def handle_description_product(update, context, user_reply):
    """Описание выбранного пользователем продукта из меню.

    Если выбрал товар - отображает описание и переводит в состояние 'HANDLE_DESCRIPTION'.
    Если выбрал кнопку 'Добавить в корзину' - добавляет продукт в корзину в CMS Strapi.
    Если пользователь выбрал кнопку 'В меню' - бот отображает меню.
    Если выбрал кнопку 'Моя корзина' - отображает список товаров в корзине и переводит в состояние 'HANDLE_CART'."""
    if user_reply.startswith("product_"):
        product_id = user_reply.split("_")[-1]

        product = get_product_by_id(product_id, headers,strapi_url)
        product_image = get_product_image(product,strapi_url)

        context.bot.sendPhoto(
            chat_id=update.effective_chat.id,
            photo=BytesIO(product_image),
            caption=product["description"],
            reply_markup=display_keyboard_product_description(product_id),
        )
    elif user_reply.startswith("cart_"):
        product_id = user_reply.split("_")[-1]
        add_product_in_cart(product_id, update.effective_chat.id, headers, carts_redis, strapi_url)
    elif user_reply == "menu":
        handle_menu(update, context, user_reply)
        return "HANDLE_MENU"
    elif user_reply == "my_cart":
        handle_cart(update, context, user_reply)
        return "HANDLE_CART"


def handle_cart(update, context, user_reply):
    """Корзина пользователя с продуктами.

    Если выбрал кнопку 'Моя корзина' - отображает список товаров в корзине и переводит в состояние 'HANDLE_CART'.
    Если пользователь выбрал кнопку 'В меню' - бот отображает меню.
    Если выбрал 'Очистить корзину' - удаляет из корзины пользователя все товары.
    Если выбрал кнопку 'Оплатить' - предлагает ввести email и переводит в состояние 'WAITING_EMAIL'."""
    if user_reply == "my_cart":
        cart = get_products_from_cart(update.effective_chat.id, headers, strapi_url)

        if cart:
            update.effective_chat.send_message(
                f"Ваша корзина:\n\n{cart}", reply_markup=display_keyboard_cart()
            )
        else:
            update.effective_chat.send_message(
                "Ваша корзина пуста", reply_markup=display_keyboard_cart()
            )
    elif user_reply == "menu":
        handle_menu(update, context, user_reply)
        return "HANDLE_MENU"
    elif user_reply == "clean_cart":
        clean_cart(headers, update.effective_chat.id, carts_redis, strapi_url)
    else:
        update.effective_chat.send_message(
            "Введите Вашу электронную почту и мы свяжемся с Вами!"
        )
        return "WAITING_EMAIL"


def handle_email(update, context, user_reply):
    """Проверка электронной почты на валидность.

    Если почта валидна, то пероводит пользователя в состояние 'START'.
    Иначе - просит вновь ввести email."""
    email = update.message.text
    if validate(email):
        cart_id = carts_redis.get(update.effective_chat.id)
        add_email(strapi_token, cart_id, email, strapi_url)
        update.message.reply_text("Спасибо! Скоро с Вами свяжется наш сотрудник!")
        return "START"
    else:
        update.message.reply_text("Введите корректные данные")
        return "WAITING_EMAIL"


def handle_users_reply(update, context):
    """
    Функция, которая запускается при любом сообщении от пользователя и решает как его обработать.
    Эта функция запускается в ответ на эти действия пользователя:
        * Нажатие на inline-кнопку в боте
        * Отправка сообщения боту
        * Отправка команды боту
    Она получает стейт пользователя из базы данных и запускает соответствующую функцию-обработчик (хэндлер).
    Функция-обработчик возвращает следующее состояние, которое записывается в базу данных.
    """

    states = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description_product,
        "HANDLE_CART": handle_cart,
        "WAITING_EMAIL": handle_email,
    }

    chat_id = update.effective_chat.id

    if update.message:
        user_reply = update.message.text

    elif update.callback_query:
        user_reply = update.callback_query.data
    else:
        return

    if user_reply == "/start":
        current_state = "START"
    else:
        current_state = user_state_redis.get(chat_id)

    try:
        next_state = states[current_state](update, context, user_reply)
        user_state_redis.set(chat_id, next_state)
    except Exception as error:
        logger.error(error, exc_info=True)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    strapi_token = env.str("STRAPI_TOKEN")
    strapi_url = env.str("STRAPI_URL")
    bot_token = env.str("TELEGRAM_BOT_TOKEN")

    headers = {"Authorization": f"bearer {strapi_token}"}

    user_state_redis = redis.Redis(
        host=env.str("HOST", "localhost"),
        port=env.int("PORT", 6379),
        db=env.int("USERS_DB", 1),
        password=env.int("USERS_DB_PASSWORD", None),
        decode_responses=True,
    )

    carts_redis = redis.Redis(
        host=env.str("HOST", "localhost"),
        port=env.int("PORT", 6379),
        db=env.int("USERS_DB", 2),
        password=env.int("USERS_DB_PASSWORD", None),
        decode_responses=True,
    )

    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(CommandHandler("start", handle_users_reply))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_users_reply))
    updater.start_polling()
