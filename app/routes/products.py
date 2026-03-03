from flask import Blueprint, render_template, request, redirect, url_for, flash
from app.models import Product

product_bp = Blueprint("product", __name__, url_prefix="/products")


@product_bp.route("/product-test")
def product_test():
    return render_template("product/product_test.html")


@product_bp.route("/search")
def search():
    query = request.args.get("q", "").strip()
    if not query:
        flash("Please enter a search term.", "warning")
        return redirect(url_for("main.home"))

    results = Product.query.filter(
        Product.name.ilike(f"%{query}%")
    ).all()

    return render_template(
        "product/search_results.html",
        query=query,
        results=results
    )