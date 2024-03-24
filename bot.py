from io import BytesIO

import redis
from email_validate import validate
from environs import Env
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from keyboards import menu_keyboard, product_description_keyboard, cart_keyboard
from strapi import get_name_products, get_product_by_id, download_product_image, get_products_from_cart, add_email, \
    clean_cart, save_product_in_cart_products, add_product_in_cart


def display_menu(update, context):
    products = get_name_products(strapi_token)
    update.effective_chat.send_message(
        "Выберите, что хотите заказать:",
        reply_markup=menu_keyboard(products)
    )


def start(update, context):
    display_menu(update, context)
    return "HANDLE_MENU"


def handle_menu(update, context):
    display_menu(update, context)
    return "HANDLE_DESCRIPTION"


def handle_description_product(update, context):
    product_id = update.callback_query.data.split('_')[-1]

    product = get_product_by_id(product_id, strapi_token)
    product_image = download_product_image(product)

    context.bot.sendPhoto(
        chat_id=update.effective_chat.id,
        photo=BytesIO(product_image),
        caption=product["description"],
        reply_markup=product_description_keyboard(product_id)
    )

    return "HANDLE_MENU"


def handle_cart(update, context):
    cart = get_products_from_cart(update.effective_chat.id, strapi_token)

    print(cart)

    if cart:
        update.effective_chat.send_message(
            f"Ваша корзина:\n\n{cart}",
            reply_markup=cart_keyboard()
        )
    else:
        update.effective_chat.send_message(
            f"Ваша корзина пуста",
            reply_markup=cart_keyboard()
        )
    return "HANDLE_MENU"


def handle_payment(update, context):
    update.effective_chat.send_message("Введите Вашу электронную почту и мы свяжемся с Вами!")
    return "WAITING_EMAIL"


def handle_email(update, context):
    email = update.message.text
    if validate(email):
        cart_id = carts_redis.get(update.effective_chat.id)
        add_email(strapi_token, cart_id, email)
        update.message.reply_text("Спасибо! Скоро с Вами свяжется наш сотрудник!")
        return "HANDLE_MENU"
    else:
        update.message.reply_text("Введите корректные данные")
        return "WAITING_EMAIL"


def handle_users_reply(update, context):
    states = {
        "START": start,
        "HANDLE_MENU": handle_menu,
        "HANDLE_DESCRIPTION": handle_description_product,
        "HANDLE_CART": handle_cart,
        "HANDLE_PAYMENT": handle_payment,
        "WAITING_EMAIL": handle_email
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
    elif user_reply == "menu":
        current_state = "HANDLE_MENU"
    elif user_reply.startswith("product_"):
        current_state = "HANDLE_DESCRIPTION"
    elif user_reply == "my_cart":
        current_state = "HANDLE_CART"
    elif user_reply == "pay":
        current_state = "HANDLE_PAYMENT"
    elif user_reply == "clean_cart":
        clean_cart(strapi_token, update.effective_chat.id, carts_redis)
        current_state = "HANDLE_CART"
    elif user_reply.startswith("cart_"):
        product_id = user_reply.split("_")[-1]
        cart_product_id = save_product_in_cart_products(product_id, strapi_token)
        add_product_in_cart(cart_product_id, update.effective_chat.id, strapi_token, carts_redis)
        current_state = "HANDLE_CART"

    try:
        print(current_state)
        next_state = states[current_state](update, context)
        users_redis.set(chat_id, next_state)
        # print(users_redis.get(chat_id))
        print(carts_redis.get(chat_id))
    except Exception as err:
        print(err)


if __name__ == "__main__":
    env = Env()
    env.read_env()

    users_redis = redis.Redis(
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

    strapi_token = env.str("STRAPI_TOKEN")

    bot_token = env.str("TELEGRAM_BOT_TOKEN")
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(handle_menu))
    dispatcher.add_handler(CallbackQueryHandler(handle_description_product))
    dispatcher.add_handler(CallbackQueryHandler(handle_cart))
    dispatcher.add_handler(CallbackQueryHandler(handle_payment))
    dispatcher.add_handler(MessageHandler(Filters.text, handle_email))
    updater.start_polling()
