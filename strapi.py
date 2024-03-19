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


def add_product_in_cart(cart_product_id: int, tg_id: str, strapi_token: str):
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
        requests.post(
            url=f"http://localhost:1337/api/carts",
            headers={"Authorization": f"bearer {strapi_token}"},
            json={
                "data": {
                    "tg_id": tg_id,
                    "cart_products": cart_product_id

                }
            }
        )
