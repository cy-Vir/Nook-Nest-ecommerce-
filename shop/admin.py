from django.contrib import admin
from .models import Category, Product, Order, OrderItem


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "inventory", "featured", "is_active")
    list_editable = ("price", "inventory", "featured", "is_active")
    list_filter = ("category", "is_active", "featured")
    search_fields = ("name", "description")
    prepopulated_fields = {"slug": ("name",)}


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ("product", "product_name", "unit_price", "quantity")


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "full_name", "total", "status", "payment_reference", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("full_name", "email", "payment_reference")
    list_editable = ("status",)
    inlines = [OrderItemInline]
