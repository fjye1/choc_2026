from flask import render_template
from flask_login import login_required, current_user
from flask import Blueprint


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

# @profile_bp.route('/delete-alert/<int:alert_id>', methods=['POST'])
# @login_required
# def delete_alert(alert_id):
#     alert = PriceAlert.query.get_or_404(alert_id)
#
#     if alert.user_id != current_user.id:
#         abort(403)
#
#     db.session.delete(alert)
#     safe_commit()
#     flash("Price alert deleted.", "success")
#     return redirect(url_for('profile_price_alerts'))