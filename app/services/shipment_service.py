from app.models import Shipment, Box, Product
from app.extensions import db, safe_commit
from datetime import datetime, timezone
from app.services.currency_service import inr_to_gbp, gbp_to_inr

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



def _process_box_costs(box, total_weight, transit_cost, total_cost_incl_shipping, tariff_cost_gbp):
    box_weight = float(box.weight_per_unit) * box.quantity

    shipping_share_gbp = (box_weight / total_weight) * float(transit_cost)

    box_cost_incl_shipping_gbp = float(box.landing_price_gbp_box) + shipping_share_gbp

    tariff_share_gbp = (
        box_cost_incl_shipping_gbp / total_cost_incl_shipping
    ) * tariff_cost_gbp

    total_box_cost_gbp = box_cost_incl_shipping_gbp + tariff_share_gbp

    cost_per_unit_gbp = total_box_cost_gbp / box.quantity

    box.price_gbp_unit = round(cost_per_unit_gbp, 4)
    box.floor_price_gbp_unit = round(cost_per_unit_gbp * 0.8, 2)

    cost_per_unit_inr = gbp_to_inr(cost_per_unit_gbp)

    box.landing_price_inr_box = round(cost_per_unit_inr * box.quantity, 2)
    box.floor_price_inr_unit = round(cost_per_unit_inr * 0.8, 2)
    box.price_inr_unit = round(cost_per_unit_inr * 1.15, 2)


def process_shipment_arrival(shipment, tariff_cost_rupees):
    tariff_cost_rupees = float(tariff_cost_rupees or 0.0)
    tariff_cost_gbp = inr_to_gbp(tariff_cost_rupees)

    shipment.has_arrived = True
    shipment.date_arrived = datetime.now(timezone.utc)
    shipment.tariff_cost_rupees = tariff_cost_rupees
    shipment.tariff_cost_gbp = tariff_cost_gbp
    shipment.inr_to_gbp_exchange_rate = inr_to_gbp(1)

    shipment_total_cost = sum(float(box.landing_price_gbp_box) for box in shipment.boxes)
    shipment_total_weight = sum(float(box.weight_per_unit) * box.quantity for box in shipment.boxes)
    shipment_total_cost_including_shipping = shipment_total_cost + float(shipment.transit_cost)

    for box in shipment.boxes:
        _process_box_costs(
            box,
            shipment_total_weight,
            shipment.transit_cost,
            shipment_total_cost_including_shipping,
            tariff_cost_gbp
        )

    safe_commit()