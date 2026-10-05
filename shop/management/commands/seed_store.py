from django.core.management.base import BaseCommand
from shop.models import Category, Product


class Command(BaseCommand):
    help = "Load a curated demo product catalog."

    def handle(self, *args, **options):
        categories = {}
        for name, slug in [("Home", "home"), ("Kitchen", "kitchen"), ("Desk", "desk"), ("Wellness", "wellness")]:
            categories[slug], _ = Category.objects.get_or_create(name=name, slug=slug)
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
            Product.objects.update_or_create(slug=slug, defaults={"name": name, "category": categories[category], "description": description, "price": price, "inventory": inventory, "featured": featured, "is_active": True})
        self.stdout.write(self.style.SUCCESS(f"Loaded {len(products)} demo products."))
