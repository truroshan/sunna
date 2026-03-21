"""
Agent call module - Uses Bolna API for COD confirmation calls.
"""

import os
from datetime import datetime, timedelta

from dateutil import tz
import httpx


BOLNA_API_URL = "https://api.bolna.ai/call"
BOLNA_API_KEY = os.environ["BOLNA_API_KEY"]
BOLNA_AGENT_ID = os.environ["BOLNA_AGENT_ID"]


async def trigger_cod_confirmation_call(phone: str, order_id: int, order_details: dict = None):
    """
    Trigger a call to the customer for COD order confirmation via Bolna API.
    """
    print(f"[BOLNA CALL] Scheduling call to {phone} for order #{order_id}")
    
    if not BOLNA_API_KEY or not BOLNA_AGENT_ID:
        print("[BOLNA] API key or Agent ID not configured")
        return {"status": "not_configured", "phone": phone, "order_id": order_id}
        
    ist = tz.gettz("Asia/Kolkata")
    ist_time = datetime.now(ist) + timedelta(seconds=10)
    scheduled_at = ist_time.isoformat()
        
    user_data = {
        "order_id": order_id,
        "customer_name": order_details.get("customer_name", "Customer") if order_details else "Customer",
        "total_items_count": len(order_details.get("products", [])) if order_details else 0,
        "total_amount": order_details.get("total", 0) if order_details else 0,
    }
    
    payload = {
        "agent_id": BOLNA_AGENT_ID,
        "recipient_phone_number": f"+91{phone}" if not phone.startswith("+") else phone,
        "scheduled_at": scheduled_at,
        "user_data": user_data
    }

    headers = {
        "Authorization": f"Bearer {BOLNA_API_KEY}",
        "Content-Type": "application/json"
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(BOLNA_API_URL, json=payload, headers=headers, timeout=30)
            if response.status_code == 200:
                result = response.json()
                print(f"[BOLNA] Call scheduled: {result.get('execution_id')} at {scheduled_at}")
                return {"status": "scheduled", "execution_id": result.get("execution_id"), "phone": phone, "order_id": order_id}
            else:
                print(f"[BOLNA] Error: {response.status_code} - {response.text}")
                return {"status": "failed", "error": response.text}
    except Exception as e:
        print(f"[BOLNA] Exception: {e}")
        return {"status": "error", "error": str(e)}
