from flask import render_template, flash, url_for, redirect
from flask_login import login_required, current_user
from flask import Blueprint
from app.models import Orders, Address
from app.forms import AddAddress
from app.utils.functions import can_deliver_to
from app.extensions import safe_commit, db

profile_bp = Blueprint("profile",__name__,template_folder="templates")

@profile_bp.route("/profile")
@login_required
def profile():
    return render_template("profile/profile.html", user=current_user)

@profile_bp.route('/profile/price_alerts')
@login_required
def profile_price_alerts():
    alerts = current_user.price_alerts
    return render_template("profile/profile_price_alerts.html", alerts=alerts)

@profile_bp.route('/orders')
@login_required
def profile_orders():
    orders = Orders.query.filter_by(user_id=current_user.id).order_by(Orders.created_at.desc()).all()
    return render_template(
        "profile/profile_orders.html",
        orders=orders
    )

# ('invoice', order_id=order.order_id)

@profile_bp.route('/profile/address', methods=["GET", "POST"])
@login_required
def profile_addresses():
    form = AddAddress()

    if form.validate_on_submit():
        if not can_deliver_to(form.postcode.data):
            flash("Sorry, we don't currently deliver to that PIN code.", "danger")
            return redirect(url_for('profile.profile_addresses'))

        # Unset all current addresses for the user
        Address.query.filter_by(user_id=current_user.id).update({'current_address': False})

        # Add new address and mark as current
        address = Address(
            user_id=current_user.id,
            street=form.address.data,
            city=form.city.data,
            postcode=form.postcode.data,
            current_address=True
        )
        db.session.add(address)
        safe_commit()

        flash("Address saved and set as current!", "success")
        return redirect(url_for('profile.profile_addresses'))

    # Fetch current addresses
    addresses = Address.query.filter_by(user_id=current_user.id, deleted=False).all()
    return render_template("profile/profile_addresses.html", addresses=addresses, form=form)

@profile_bp.route('/profile/address/delete/<int:address_id>', methods=['POST'])
@login_required
def delete_address(address_id):
    address = Address.query.get_or_404(address_id)

    # Check ownership
    if address.user_id != current_user.id:
        flash("You can't delete this address.", "danger")
        return redirect(url_for('profile.profile_addresses'))

    # Soft delete instead of hard delete
    address.deleted = True
    safe_commit()

    flash("Address removed from your profile.", "success")
    return redirect(url_for('profile.profile_addresses'))

@profile_bp.route('/set-current-address/<int:address_id>', methods=['POST'])
@login_required
def set_current_address(address_id):
    address = Address.query.filter_by(id=address_id, user_id=current_user.id).first_or_404()

    if address.current_address:
        flash("This address is already current.", "info")
        return redirect(url_for('profile.profile_addresses'))

    # Fetch all user's addresses and unset current
    user_addresses = Address.query.filter_by(user_id=current_user.id).all()
    for addr in user_addresses:
        addr.current_address = False

    # Set selected address to True
    address.current_address = True

    safe_commit()
    flash("Current address updated.", "success")
    return redirect(url_for('profile.profile_addresses'))

