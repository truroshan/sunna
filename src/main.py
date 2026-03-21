from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from src import products, cart, order

app = FastAPI(title="ByteIO - Shop", description="ByteIO - Shop")
templates = Jinja2Templates(directory="templates")


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
    
    ord = order.create_order(
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
