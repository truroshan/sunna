"""
Agent call module - Uses Bolna API for COD confirmation calls.
"""

import os
import asyncio
import logging
from datetime import datetime, timedelta
from dateutil import tz

import httpx

logger = logging.getLogger("bolna")

BOLNA_API_KEY = os.getenv("BOLNA_API_KEY")
BOLNA_AGENT_ID = os.getenv("BOLNA_AGENT_ID", "")
BOLNA_DELIVERY_AGENT_ID = os.getenv("BOLNA_DELIVERY_AGENT_ID", "")
BASE = "https://api.bolna.ai"

async def trigger_cod_confirmation_call(phone: str, order_id: int, order_details: dict = None):
    """
    Trigger a call to the customer for COD order confirmation via Bolna API.
    """
    logger.info(f"[BOLNA CALL] Scheduling call to {phone} for order #{order_id}")

    if not BOLNA_API_KEY or not BOLNA_AGENT_ID:
        logger.warning("[BOLNA] API key or Agent ID not configured")
        return {"status": "not_configured", "phone": phone, "order_id": order_id}

    # Build context
    products = order_details.get("products", []) if order_details else []
    product_name = products[0]["name"] if products else "your item"

    ist = tz.gettz("Asia/Kolkata")
    ist_time = datetime.now(ist) + timedelta(seconds=10)
    scheduled_at = ist_time.isoformat()
        

    context = {
        "order_id": str(order_id),
        "customer_name": (order_details.get("customer_name", "Customer") if order_details else "Customer").strip().title(),
        "product_name": product_name,
        "amount": f"{int(order_details.get('total', 0)):,}" if order_details else "0",
        "city": order_details.get("address", "Mumbai") if order_details else "Mumbai",
    }

    try:
        # Pass user_data with dynamic variables - Bolna will substitute them in the agent prompt
        payload = {
            "agent_id": BOLNA_AGENT_ID,
            "recipient_phone_number": f"+91{phone}" if not phone.startswith("+") else phone,
            "user_data": context,
            "scheduled_at": scheduled_at,
        }

        logger.info(f"[BOLNA] Triggering call to {phone} | order={order_id} customer={context.get('customer_name')} product={product_name}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE}/call",
                json=payload,
                headers={"Authorization": f"Bearer {BOLNA_API_KEY}"},
                timeout=15,
            )
            logger.info(f"[BOLNA] Trigger response {response.status_code}: {response.text[:300]}")

            if response.status_code == 200:
                result = response.json()
                call_id = result.get("execution_id") or result.get("run_id") or result.get("call_id") or ""
                logger.info(f"[BOLNA] Call queued — call_id={call_id}")
                return {"status": "scheduled", "execution_id": call_id, "phone": phone, "order_id": order_id}
            else:
                logger.error(f"[BOLNA] Error: {response.status_code} - {response.text}")
                return {"status": "failed", "error": response.text}

    except Exception as e:
        logger.error(f"[BOLNA] Exception: {e}")
        return {"status": "error", "error": str(e)}


async def get_call_status(call_id: str) -> dict:
    """Fetch execution details from Bolna API using execution_id"""
    if not BOLNA_API_KEY:
        logger.warning("[BOLNA] API key not configured")
        return {}

    try:
        async with httpx.AsyncClient() as client:
            # Correct endpoint: /executions/{execution_id}
            r = await client.get(
                f"{BASE}/executions/{call_id}",
                headers={"Authorization": f"Bearer {BOLNA_API_KEY}"},
                timeout=10,
            )

            if r.status_code == 200:
                data = r.json()
                logger.info(f"[BOLNA] Fetched execution {call_id[:8]}... — status: {data.get('status')}")
                return data
            else:
                logger.error(f"[BOLNA] Failed to fetch execution {call_id[:8]}...: {r.status_code} - {r.text[:200]}")
                return {}

    except Exception as e:
        logger.error(f"[BOLNA] Exception fetching execution {call_id[:8]}...: {e}")
        return {}


