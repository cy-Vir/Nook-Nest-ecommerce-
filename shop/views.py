from decimal import Decimal
from uuid import uuid4
from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from .forms import CheckoutForm, RegistrationForm
from .models import Category, Order, OrderItem, Product


def _cart_items(request):
    cart = request.session.get("cart", {})
    products = Product.objects.filter(id__in=cart, is_active=True)
    items, subtotal = [], Decimal("0.00")
    for product in products:
        quantity = min(cart.get(str(product.id), 0), product.inventory)
        if quantity:
            line_total = product.price * quantity
            items.append({"product": product, "quantity": quantity, "line_total": line_total})
            subtotal += line_total
    return items, subtotal


def catalog(request):
    products = Product.objects.filter(is_active=True)
    query = request.GET.get("q", "").strip()
    category = request.GET.get("category", "")
    if query: products = products.filter(Q(name__icontains=query) | Q(description__icontains=query))
    if category: products = products.filter(category__slug=category)
    return render(request, "shop/catalog.html", {"products": products, "categories": Category.objects.all(), "query": query, "selected_category": category})


def product_detail(request, slug):
    return render(request, "shop/product_detail.html", {"product": get_object_or_404(Product, slug=slug, is_active=True)})


def add_to_cart(request, product_id):
    if request.method != "POST": return redirect("shop:catalog")
    product = get_object_or_404(Product, pk=product_id, is_active=True)
    cart = request.session.get("cart", {})
    quantity = int(request.POST.get("quantity", 1))
    current = cart.get(str(product.id), 0)
    if product.inventory <= 0: messages.error(request, f"{product.name} is currently out of stock.")
    else:
        cart[str(product.id)] = min(current + max(quantity, 1), product.inventory)
        request.session["cart"] = cart
        messages.success(request, f"{product.name} added to your cart.")
    return redirect(request.POST.get("next") or "shop:cart")


def cart_view(request):
    items, subtotal = _cart_items(request)
    return render(request, "shop/cart.html", {"items": items, "subtotal": subtotal})


def update_cart(request, product_id):
    if request.method != "POST": return redirect("shop:cart")
    cart = request.session.get("cart", {})
    product = get_object_or_404(Product, pk=product_id)
    quantity = max(0, int(request.POST.get("quantity", 0)))
    if quantity == 0: cart.pop(str(product_id), None)
    else: cart[str(product_id)] = min(quantity, product.inventory)
    request.session["cart"] = cart
    return redirect("shop:cart")


@login_required
def checkout(request):
    items, subtotal = _cart_items(request)
    if not items:
        messages.info(request, "Your cart is empty. Add a product before checkout.")
        return redirect("shop:catalog")
    if request.method == "POST":
        form = CheckoutForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                for item in items:
                    product = Product.objects.select_for_update().get(pk=item["product"].pk)
                    if product.inventory < item["quantity"]:
                        form.add_error(None, f"Only {product.inventory} unit(s) of {product.name} remain.")
                        break
                else:
                    order = Order.objects.create(user=request.user, total=subtotal, payment_reference=f"DEMO-{uuid4().hex[:10].upper()}", **{key: value for key, value in form.cleaned_data.items() if key != "payment_method"})
                    for item in items:
                        product = Product.objects.select_for_update().get(pk=item["product"].pk)
                        product.inventory -= item["quantity"]
                        product.save(update_fields=["inventory"])
                        OrderItem.objects.create(order=order, product=product, product_name=product.name, unit_price=product.price, quantity=item["quantity"])
                    request.session["cart"] = {}
                    messages.success(request, f"Order #{order.pk} placed successfully. Payment reference: {order.payment_reference}")
                    return redirect("shop:order_detail", pk=order.pk)
    else:
        form = CheckoutForm(initial={"full_name": request.user.get_full_name() or request.user.username, "email": request.user.email})
    return render(request, "shop/checkout.html", {"form": form, "items": items, "subtotal": subtotal})


@login_required
def order_list(request):
    return render(request, "shop/order_list.html", {"orders": request.user.orders.prefetch_related("items").all()})


@login_required
def order_detail(request, pk):
    return render(request, "shop/order_detail.html", {"order": get_object_or_404(Order.objects.prefetch_related("items"), pk=pk, user=request.user)})


def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            user.first_name = form.cleaned_data["first_name"]
            user.email = form.cleaned_data["email"]
            user.save(update_fields=["first_name", "email"])
            login(request, user)
            messages.success(request, "Your account is ready. Welcome to Nook & Nest!")
            return redirect("shop:catalog")
    else: form = RegistrationForm()
    return render(request, "registration/register.html", {"form": form})
