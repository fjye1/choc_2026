from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.utils.auth import internal_required
from app.models import Orders
from app.services.invoice_service import serialize_order

order_bp = Blueprint('orders', __name__, url_prefix='/orders')


@order_bp.route('/invoice/<string:order_id>')
@login_required
def invoice(order_id):
    order = Orders.query.filter_by(order_id=order_id, user_id=current_user.id).first_or_404()
    return render_template('orders/invoice.html', order=order)


@order_bp.route('/internal-invoice/<string:order_id>')
@internal_required
def internal_invoice(order_id):
    order = Orders.query.filter_by(order_id=order_id).first_or_404()
    return render_template('invoice.html', order=order)


@order_bp.route('/internal-invoice/<string:order_id>/json')
@internal_required
def internal_invoice_json(order_id):
    order = Orders.query.filter_by(order_id=order_id).first_or_404()
    return jsonify(serialize_order(order, request.url_root))
