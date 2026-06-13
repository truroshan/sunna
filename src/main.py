import os
import json
import logging
import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src import products, cart, order

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("byteio")

app = FastAPI(title="ByteIO - Shop", description="ByteIO - Shop")
templates = Jinja2Templates(directory="templates")


@app.on_event("startup")
async def startup_event():
    """Initialize demo orders on startup"""
    logger.info("[STARTUP] Initializing application...")
    await order.initialize_demo_orders()
    logger.info("[STARTUP] Application ready!")


@app.get("/", response_class=HTMLResponse)
async def home():
    return RedirectResponse(url="/products")


@app.get("/products", response_class=HTMLResponse)
async def list_products(request: Request):
    session_id = request.cookies.get("session_id", "default")
    cart_items = cart.get_cart(session_id)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "products": products.get_all_products(),
        "cart_count": len(cart_items)
    })


@app.post("/cart/add")
async def add_to_cart(request: Request):
    session_id = request.cookies.get("session_id", "default")
    form = await request.form()
    product_id = int(form.get("product_id"))
    cart.add_to_cart(session_id, product_id)
    return JSONResponse({"success": True, "cart_count": len(cart.get_cart(session_id))})


@app.get("/cart", response_class=HTMLResponse)
async def view_cart(request: Request):
    session_id = request.cookies.get("session_id", "default")
    cart_items = cart.get_cart(session_id)
    total = cart.get_cart_total(session_id)
    return templates.TemplateResponse("cart.html", {
        "request": request,
        "cart_items": cart_items,
        "total": total
    })


@app.post("/cart/remove", response_class=HTMLResponse)
async def remove_from_cart(request: Request):
    session_id = request.cookies.get("session_id", "default")
    form = await request.form()
    index = int(form.get("index"))
    cart.remove_from_cart(session_id, index)
    return RedirectResponse(url="/cart", status_code=303)


@app.post("/checkout", response_class=HTMLResponse)
async def checkout(request: Request):
    session_id = request.cookies.get("session_id", "default")
    form = await request.form()

    customer_name = form.get("customer_name")
    phone = form.get("phone")
    payment_mode = form.get("payment_mode")

    cart_items = cart.get_cart(session_id)
    total = cart.get_cart_total(session_id)

    if not cart_items:
        return RedirectResponse(url="/cart", status_code=303)

    ord = await order.create_order(
        session_id=session_id,
        cart_items=cart_items,
        total=total,
        payment_mode=payment_mode,
        customer_name=customer_name,
        phone=phone
    )

    cart.clear_cart(session_id)

    return templates.TemplateResponse("success.html", {
        "request": request,
        "order": ord
    })


@app.get("/orders", response_class=HTMLResponse)
async def list_orders(request: Request):
    session_id = request.cookies.get("session_id", "default")
    user_orders = order.get_orders_by_session(session_id)
    return templates.TemplateResponse("orders.html", {
        "request": request,
        "orders": user_orders
    })


@app.post("/api/orders/confirm")
async def confirm_order(request: Request):
    """External API to confirm an order (called by agent service)"""
    body = await request.json()
    order_id = body.get("order_id")
    
    if not order_id:
        return JSONResponse({"success": False, "message": "order_id required"}, status_code=400)
    
    success = order.confirm_order(int(order_id))
    if success:
        return JSONResponse({"success": True, "message": "Order confirmed", "order_id": order_id})
    return JSONResponse({"success": False, "message": "Order not found"}, status_code=404)


@app.post("/api/orders/cancel")
async def cancel_order(request: Request):
    """External API to cancel an order (called by agent service)"""
    body = await request.json()
    order_id = body.get("order_id")

    if not order_id:
        return JSONResponse({"success": False, "message": "order_id required"}, status_code=400)

    success = order.cancel_order(int(order_id))
    if success:
        return JSONResponse({"success": True, "message": "Order cancelled", "order_id": order_id})
    return JSONResponse({"success": False, "message": "Order not found"}, status_code=404)


@app.get("/api/orders/recent")
async def get_recent_orders():
    """Get the last 3 orders"""
    all_orders = list(order.orders.values())
    sorted_orders = sorted(all_orders, key=lambda x: x["id"], reverse=True)
    recent_orders = sorted_orders[:3]

    return JSONResponse({
        "success": True,
        "count": len(recent_orders),
        "orders": recent_orders
    })


@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    """Admin dashboard to view all orders"""
    all_orders = list(order.orders.values())
    sorted_orders = sorted(all_orders, key=lambda x: x["id"], reverse=True)

    # Calculate statistics
    total_orders = len(all_orders)
    confirmed_orders = len([o for o in all_orders if o["status"] == "confirmed"])
    cancelled_orders = len([o for o in all_orders if o["status"] == "cancelled"])

    # Calculate RTG saved (cancelled orders total)
    rtg_saved = sum(o["total"] for o in all_orders if o["status"] == "cancelled")

    return templates.TemplateResponse("admin.html", {
        "request": request,
        "orders": sorted_orders,
        "total_orders": total_orders,
        "confirmed_orders": confirmed_orders,
        "cancelled_orders": cancelled_orders,
        "rtg_saved": rtg_saved
    })


