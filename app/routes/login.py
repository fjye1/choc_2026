# from flask import Blueprint, render_template, redirect, url_for, flash, request
# from flask_login import login_user
# from app.models import User  # your User model
# from app.forms import LoginForm  # your WTForms login form
#
# login_bp = Blueprint('login', __name__)
#
#
# @login_bp.route('/login', methods=['GET', 'POST'])
# def login():
#     form = LoginForm()
#
#     if form.validate_on_submit():
#         user = User.query.filter_by(email=form.email.data).first()
#
#         if user and user.check_password(form.password.data):
#             login_user(user, remember=form.remember_me.data)
#             flash("Logged in successfully!", "success")
#
#             next_page = request.args.get('next')
#             return redirect(next_page or url_for('home.index'))
#
#         flash("Invalid email or password.", "danger")
#
#     return render_template("login.html", form=form)



# app/routes/login.py
from flask import Blueprint, render_template

login_bp = Blueprint('login', __name__)

@login_bp.route('/login')
def login():
    # Just a test render for now
    return render_template("login.html")