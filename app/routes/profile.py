from flask import render_template
from flask_login import login_required, current_user
from flask import Blueprint


profile_bp = Blueprint("profile",__name__,template_folder="templates")

@profile_bp.route("/profile")
@login_required
def profile():
    return render_template("profile/profile.html", user=current_user)