products: dict[int, dict] = {
    1: {"id": 1, "name": "Wireless Headphones", "price": 1499, "image": "https://picsum.photos/300/200?random=1"},
    2: {"id": 2, "name": "Smart Watch", "price": 2999, "image": "https://picsum.photos/300/200?random=2"},
    3: {"id": 3, "name": "Bluetooth Speaker", "price": 899, "image": "https://picsum.photos/300/200?random=3"},
    4: {"id": 4, "name": "Laptop Stand", "price": 599, "image": "https://picsum.photos/300/200?random=4"},
    5: {"id": 5, "name": "USB-C Hub", "price": 799, "image": "https://picsum.photos/300/200?random=5"},
    6: {"id": 6, "name": "Mechanical Keyboard", "price": 2499, "image": "https://picsum.photos/300/200?random=6"},
}


def get_product(product_id: int) -> dict | None:
    return products.get(product_id)


def get_all_products() -> list[dict]:
    return list(products.values())