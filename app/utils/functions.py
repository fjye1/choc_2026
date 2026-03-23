# ─── Delivery Area Configuration ──────────────────────────────────────────
VALID_PREFIXES   = ("39", "40")
EXCLUDED_PREFIXES = ("403",)      # Goa — no delivery
# ──────────────────────────────────────────────────────────────────────────
# ─── Fee Configuration ────────────────────────────────────────────────────
SHIPPING_FEE            = 99      # ₹ flat shipping fee
SHIPPING_FREE_THRESHOLD = 500     # ₹ order value for free shipping
CARD_FEE_FIXED          = 25      # ₹ fixed card processing fee
CARD_FEE_PERCENT        = 5.25    # % card processing fee (applied to subtotal + shipping)
# ──────────────────────────────────────────────────────────────────────────

def can_deliver_to(pincode: str) -> bool:
    """
    Returns True if we deliver to the given PIN code.
    - Must start with 39 or 40
    - Must NOT start with 403 (Goa)
    """
    pincode = pincode.strip()

    if not pincode.isdigit() or len(pincode) != 6:
        return False

    if pincode.startswith(EXCLUDED_PREFIXES):
        return False

    return pincode.startswith(VALID_PREFIXES)

def precompute_products(products):
    for product in products:
        product._avg_rating = round(
            sum(c.rating for c in product.comments) / len(product.comments),
            1
        ) if product.comments else 0

        arrived_boxes = [
            b for b in product.boxes if b.is_active and b.shipment.has_arrived
        ]
        product._lowest_box = min(arrived_boxes, key=lambda b: b.price_inr_unit) if arrived_boxes else None

    return products

def build_price_groups(boxes):
    groups = {}
    for box in boxes:
        if box.price_inr_unit not in groups:
            groups[box.price_inr_unit] = {
                "quantity": 0,
                "expiry": box.expiration_date,
                "box": box,
                "shipment": box.shipment
            }
        groups[box.price_inr_unit]["quantity"] += box.quantity
    return groups



