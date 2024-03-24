from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def menu_keyboard(products):
    keyboard = [[InlineKeyboardButton(products[product_id], callback_data=f"product_{product_id}")] for
                product_id in
                products] + [[InlineKeyboardButton("Моя корзина", callback_data="my_cart")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def product_description_keyboard(product_id):
    keyboard = [
        [InlineKeyboardButton("В меню", callback_data="menu")],
        [InlineKeyboardButton("Добавить в корзину", callback_data=f"cart_{product_id}")],
        [InlineKeyboardButton("Моя корзина", callback_data="my_cart")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup


def cart_keyboard():
    keyboard = [
        [InlineKeyboardButton("В меню", callback_data="menu")],
        [InlineKeyboardButton("Очистить корзину", callback_data="clean_cart")],
        [InlineKeyboardButton("Оплатить", callback_data="pay")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    return reply_markup
