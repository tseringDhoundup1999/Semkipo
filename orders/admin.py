from django.contrib import admin
from .models import Order, OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "customer", "status", "discount", "total_price", "created_at", "updated_at")
    list_filter = ("status", "created_at")
    search_fields = ("customer__name",)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "ItemType", "quantity", "price", "created_at", "updated_at")
    list_filter = ("ItemType", "created_at")
    search_fields = ("order__customer__name", "ItemType__name")
