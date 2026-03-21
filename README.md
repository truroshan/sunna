# ByteIO - COD Order Confirmation System

A FastAPI-based e-commerce order system with AI-powered phone call confirmations for Cash on Delivery (COD) orders using Bolna Voice AI.

## Features

- **Product Listing** - Browse products with images and prices
- **Shopping Cart** - Add/remove items, view cart total
- **Checkout** - Enter customer details, select payment mode (COD/Card)
- **COD Confirmation** - AI agent calls customer to confirm COD orders
- **Order Tracking** - View order status (Pending/Confirmed/Cancelled)
- **REST API** - External integration endpoints for order confirmation

## Tech Stack

- **Backend**: FastAPI, Python 3.11
- **Frontend**: HTML, Tailwind CSS, Vanilla JS
- **AI Calling**: Bolna Voice AI
- **Deployment**: NixOS with OCI containers

## Project Structure

```
├── flake.nix              # NixOS flake for Docker image
├── src/
│   ├── main.py           # FastAPI application
│   ├── products.py       # Product data (dict-based)
│   ├── cart.py           # Shopping cart (session-based)
│   ├── order.py          # Order management
│   └── agent.py          # Bolna API integration
└── templates/
    ├── index.html        # Product listing
    ├── cart.html         # Cart & checkout
    ├── orders.html       # Order history
    └── success.html      # Order confirmation
```

## Quick Start

### Development
```bash
# Enter dev shell
nix develop

# Run server
uvicorn src.main:app --reload
```

### Production (Docker)
```bash
# Build image
nix build .#defaultPackage

# Load and run
docker load < result
docker run -p 8000:8000 byteio-cod-confirmation:latest
```

### With Environment Variables
```bash
docker run -p 8000:8000 \
  -e BOLNA_API_KEY=your-key \
  -e BOLNA_AGENT_ID=your-agent-id \
  byteio-cod-confirmation:latest
```

## API Endpoints

### Web Pages
| Route | Description |
|-------|-------------|
| `/` | Redirect to products |
| `/products` | Product listing |
| `/cart` | Shopping cart |
| `/orders` | Order history |

### API (External)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/orders/confirm` | Confirm COD order |
| POST | `/api/orders/cancel` | Cancel COD order |

### API Request/Response
```bash
# Confirm order
curl -X POST http://localhost:8000/api/orders/confirm \
  -H "Content-Type: application/json" \
  -d '{"order_id": 1}'

# Response
{"success": true, "message": "Order confirmed", "order_id": 1}
```

## Order Flow

1. **User** places order with COD payment
2. **System** creates order with status "pending"
3. **Bolna** schedules AI call after 10 seconds (IST → UTC)
4. **AI Agent** calls customer asking for confirmation
5. **Customer** confirms or cancels
6. **Bolna** calls `/api/orders/confirm` or `/api/orders/cancel`
7. **System** updates order status

## Bolna Integration

### Agent Prompt
```
You are calling to confirm a COD order.

State the order details and ask for confirmation.
End call after response.
```

### Hangup Prompt
```
End call when: user confirms/cancels, says thanks/bye, or no response after 2 attempts.
```

### Function Schema

#### Confirm Order
```json
{
  "name": "confirm_order",
  "description": "Use this function when the customer confirms their COD order. Call this function after the customer says yes, confirm, proceed, or any positive confirmation to their order. Do not call this if the customer wants to cancel.",
  "pre_call_message": "Confirming your order now.",
  "parameters": {
    "type": "object",
    "required": [
      "order_id"
    ],
    "properties": {
      "order_id": {
        "type": "integer",
        "description": "The order ID number."
      }
    }
  },
  "key": "custom_task",
  "value": {
    "method": "POST",
    "param": {
      "order_id": "%(order_id)i"
    },
    "url": "https://sunna.byteio.in/api/orders/confirm",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

#### Cancel Order
```json
{
  "name": "cancel_order",
  "description": "Use this function when the customer wants to cancel their COD order.",
  "pre_call_message": "Cancelling your order now.",
  "parameters": {
    "type": "object",
    "required": [
      "order_id"
    ],
    "properties": {
      "order_id": {
        "type": "integer",
        "description": "The order ID number."
      }
    }
  },
  "key": "custom_task",
  "value": {
    "method": "POST",
    "param": {
      "order_id": "%(order_id)i"
    },
    "url": "https://sunna.byteio.in/api/orders/cancel",
    "headers": {
      "Content-Type": "application/json"
    }
  }
}
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `BOLNA_API_KEY` | Bolna API authentication key |
| `BOLNA_AGENT_ID` | Bolna agent ID for calls |

## Order Status

| Status | Description |
|--------|-------------|
| `pending` | COD order waiting for confirmation |
| `confirmed` | Order confirmed by customer |
| `cancelled` | Order cancelled by customer |

## License

MIT
