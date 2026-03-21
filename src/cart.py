from typing import Dict

carts: Dict[str, list] = {}


def get_cart(session_id: str) -> list:
    if session_id not in carts:
        carts[session_id] = []
    return carts[session_id]


def add_to_cart(session_id: str, product_id: int) -> bool:
    from src import products
    product = products.get_product(product_id)
    if product:
        cart = get_cart(session_id)
        cart.append(product)
        return True
    return False


def remove_from_cart(session_id: str, index: int) -> bool:
    cart = get_cart(session_id)
    if 0 <= index < len(cart):
        cart.pop(index)
        return True
    return False


def clear_cart(session_id: str):
    carts[session_id] = []


def get_cart_total(session_id: str) -> int:
    cart = get_cart(session_id)
    return sum(item["price"] for item in cart)