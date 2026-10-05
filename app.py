"""Nook & Nest Flask storefront."""
from __future__ import annotations

import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from flask import Flask, abort, flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, UserMixin, current_user, login_required, login_user, logout_user
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_
from werkzeug.security import check_password_hash, generate_password_hash


BASE_DIR = Path(__file__).resolve().parent
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.login_message = "Please sign in to continue to checkout."
login_manager.login_message_category = "error"


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    first_name = db.Column(db.String(30), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    orders = db.relationship("Order", back_populates="user", lazy=True)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)
    slug = db.Column(db.String(80), unique=True, nullable=False)
    products = db.relationship("Product", back_populates="category", lazy=True)


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey("category.id"), nullable=False)
    name = db.Column(db.String(150), nullable=False)
    slug = db.Column(db.String(150), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    inventory = db.Column(db.Integer, nullable=False, default=0)
    image_url = db.Column(db.String(500), nullable=False, default="")
    featured = db.Column(db.Boolean, nullable=False, default=False)
    is_active = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    category = db.relationship("Category", back_populates="products")

    @property
    def url(self) -> str:
        return url_for("product_detail", slug=self.slug)


class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    full_name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(80), nullable=False)
    postal_code = db.Column(db.String(12), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), nullable=False, default="paid")
    payment_reference = db.Column(db.String(60), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=lambda: datetime.now(timezone.utc))
    user = db.relationship("User", back_populates="orders")
    items = db.relationship("OrderItem", back_populates="order", cascade="all, delete-orphan", lazy=True)

    @property
    def status_label(self) -> str:
        return self.status.replace("_", " ").title()


class OrderItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey("order.id"), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey("product.id"), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    order = db.relationship("Order", back_populates="items")
    product = db.relationship("Product")

    @property
    def line_total(self) -> Decimal:
        return self.unit_price * self.quantity


def create_app(test_config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "change-this-before-production"),
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{BASE_DIR / 'store.db'}",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config:
        app.config.update(test_config)

    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id: str) -> User | None:
        return db.session.get(User, int(user_id))

    @app.context_processor
    def cart_context() -> dict:
        return {"cart_count": sum(session.get("cart", {}).values())}

    def cart_items() -> tuple[list[dict], Decimal]:
        cart = session.get("cart", {})
        ids = [int(product_id) for product_id in cart if product_id.isdigit()]
        products = Product.query.filter(Product.id.in_(ids), Product.is_active.is_(True)).all() if ids else []
        items: list[dict] = []
        subtotal = Decimal("0.00")
        for product in products:
            quantity = min(int(cart.get(str(product.id), 0)), product.inventory)
            if quantity > 0:
                line_total = product.price * quantity
                items.append({"product": product, "quantity": quantity, "line_total": line_total})
                subtotal += line_total
        return items, subtotal

    @app.get("/")
    def catalog():
        query = request.args.get("q", "").strip()
        selected_category = request.args.get("category", "")
        products = Product.query.filter_by(is_active=True)
        if query:
            needle = f"%{query}%"
            products = products.filter(or_(Product.name.ilike(needle), Product.description.ilike(needle)))
        if selected_category:
            products = products.join(Category).filter(Category.slug == selected_category)
        return render_template(
            "shop/catalog.html",
            products=products.order_by(Product.featured.desc(), Product.name).all(),
            categories=Category.query.order_by(Category.name).all(),
            query=query,
            selected_category=selected_category,
        )

    @app.get("/products/<slug>/")
    def product_detail(slug: str):
        product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
        return render_template("shop/product_detail.html", product=product)

    @app.post("/cart/add/<int:product_id>/")
    def add_to_cart(product_id: int):
        product = db.session.get(Product, product_id)
        if not product or not product.is_active:
            abort(404)
        cart = session.get("cart", {})
        try:
            quantity = int(request.form.get("quantity", 1))
        except ValueError:
            quantity = 1
        if product.inventory <= 0:
            flash(f"{product.name} is currently out of stock.", "error")
        else:
            current = int(cart.get(str(product.id), 0))
            cart[str(product.id)] = min(current + max(quantity, 1), product.inventory)
            session["cart"] = cart
            flash(f"{product.name} added to your cart.", "success")
        return redirect(request.form.get("next") or url_for("cart"))

    @app.get("/cart/")
    def cart():
        items, subtotal = cart_items()
        return render_template("shop/cart.html", items=items, subtotal=subtotal)

    @app.post("/cart/update/<int:product_id>/")
    def update_cart(product_id: int):
        product = db.session.get(Product, product_id)
        if not product:
            abort(404)
        try:
            quantity = max(0, int(request.form.get("quantity", 0)))
        except ValueError:
            quantity = 0
        cart = session.get("cart", {})
        if quantity == 0:
            cart.pop(str(product_id), None)
        else:
            cart[str(product_id)] = min(quantity, product.inventory)
        session["cart"] = cart
        return redirect(url_for("cart"))

    @app.route("/checkout/", methods=["GET", "POST"])
    @login_required
    def checkout():
        items, subtotal = cart_items()
        if not items:
            flash("Your cart is empty. Add a product before checkout.", "info")
            return redirect(url_for("catalog"))
        values = {"full_name": current_user.first_name or current_user.username, "email": current_user.email}
        errors: dict[str, str] = {}
        if request.method == "POST":
            values = {field: request.form.get(field, "").strip() for field in ("full_name", "email", "address", "city", "postal_code", "payment_method")}
            for field in ("full_name", "email", "address", "city", "postal_code", "payment_method"):
                if not values[field]:
                    errors[field] = "This field is required."
            if values.get("email") and "@" not in values["email"]:
                errors["email"] = "Enter a valid email address."
            if values.get("payment_method") not in {"demo_card", "cash"}:
                errors["payment_method"] = "Choose a payment method."
            if not errors:
                refreshed_items, refreshed_subtotal = cart_items()
                unavailable = next((item for item in refreshed_items if item["product"].inventory < item["quantity"]), None)
                if unavailable:
                    errors["form"] = f"Only {unavailable['product'].inventory} unit(s) of {unavailable['product'].name} remain."
                else:
                    order = Order(
                        user=current_user,
                        total=refreshed_subtotal,
                        payment_reference=f"DEMO-{uuid4().hex[:10].upper()}",
                        **{field: values[field] for field in ("full_name", "email", "address", "city", "postal_code")},
                    )
                    db.session.add(order)
                    for item in refreshed_items:
                        product = item["product"]
                        product.inventory -= item["quantity"]
                        order.items.append(OrderItem(product=product, product_name=product.name, unit_price=product.price, quantity=item["quantity"]))
                    db.session.commit()
                    session["cart"] = {}
                    flash(f"Order #{order.id} placed successfully. Payment reference: {order.payment_reference}", "success")
                    return redirect(url_for("order_detail", order_id=order.id))
        return render_template("shop/checkout.html", items=items, subtotal=subtotal, values=values, errors=errors)

    @app.get("/orders/")
    @login_required
    def order_list():
        orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
        return render_template("shop/order_list.html", orders=orders)

    @app.get("/orders/<int:order_id>/")
    @login_required
    def order_detail(order_id: int):
        order = Order.query.filter_by(id=order_id, user_id=current_user.id).first_or_404()
        return render_template("shop/order_detail.html", order=order)

    @app.route("/accounts/register/", methods=["GET", "POST"])
    def register():
        values = {}
        errors: dict[str, str] = {}
        if request.method == "POST":
            values = {field: request.form.get(field, "").strip() for field in ("first_name", "username", "email")}
            password = request.form.get("password", "")
            password_confirm = request.form.get("password_confirm", "")
            for field, label in (("first_name", "First name"), ("username", "Username"), ("email", "Email")):
                if not values[field]:
                    errors[field] = f"{label} is required."
            if values.get("email") and "@" not in values["email"]:
                errors["email"] = "Enter a valid email address."
            if len(password) < 8:
                errors["password"] = "Use at least 8 characters."
            if password != password_confirm:
                errors["password_confirm"] = "Passwords do not match."
            if User.query.filter((User.username == values.get("username")) | (User.email == values.get("email"))).first():
                errors["form"] = "That username or email is already registered."
            if not errors:
                user = User(**values)
                user.set_password(password)
                db.session.add(user)
                db.session.commit()
                login_user(user)
                flash("Your account is ready. Welcome to Nook & Nest!", "success")
                return redirect(url_for("catalog"))
        return render_template("registration/register.html", values=values, errors=errors)

    @app.route("/accounts/login/", methods=["GET", "POST"])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for("catalog"))
        errors: dict[str, str] = {}
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            user = User.query.filter_by(username=username).first()
            if not user or not user.check_password(request.form.get("password", "")):
                errors["form"] = "Invalid username or password."
            else:
                login_user(user)
                return redirect(request.args.get("next") or url_for("catalog"))
        return render_template("registration/login.html", errors=errors)

    @app.post("/accounts/logout/")
    @login_required
    def logout():
        logout_user()
        flash("You have been signed out.", "info")
        return redirect(url_for("catalog"))

    with app.app_context():
        db.create_all()
        seed_catalog()
    return app