@app.get("/api/admin/calls/{call_id}")
async def get_call_details(call_id: str):
    """Fetch call details from Bolna API and enrich with order data"""
    from src import agent

    try:
        # Fetch from Bolna API
        bolna_data = await agent.get_call_status(call_id)

        if not bolna_data:
            return JSONResponse(
                {"success": False, "message": "Call not found or API key not configured"},
                status_code=404
            )

        # Try to find the order with this call_id to enrich the response
        matching_order = None
        for o in order.orders.values():
            if o.get("call_id") == call_id:
                matching_order = o
                break

        # Enrich Bolna data with our order information if found
        if matching_order:
            # Ensure metadata field exists and has order context
            if "metadata" not in bolna_data or not bolna_data["metadata"]:
                bolna_data["metadata"] = {}

            # Add order details to metadata if not present
            products = matching_order.get("products", [])
            product_name = products[0]["name"] if products else "Unknown Product"

            bolna_data["metadata"].update({
                "order_id": str(matching_order["id"]),
                "customer_name": matching_order.get("customer_name", "Customer"),
                "product_name": product_name,
                "amount": f"{matching_order.get('total', 0):,}",
                "city": matching_order.get("address", "Unknown"),
            })

        logger.info(f"[API] Fetched call {call_id} — status: {bolna_data.get('status')}")
        return JSONResponse({"success": True, "data": bolna_data})

    except Exception as e:
        logger.error(f"[API] Failed to fetch call {call_id}: {e}")
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=500
        )


# Tool endpoints for Bolna agent callbacks
@app.post("/api/tools/confirm_order")
async def tool_confirm_order(body: dict):
    """Tool called by Bolna agent to confirm an order"""
    order_id = body.get("order_id", "")
    logger.info(f"[TOOL] confirm_order — order_id={order_id}")

    if order_id:
        try:
            order_id_int = int(order_id)
            success = order.confirm_order(order_id_int)
            if success:
                logger.info(f"[TOOL] Order {order_id} confirmed successfully")
                return {
                    "status": "success",
                    "message": "Order confirmed successfully. Please keep cash ready at delivery."
                }
        except (ValueError, KeyError) as e:
            logger.error(f"[TOOL] Failed to confirm order {order_id}: {e}")

    return {
        "status": "error",
        "message": "Failed to confirm order"
    }


@app.post("/api/tools/cancel_order")
async def tool_cancel_order(body: dict):
    """Tool called by Bolna agent to cancel an order"""
    order_id = body.get("order_id", "")
    reason = body.get("reason", "") or "Not specified"
    logger.info(f"[TOOL] cancel_order — order_id={order_id} reason={reason}")

    if order_id:
        try:
            order_id_int = int(order_id)
            success = order.cancel_order(order_id_int)
            if success:
                logger.info(f"[TOOL] Order {order_id} cancelled — reason: {reason}")
                return {
                    "status": "success",
                    "message": "Order has been cancelled. Reason recorded."
                }
        except (ValueError, KeyError) as e:
            logger.error(f"[TOOL] Failed to cancel order {order_id}: {e}")

    return {
        "status": "error",
        "message": "Failed to cancel order"
    }


@app.post("/api/tools/schedule_callback")
async def tool_schedule_callback(body: dict):
    """Tool called by Bolna agent to schedule a callback"""
    order_id = body.get("order_id", "")
    preferred_time = body.get("preferred_time", "") or "a convenient time"
    logger.info(f"[TOOL] schedule_callback — order_id={order_id} time={preferred_time}")

    if order_id:
        try:
            order_id_int = int(order_id)
            # For now, just log it - you can add callback_time field to orders if needed
            logger.info(f"[TOOL] Callback scheduled for order {order_id} at {preferred_time}")
            return {
                "status": "success",
                "message": f"Callback scheduled for {preferred_time}. We will call you back then."
            }
        except (ValueError, KeyError) as e:
            logger.error(f"[TOOL] Failed to schedule callback for order {order_id}: {e}")

    return {
        "status": "error",
        "message": "Failed to schedule callback"
    }


def _parse_transcript(raw_transcript) -> list:
    """Normalize Bolna transcript to list of {role, content} dicts."""
    if not raw_transcript:
        return []
    if isinstance(raw_transcript, list):
        return raw_transcript
    # Bolna sends string like: "assistant: Hello\nuser: Yes\nassistant: ..."
    messages = []
    for line in str(raw_transcript).split("\n"):
        line = line.strip()
        if not line:
            continue
        if line.startswith("assistant:"):
            messages.append({"role": "agent", "content": line[len("assistant:"):].strip()})
        elif line.startswith("user:"):
            messages.append({"role": "user", "content": line[len("user:"):].strip()})
        else:
            # continuation of previous message
            if messages:
                messages[-1]["content"] += " " + line
    return messages