async def get_recent_executions(page_size: int = 10, status: str = "completed") -> list:
    """Fetch recent completed call executions from Bolna API"""
    if not BOLNA_API_KEY or not BOLNA_AGENT_ID:
        logger.warning("[BOLNA] API key or Agent ID not configured")
        return []

    try:
        async with httpx.AsyncClient() as client:
            # Correct Bolna API endpoint for fetching executions
            r = await client.get(
                f"{BASE}/v2/agent/{BOLNA_AGENT_ID}/executions",
                headers={"Authorization": f"Bearer {BOLNA_API_KEY}"},
                params={"page_size": page_size, "page_number": 1, "status": status},
                timeout=15,
            )
            if r.status_code == 200:
                data = r.json()
                # Response format: {"data": [...], "page_number": 123, "page_size": 123, "total": 123, "has_more": true}
                executions = data.get("data", [])
                logger.info(f"[BOLNA] Fetched {len(executions)} {status} executions")
                return executions
            else:
                logger.warning(f"[BOLNA] Failed to fetch executions: {r.status_code} - {r.text[:200]}")
                return []
    except Exception as e:
        logger.error(f"[BOLNA] Exception fetching executions: {e}")
        return []


async def trigger_delivery_call(phone: str, order_id: int, order_details: dict = None):
    """
    Trigger a delivery notification call to the customer via Bolna API.
    """
    logger.info(f"[BOLNA DELIVERY] Scheduling delivery call to {phone} for order #{order_id}")

    if not BOLNA_API_KEY or not BOLNA_DELIVERY_AGENT_ID:
        logger.warning("[BOLNA] API key or Delivery Agent ID not configured")
        return {"status": "not_configured", "phone": phone, "order_id": order_id}

    # Build context
    products = order_details.get("products", []) if order_details else []
    product_name = products[0]["name"] if products else "your item"

    ist = tz.gettz("Asia/Kolkata")
    ist_time = datetime.now(ist) + timedelta(seconds=10)
    scheduled_at = ist_time.isoformat()

    context = {
        "order_id": str(order_id),
        "customer_name": (order_details.get("customer_name", "Customer") if order_details else "Customer").strip().title(),
        "product_name": product_name,
        "amount": f"{int(order_details.get('total', 0)):,}" if order_details else "0",
        "city": order_details.get("address", "Mumbai") if order_details else "Mumbai",
    }

    try:
        # Pass user_data with dynamic variables - Bolna will substitute them in the agent prompt
        payload = {
            "agent_id": BOLNA_DELIVERY_AGENT_ID,
            "recipient_phone_number": f"+91{phone}" if not phone.startswith("+") else phone,
            "user_data": context,
            "scheduled_at": scheduled_at,
        }

        logger.info(f"[BOLNA DELIVERY] Triggering call to {phone} | order={order_id} customer={context.get('customer_name')} product={product_name}")

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{BASE}/call",
                json=payload,
                headers={"Authorization": f"Bearer {BOLNA_API_KEY}"},
                timeout=15,
            )
            logger.info(f"[BOLNA DELIVERY] Trigger response {response.status_code}: {response.text[:300]}")

            if response.status_code == 200:
                result = response.json()
                call_id = result.get("execution_id") or result.get("run_id") or result.get("call_id") or ""
                logger.info(f"[BOLNA DELIVERY] Call queued — call_id={call_id}")
                return {"status": "scheduled", "execution_id": call_id, "phone": phone, "order_id": order_id}
            else:
                logger.error(f"[BOLNA DELIVERY] Error: {response.status_code} - {response.text}")
                return {"status": "failed", "error": response.text}

    except Exception as e:
        logger.error(f"[BOLNA DELIVERY] Exception: {e}")
        return {"status": "error", "error": str(e)}
