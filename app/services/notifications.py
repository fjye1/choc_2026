import requests
from flask import current_app



def send_discord_order_notification(order):
    discord_webhook_url = current_app.config.get("DISCORD_WEBHOOK_URL")
    # Build items list from order_items relationship
    items_text = "\n".join(
        f"• {item.quantity}x {item.product.name} — ₹{item.price_at_purchase:.2f}"
        for item in order.order_items
    )

    # Build address from shipping_address relationship
    address = order.shipping_address
    address_text = f"{address.street}, {address.city}, {address.postcode}"
    payload = {
        "embeds": [{
            "title": '🛒 New Order Received! ',
            "color": 0x00C851,
            "fields": [
                {
                    "name": "🧾 Order ID",
                    "value": f"{order.order_id}",
                    "inline": True
                },
                {
                    "name": "💰  Total",
                    "value": f"₹{order.total_amount:.2f}",
                    "inline": True
                },
                {
                    "name": "📦 Items",
                    "value": items_text or "No items found",
                    "inline": False
                },
                {
                    "name": "🚚 Shipping Address",
                    "value": address_text,
                    "inline": False
                },
            ],
            "footer": {"text": f"Order #{order.order_id}"}
        }]
    }

    response = requests.post(discord_webhook_url, json=payload)

    if response.status_code == 204:
        print("✅ Success! Check your Discord channel.")
    else:
        print(f"❌ Failed — Status: {response.status_code}, Response: {response.text}")
