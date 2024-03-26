from urllib.parse import urljoin

import requests


def get_name_products(headers: dict) -> dict:
    """Возвращает dict с ключом - id продукта и значением - название продукта."""
    products = requests.get(
        url="http://localhost:1337/api/products", headers=headers
    ).json()["data"]
    return {product["id"]: product["attributes"]["title"] for product in products}


def get_product_by_id(product_id: str, headers: dict) -> dict:
    """Получает продукт по его id в БД Strapi."""
    product = requests.get(
        url=f"http://localhost:1337/api/products/{product_id}",
        headers=headers,
        params={"populate": "*"},
    ).json()["data"]["attributes"]
    return product


def get_product_image(product: dict) -> bytes:
    """Получает изображение продукта по его url."""
    image_url = urljoin(
        "http://localhost:1337", product["image"]["data"][0]["attributes"]["url"]
    )
    product_image = requests.get(image_url)
    return product_image.content


def add_new_user(tg_id: str, headers: dict, cart_redis):
    """Добавляет нового пользователя в хранилище Cart."""
    if cart_redis.get(tg_id) is None:
        response = requests.post(
            url="http://localhost:1337/api/carts",
            headers=headers,
            json={"data": {"tg_id": str(tg_id)}},
        )
        cart_redis.set(tg_id, response.json()["data"]["id"])


def add_product_in_cart(product_id: str, tg_id: str, headers: dict, cart_redis):
    """Добавляет продукт в корзину пользователя."""
    cart_id = cart_redis.get(tg_id)

    cart_product_id = requests.post(
        url="http://localhost:1337/api/cart-products",
        headers=headers,
        json={"data": {"product": int(product_id)}},
    ).json()["data"]["id"]

    requests.put(
        url=f"http://localhost:1337/api/carts/{cart_id}",
        headers=headers,
        json={"data": {"cart_products": {"connect": [cart_product_id]}}},
    )


def get_products_from_cart(tg_id: str, headers: dict) -> str | None:
    """Получает все продукты из корзины пользователя."""
    response = requests.get(
        url="http://localhost:1337/api/carts",
        headers=headers,
        params={
            "filters[tg_id][$eq]": f"{tg_id}",
            "populate[cart_products][populate][0]": "product",
        },
    ).json()

    products = []
    cart = response["data"][0]["attributes"]["cart_products"]["data"]

    for product in cart:
        product_title = product["attributes"]["product"]["data"]["attributes"]["title"]
        products.append(product_title)
    return "\n".join(products)


def clean_cart(headers: dict, chat_id, cart_redis):
    """Очищает корзину пользователя."""
    cart_id = cart_redis.get(chat_id)

    requests.put(
        url=f"http://localhost:1337/api/carts/{cart_id}",
        headers=headers,
        json={"data": {"cart_products": []}},
    )


def add_email(strapi_token, cart_id, email):
    """Добавляет в БД, введенный пользователем email."""
    requests.put(
        url=f"http://localhost:1337/api/carts/{cart_id}",
        headers={"Authorization": f"bearer {strapi_token}"},
        json={"data": {"email": email}},
    )
