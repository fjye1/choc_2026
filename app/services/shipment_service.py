from app.models import Shipment, Box, Product
from app.extensions import db, safe_commit
from datetime import datetime, timezone

def get_all_shipments_admin():
    """
    Fetch all shipments with calculated fields needed for admin view.
    """
    shipments = Shipment.query.order_by(Shipment.date_created.desc()).all()
    return shipments


def create_shipment(transit_cost: float, tariff_cost: float = 0.0) -> Shipment:
    shipment = Shipment(
        transit_cost=transit_cost,
        tariff_cost_gbp=tariff_cost
    )
    db.session.add(shipment)
    safe_commit()
    return shipment



def add_box_to_shipment(shipment_id: int, product_id: int, quantity: int,
                        landing_price_gbp_box: float, weight_per_unit: float,
                        expiration_date, dynamic_pricing_enabled: bool) -> Box:
    product = Product.query.get(product_id)
    if not product:
        return None  # Caller should handle the flash/message

    box = Box(
        shipment_id=shipment_id,
        product_id=product.id,
        quantity=quantity,
        landing_price_gbp_box=landing_price_gbp_box,
        weight_per_unit=weight_per_unit,
        expiration_date=expiration_date,
        dynamic_pricing_enabled=dynamic_pricing_enabled
    )
    db.session.add(box)
    safe_commit()
    return box