from flask import render_template, current_app
import io
from xhtml2pdf import pisa
import os


def serialize_order(order, url_root):
    return {
        "order_id": order.order_id,
        "created_at": order.created_at.isoformat(),
        "created_at_formatted": order.created_at.strftime('%b %d, %Y'),
        "status": order.status,

        "subtotal": float(order.subtotal),
        "shipping": float(order.shipping),
        "card_fee": float(order.card_fee),
        "grand_total": float(order.total_amount),

        "shipping_address": {
            "street": order.shipping_address.street,
            "city": order.shipping_address.city,
            "postcode": order.shipping_address.postcode,
        } if order.shipping_address else None,

        "items": [
            {
                "product_name": item.product.name,
                # Full URL if url_root provided, else just filename
                "product_image": f"{url_root.rstrip('/')}/{item.product.pdf_image}" if url_root else item.product.pdf_image,
                "box_id": item.box_id,
                "shipment_id": item.shipment_id,
                "quantity": item.quantity,
                "price_at_purchase": float(item.price_at_purchase),
                "line_total": float(item.quantity * item.price_at_purchase),
            }
            for item in order.order_items
        ]
    }


def link_callback(uri, rel):
    # Convert /static/... to the real filesystem path
    if uri.startswith('/static/'):
        path = os.path.join(current_app.root_path, uri[1:])
        return path
    return uri


def generate_invoice_pdf(order):
    html = render_template('orders/invoice.html', order=order)
    result = io.BytesIO()
    pisa_status = pisa.CreatePDF(html, dest=result, link_callback=link_callback)
    if pisa_status.err:
        raise Exception("PDF generation failed")
    return result.getvalue()