def seed_catalog() -> None:
    if Product.query.first():
        return
    categories = {}
    for name, slug in [("Home", "home"), ("Kitchen", "kitchen"), ("Desk", "desk"), ("Wellness", "wellness")]:
        category = Category(name=name, slug=slug)
        db.session.add(category)
        categories[slug] = category
    db.session.flush()
    products = [
        ("Cloud Vase", "cloud-vase", "home", "A softly sculpted ceramic vase for small branches and unhurried tables.", "799.00", 14, True),
        ("Sage Linen Throw", "sage-linen-throw", "home", "Breathable washed linen with a fringed finish for cooler evenings.", "1899.00", 8, True),
        ("Sunday Mug", "sunday-mug", "kitchen", "A generous stoneware mug, glazed by hand in warm oat tones.", "549.00", 23, True),
        ("Olive Oil Pourer", "olive-oil-pourer", "kitchen", "A practical countertop pourer with a balanced, easy-grip shape.", "649.00", 11, False),
        ("Tapered Desk Lamp", "tapered-desk-lamp", "desk", "Soft directional light for a more comfortable evening desk ritual.", "2499.00", 5, True),
        ("Paperbound Planner", "paperbound-planner", "desk", "Undated weekly pages and generous notes space for thoughtful planning.", "699.00", 17, False),
        ("Cedar Bath Soak", "cedar-bath-soak", "wellness", "Mineral-rich bath salts with a grounding cedar and bergamot scent.", "599.00", 19, False),
        ("Quiet Morning Candle", "quiet-morning-candle", "wellness", "A small-batch soy candle with notes of fig leaf and sandalwood.", "899.00", 0, False),
    ]
    for name, slug, category, description, price, inventory, featured in products:
        db.session.add(Product(name=name, slug=slug, category=categories[category], description=description, price=Decimal(price), inventory=inventory, featured=featured))
    db.session.commit()


app = create_app()

if __name__ == "__main__":
    app.run(debug=True)
