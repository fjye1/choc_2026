from flask import Blueprint, render_template

products_bp = Blueprint('products', __name__)

@products_bp.route('/product-test')
def product_test():
    return render_template('product/product_test.html')