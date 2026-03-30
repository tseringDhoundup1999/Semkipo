from django.db import models

# Create your models here.

class MeasurementType(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class ItemType(models.Model):
    name = models.CharField(max_length=100)
    Measurement_type = models.ForeignKey(MeasurementType, on_delete=models.SET_NULL, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='measurement_items/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name