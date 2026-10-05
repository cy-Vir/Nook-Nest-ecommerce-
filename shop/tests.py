from decimal import Decimal
from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse
from .models import Category, Product


class ShopTests(TestCase):
    def setUp(self):
        category = Category.objects.create(name="Home", slug="home")
        self.product = Product.objects.create(category=category, name="Cloud Vase", slug="cloud-vase", description="Test product", price=Decimal("799.00"), inventory=4)
        self.user = User.objects.create_user(username="demo", password="demo-pass-123")

    def test_catalog_loads(self): self.assertContains(self.client.get(reverse("shop:catalog")), "Cloud Vase")
    def test_add_to_cart(self):
        self.client.post(reverse("shop:add_to_cart", args=[self.product.id]), {"quantity": 2})
        self.assertEqual(self.client.session["cart"][str(self.product.id)], 2)
    def test_checkout_reduces_inventory(self):
        self.client.force_login(self.user)
        self.client.post(reverse("shop:add_to_cart", args=[self.product.id]), {"quantity": 1})
        response = self.client.post(reverse("shop:checkout"), {"full_name": "Demo User", "email": "demo@example.com", "address": "12 Palm Road", "city": "Pune", "postal_code": "411001", "payment_method": "demo_card"})
        self.assertEqual(response.status_code, 302)
        self.product.refresh_from_db()
        self.assertEqual(self.product.inventory, 3)
