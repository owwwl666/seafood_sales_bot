from urllib.parse import urljoin

import requests


def get_name_products(strapi_token: str) -> dict:
    products = requests.get(
        url="http://localhost:1337/api/products",
        headers={"Authorization": f"bearer {strapi_token}"}) \
        .json()["data"]
    return {product["id"]: product["attributes"]["title"] for product in products}


def get_product_by_id(id: str, strapi_token: str) -> dict:
    product = requests.get(
        url=f"http://localhost:1337/api/products/{id}",
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
