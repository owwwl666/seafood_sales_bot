from io import BytesIO
from urllib.parse import urljoin

import redis
import requests
from environs import Env
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, CallbackQueryHandler


def get_name_products() -> dict:
    products = requests.get(
        url="http://localhost:1337/api/products",
        headers={"Authorization": f"bearer {env.str('STRAPI_TOKEN')}"}) \
        .json()["data"]
    return {product["id"]: product["attributes"]["title"] for product in products}


def get_product_by_id(id: str) -> dict:
    product = requests.get(
        url=f"http://localhost:1337/api/products/{id}",
        headers={"Authorization": f"bearer {env.str('STRAPI_TOKEN')}"},
        params={"populate": "*"}) \
        .json()["data"]["attributes"]
    return product


def download_product_image(product: dict) -> bytes:
    image_url = urljoin(
        "http://localhost:1337",
        product["image"]["data"][0]["attributes"]["url"]
    )
    product_image = requests.get(image_url)
    return product_image.content


def start(update, context):
    product_id_name = get_name_products()
    keyboard = [[InlineKeyboardButton(product_id_name[id], callback_data=f"{id}")] for id in product_id_name]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.message.reply_text(
        "Выберите, что хотите заказать:",
        reply_markup=reply_markup
    )
    return "HANDLE_MENU"


def menu(update, context):
    product_id_name = get_name_products()
    keyboard = [[InlineKeyboardButton(product_id_name[id], callback_data=f"{id}")] for id in product_id_name]

    reply_markup = InlineKeyboardMarkup(keyboard)
    update.effective_chat.send_message(
        text="Выберите, что хотите заказать:",
        reply_markup=reply_markup
    )
    return "HANDLE_MENU"


def display_information_product(update, context):
    product_id = update.callback_query.data

    product = get_product_by_id(product_id)
    product_image = download_product_image(product)

    back = [[InlineKeyboardButton("Назад", callback_data="back")]]

    context.bot.sendPhoto(
        chat_id=update.effective_chat.id,
        photo=BytesIO(product_image),
        caption=product["description"],
        reply_markup=InlineKeyboardMarkup(back)
    )

    return "HANDLE_DESCRIPTION"


def handle_users_reply(update, context):
    states = {
        "START": start,
        "HANDLE_MENU": display_information_product,
        "HANDLE_DESCRIPTION": menu
    }

    if update.message:
        text = update.message.text
        if text == "/start":
            states["START"](update, context)
    if update.callback_query:
        query = update.callback_query.data
        if query.isdigit():
            states["HANDLE_MENU"](update, context)
        elif query == "back":
            states["HANDLE_DESCRIPTION"](update, context)


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

    bot_token = env.str("TELEGRAM_BOT_TOKEN")
    updater = Updater(bot_token)
    dispatcher = updater.dispatcher
    dispatcher.add_handler(CallbackQueryHandler(handle_users_reply))
    dispatcher.add_handler(CommandHandler('start', start))
    dispatcher.add_handler(CallbackQueryHandler(display_information_product))
    dispatcher.add_handler(CallbackQueryHandler(menu))
    updater.start_polling()
