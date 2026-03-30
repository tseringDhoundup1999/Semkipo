from django.contrib import admin
from .models import MeasurementType, ItemType

# Register your models here.

@admin.register(MeasurementType)
class MeasurementTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

@admin.register(ItemType)
class ItemTypeAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'measurement_type', 'price_per_unit')
    search_fields = ('name',)