from flask import Blueprint, render_template, request, jsonify, make_response, current_app, abort
from flask_login import login_required, current_user

from app.models import Orders
from app.services.invoice_service import serialize_order, generate_invoice_pdf
from app.utils.auth import internal_required

order_bp  = Blueprint("orders", __name__, url_prefix="/orders")


@order_bp.route('/invoice/<string:order_id>')
@login_required
def invoice(order_id):
    order = Orders.query.filter_by(order_id=order_id, user_id=current_user.id).first_or_404()
    return render_template('orders/invoice.html', order=order)


@order_bp.route('/internal-invoice/<string:order_id>')
@internal_required
def internal_invoice(order_id):
    order = Orders.query.filter_by(order_id=order_id).first_or_404()
    return render_template('orders/invoice.html', order=order)


@order_bp.route('/internal-invoice/<string:order_id>/json')
@internal_required
def internal_invoice_json(order_id):
    order = Orders.query.filter_by(order_id=order_id).first_or_404()
    return jsonify(serialize_order(order, request.url_root))


@order_bp.route('/invoice/<order_id>/download')
@login_required
def download_invoice(order_id):
    # Get the order for the current user
    order = Orders.query.filter_by(order_id=order_id, user_id=current_user.id).first_or_404()

    # Generate PDF using pdfkit
    try:
        pdf_bytes = generate_invoice_pdf(order)
    except Exception as e:
        current_app.logger.error(f"PDF generation failed for order {order_id}: {e}")
        abort(500, description="Invoice generation failed")

    # Return PDF as downloadable file
    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=invoice_{order.order_id}.pdf'
    return response
