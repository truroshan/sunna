import asyncio
from datetime import datetime
from typing import Optional

orders: dict[int, dict] = {}
order_counter = 1


def create_order(
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
        "created_at": datetime.now().isoformat()
    }
    
    orders[order_counter] = order
    
    if payment_mode.upper() == "COD":
        from src import agent
        asyncio.create_task(agent.trigger_cod_confirmation_call(phone, order["id"], order))
    
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