@app.post("/api/webhooks/bolna")
async def bolna_webhook(request: Request):
    """Webhook endpoint to receive Bolna call status updates"""
    raw = await request.body()
    logger.info(f"[WEBHOOK] Received Bolna webhook ({len(raw)} bytes)")

    try:
        payload = json.loads(raw)
    except Exception as e:
        logger.error(f"[WEBHOOK] Failed to parse JSON: {e}")
        return {"ok": False}

    bolna_call_id = payload.get("id") or payload.get("call_id")
    transcript = _parse_transcript(payload.get("transcript"))
    duration = payload.get("conversation_duration") or payload.get("duration")
    status = payload.get("status")

    logger.info(f"[WEBHOOK] call_id={bolna_call_id} status={status} duration={duration} transcript_msgs={len(transcript)}")

    # You can add more webhook processing here
    # For now, just log it

    return {"ok": True}


@app.post("/api/orders/retry-call")
async def retry_call_for_order(request: Request):
    """Manually trigger/retry a COD confirmation call for an order"""
    from src import agent

    try:
        body = await request.json()
        order_id = body.get("order_id")

        if not order_id:
            return JSONResponse(
                {"success": False, "message": "order_id required"},
                status_code=400
            )

        # Get order from existing orders dict
        existing_order = order.orders.get(order_id)
        if not existing_order:
            return JSONResponse(
                {"success": False, "message": f"Order #{order_id} not found"},
                status_code=404
            )

        phone = existing_order.get("phone")
        if not phone:
            return JSONResponse(
                {"success": False, "message": "Order has no phone number"},
                status_code=400
            )

        logger.info(f"[RETRY] Manual call trigger for order #{order_id} to {phone}")

        # Trigger the call using existing order data
        call_result = await agent.trigger_cod_confirmation_call(phone, order_id, existing_order)

        if call_result.get("execution_id"):
            call_id = call_result.get("execution_id")
            # Update the order with the new call_id
            if call_id:
                order.orders[order_id]["call_id"] = call_id
                logger.info(f"[RETRY] Call initiated successfully for order #{order_id}, call_id: {call_id}")

            return JSONResponse({
                "success": True,
                "message": "Call initiated successfully",
                "call_id": call_id
            })
        else:
            logger.error(f"[RETRY] Failed to initiate call: {call_result}")
            return JSONResponse(
                {"success": False, "message": "Failed to initiate call"},
                status_code=500
            )

    except Exception as e:
        logger.error(f"[RETRY] Exception: {e}")
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=500
        )


@app.post("/api/orders/delivery-call")
async def trigger_delivery_call_for_order(request: Request):
    """Trigger a delivery notification call for a confirmed order"""
    from src import agent

    try:
        body = await request.json()
        order_id = body.get("order_id")

        if not order_id:
            return JSONResponse(
                {"success": False, "message": "order_id required"},
                status_code=400
            )

        # Get order from existing orders dict
        existing_order = order.orders.get(order_id)
        if not existing_order:
            return JSONResponse(
                {"success": False, "message": f"Order #{order_id} not found"},
                status_code=404
            )

        # Check if order is confirmed
        if existing_order.get("status") != "confirmed":
            return JSONResponse(
                {"success": False, "message": "Only confirmed orders can receive delivery calls"},
                status_code=400
            )

        phone = existing_order.get("phone")
        if not phone:
            return JSONResponse(
                {"success": False, "message": "Order has no phone number"},
                status_code=400
            )

        logger.info(f"[DELIVERY] Triggering delivery call for order #{order_id} to {phone}")

        # Trigger the delivery call using existing order data
        call_result = await agent.trigger_delivery_call(phone, order_id, existing_order)

        if call_result.get("execution_id"):
            call_id = call_result.get("execution_id")
            # Store the delivery call_id separately (optional: you can add a new field)
            if call_id:
                order.orders[order_id]["delivery_call_id"] = call_id
                logger.info(f"[DELIVERY] Delivery call initiated successfully for order #{order_id}, call_id: {call_id}")

            return JSONResponse({
                "success": True,
                "message": "Delivery call initiated successfully",
                "call_id": call_id
            })
        else:
            logger.error(f"[DELIVERY] Failed to initiate delivery call: {call_result}")
            return JSONResponse(
                {"success": False, "message": "Failed to initiate delivery call"},
                status_code=500
            )

    except Exception as e:
        logger.error(f"[DELIVERY] Exception: {e}")
        return JSONResponse(
            {"success": False, "message": str(e)},
            status_code=500
        )
