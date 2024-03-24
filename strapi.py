from urllib.parse import urljoin

import requests


def get_name_products(strapi_token: str) -> dict:
    products = requests.get(
        url="http://localhost:1337/api/products",
        headers={"Authorization": f"bearer {strapi_token}"}) \
        .json()["data"]
    return {product["id"]: product["attributes"]["title"] for product in products}


def get_product_by_id(product_id: str, strapi_token: str) -> dict:
    product = requests.get(
        url=f"http://localhost:1337/api/products/{product_id}",
        headers={"Authorization": f"bearer {strapi_token}"},
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


def save_product_in_cart_products(product_id: str, strapi_token: str) -> int:
    response = requests.post(
        url="http://localhost:1337/api/cart-products",
        headers={"Authorization": f"bearer {strapi_token}"},
        json={
            "data": {
                "product": int(product_id)

            }
        }
    ).json()
    return response["data"]["id"]


def add_product_in_cart(cart_product_id: int, tg_id: str, strapi_token: str, cart_redis):
    user = requests.get(
        url="http://localhost:1337/api/carts",
        headers={"Authorization": f"bearer {strapi_token}"},
        params={"filters[tg_id][$eq]": tg_id}
    ).json()["data"]

    if user:
        user_id = user[0]["id"]
        requests.put(
            url=f"http://localhost:1337/api/carts/{user_id}",
            headers={"Authorization": f"bearer {strapi_token}"},
            json={
                "data": {
                    "cart_products": {"connect": [cart_product_id]}
                }
            }
        )
    else:
        cart = requests.post(
            url="http://localhost:1337/api/carts",
            headers={"Authorization": f"bearer {strapi_token}"},
            json={
                "data": {
                    "tg_id": str(tg_id),
                    "cart_products": cart_product_id

                }
            }
        )
        cart_redis.set(tg_id, cart.json()["data"]["id"])


def get_products_from_cart(tg_id: str, strapi_token: str) -> str | None:
    try:
        response = requests.get(
            url="http://localhost:1337/api/carts",
            headers={"Authorization": f"bearer {strapi_token}"},
            params={"filters[tg_id][$eq]": f"{tg_id}", "populate[cart_products][populate][0]": "product"},
        ).json()

        products = []
        cart = response["data"][0]["attributes"]["cart_products"]["data"]

        for product in cart:
            product_title = product["attributes"]["product"]["data"]["attributes"]["title"]
            products.append(product_title)
        return "\n".join(products)
    except:
        return None


def clean_cart(strapi_token, chat_id, cart_redis):
    cart_id = cart_redis.get(chat_id)

    requests.put(
        url=f"http://localhost:1337/api/carts/{cart_id}",
        headers={"Authorization": f"bearer {strapi_token}"},
        json={
            "data": {
                "cart_products": []
            }
        }
    )


def add_email(strapi_token, cart_id, email):
    requests.put(
        url=f"http://localhost:1337/api/carts/{cart_id}",
        headers={"Authorization": f"bearer {strapi_token}"},
        json={
            "data": {
                "email": email
            }
        }
    )
