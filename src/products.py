products: dict[int, dict] = {
    1: {
        "id": 1,
        "name": "Nike Air Force 1 White",
        "price": 7999,
        "category": "Footwear",
        "image": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400&h=300&fit=crop"
    },
    2: {
        "id": 2,
        "name": "Banarasi Silk Saree",
        "price": 4599,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400&h=300&fit=crop"
    },
    3: {
        "id": 3,
        "name": "JBL Flip 6 Speaker",
        "price": 3499,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400&h=300&fit=crop"
    },
    4: {
        "id": 4,
        "name": "Mamaearth Skincare Kit",
        "price": 1199,
        "category": "Beauty",
        "image": "https://images.unsplash.com/photo-1596755389378-c31d21fd1273?w=400&h=300&fit=crop"
    },
    5: {
        "id": 5,
        "name": "Adidas Ultraboost 22",
        "price": 9999,
        "category": "Footwear",
        "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400&h=300&fit=crop"
    },
    6: {
        "id": 6,
        "name": "Cotton Anarkali Kurti",
        "price": 899,
        "category": "Fashion",
        "image": "https://images.unsplash.com/photo-1617127365659-c47fa864d8bc?w=400&h=300&fit=crop"
    },
    7: {
        "id": 7,
        "name": "boAt Storm Smart Watch",
        "price": 2499,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400&h=300&fit=crop"
    },
    8: {
        "id": 8,
        "name": "Fire-Boltt Ninja Pro",
        "price": 1799,
        "category": "Electronics",
        "image": "https://images.unsplash.com/photo-1579586337278-3befd40fd17a?w=400&h=300&fit=crop"
    },
}


def get_product(product_id: int) -> dict | None:
    return products.get(product_id)


def get_all_products() -> list[dict]:
    return list(products.values())