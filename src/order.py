import asyncio
import logging
from datetime import datetime
from typing import Optional
from itertools import cycle

logger = logging.getLogger("orders")

# Will be populated on startup
orders: dict[int, dict] = {}
order_counter = 1


async def initialize_demo_orders():
    """Initialize demo orders with real Bolna call IDs from recent executions"""
    global orders, order_counter

    logger.info("[ORDERS] Initializing demo orders...")

    # Fetch recent completed executions from Bolna
    from src import agent
    executions = await agent.get_recent_executions(page_size=10, status="completed")

    # Extract call IDs
    call_ids = []
    for execution in executions:
        call_id = execution.get("id")
        if call_id:
            call_ids.append(call_id)

    logger.info(f"[ORDERS] Found {len(call_ids)} completed call IDs from Bolna")

    # Create a cycle iterator to reuse call IDs if we have fewer than needed
    # If no call IDs, will assign None to all COD orders
    call_id_cycle = cycle(call_ids) if call_ids else cycle([None])

    # Demo data for 7 orders
    demo_orders = [
        {
            "product": {"id": 3, "name": "JBL Flip 6 Speaker", "price": 3499, "category": "Electronics", "image": "https://images.unsplash.com/photo-1608043152269-423dbba4e7e1?w=400"},
            "customer": {"name": "Rahul Sharma", "phone": "9999999999", "city": "Mumbai"},
            "status": "confirmed",
            "payment_mode": "COD"
        },
        {
            "product": {"id": 1, "name": "Nike Air Force 1 White", "price": 7999, "category": "Footwear", "image": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=400"},
            "customer": {"name": "Priya Patel", "phone": "9999999999", "city": "Delhi"},
            "status": "confirmed",
            "payment_mode": "COD"
        },
        {
            "product": {"id": 4, "name": "Mamaearth Skincare Kit", "price": 1199, "category": "Beauty", "image": "https://images.unsplash.com/photo-1556228578-dd6a5aeb2d56?w=400"},
            "customer": {"name": "Amit Kumar", "phone": "9999999999", "city": "Bangalore"},
            "status": "pending",
            "payment_mode": "COD"
        },
        {
            "product": {"id": 2, "name": "Banarasi Silk Saree", "price": 4599, "category": "Fashion", "image": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=400"},
            "customer": {"name": "Sneha Reddy", "phone": "9999999999", "city": "Hyderabad"},
            "status": "cancelled",
            "payment_mode": "COD"
        },
        {
            "product": {"id": 7, "name": "boAt Storm Smart Watch", "price": 2499, "category": "Electronics", "image": "https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=400"},
            "customer": {"name": "Vikram Singh", "phone": "9999999999", "city": "Pune"},
            "status": "confirmed",
            "payment_mode": "CARD"
        },
        {
            "product": {"id": 5, "name": "Adidas Ultraboost 22", "price": 9999, "category": "Footwear", "image": "https://images.unsplash.com/photo-1542291026-7eec264c27ff?w=400"},
            "customer": {"name": "Ananya Gupta", "phone": "9999999999", "city": "Mumbai"},
            "status": "pending",
            "payment_mode": "COD"
        },
        {
            "product": {"id": 6, "name": "Cotton Anarkali Kurti", "price": 899, "category": "Fashion", "image": "https://images.unsplash.com/photo-1583391733975-5ac5b2d0d64e?w=400"},
            "customer": {"name": "Karthik Iyer", "phone": "9999999999", "city": "Chennai"},
            "status": "confirmed",
            "payment_mode": "COD"
        }
    ]

    # Create orders with real call IDs
    for i, demo in enumerate(demo_orders):
        order_id = i + 1
        product = demo["product"]
        customer = demo["customer"]
        status = demo["status"]
        payment_mode = demo["payment_mode"]

        # Assign real call_id from Bolna using cycle iterator for COD orders
        call_id = None
        if payment_mode == "COD":
            call_id = next(call_id_cycle)

        order = {
            "id": order_id,
            "session_id": "default",
            "products": [product],
            "total": product["price"],
            "payment_mode": payment_mode,
            "customer_name": customer["name"],
            "phone": customer["phone"],
            "address": customer["city"],
            "status": status,
            "created_at": datetime.now().isoformat(),
            "call_id": call_id
        }

        if status == "confirmed":
            order["confirmed_at"] = datetime.now().isoformat()
        elif status == "cancelled":
            order["cancelled_at"] = datetime.now().isoformat()

        orders[order_id] = order

    order_counter = 8
    logger.info(f"[ORDERS] Initialized {len(orders)} demo orders (COD orders with real call IDs from Bolna)")
    return True


async def create_order(
    session_id: str,
    cart_items: list,
    total: int,
    payment_mode: str,
    customer_name: str,
    phone: str,
    address: str = ""
) -> dict:
    global order_counter

    order = {
        "id": order_counter,
        "session_id": session_id,
        "products": cart_items,
        "total": total,
        "payment_mode": payment_mode,
        "customer_name": customer_name,
        "phone": phone,
        "address": address,
        "status": "pending" if payment_mode.upper() == "COD" else "confirmed",
        "created_at": datetime.now().isoformat(),
        "call_id": None
    }

    orders[order_counter] = order

    if payment_mode.upper() == "COD":
        from src import agent
        call_result = await agent.trigger_cod_confirmation_call(phone, order["id"], order)
        if call_result.get("status") == "scheduled" and call_result.get("execution_id"):
            order["call_id"] = call_result.get("execution_id")
            orders[order_counter]["call_id"] = call_result.get("execution_id")

    order_counter += 1

    return order


def get_order(order_id: int) -> Optional[dict]:
    return orders.get(order_id)


def get_orders_by_session(session_id: str) -> list:
    return [o for o in orders.values() if o["session_id"] == session_id]


def confirm_order(order_id: int) -> bool:
    """Confirm an order - called by external agent service"""
    if order_id in orders:
        orders[order_id]["status"] = "confirmed"
        orders[order_id]["confirmed_at"] = datetime.now().isoformat()
        return True
    return False


def cancel_order(order_id: int) -> bool:
    """Cancel an order - called by external agent service"""
    if order_id in orders:
        orders[order_id]["status"] = "cancelled"
        orders[order_id]["cancelled_at"] = datetime.now().isoformat()
        return True
    return False
