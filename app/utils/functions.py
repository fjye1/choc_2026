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

