from flask import Blueprint, render_template

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/test')
def admin_test():
    return render_template('admin/admin_test.html')