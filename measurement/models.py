from django.db import models
from django.core.exceptions import ValidationError
import os 
# Create your models here.

def validate_image(image):
        
        allowed_extensions = ['.jpg', '.jpeg', '.png']
        max_size = 2 * 1024 * 1024  # 2MB
        
        ext = os.path.splitext(image.name)[1].lower()
        if ext not in allowed_extensions:
            raise ValidationError("Unsupported file extension. Allowed extensions are: .jpg, .jpeg, .png")
        
        if image.size > max_size:
            raise ValidationError("Image size exceeds the maximum limit of 2MB.")

class MeasurementType(models.Model):
    name = models.CharField(max_length=100)

    DECIMAL_ALLOWED_UNITS = {
        "kg",
        "kilogram",
        "kilograms",
        "g",
        "gm",
        "gram",
        "grams",
        "mg",
        "ltr",
        "liter",
        "litre",
        "liters",
        "litres",
        "ml",
        "meter",
        "metre",
        "m",
        "cm",
    }

    def __str__(self):
        return self.name

    def allows_decimal_quantity(self):
        normalized_name = (self.name or "").strip().lower()
        return normalized_name in self.DECIMAL_ALLOWED_UNITS

class ItemType(models.Model):
    name = models.CharField(max_length=100)
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.SET_NULL, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='measurement_items/', null=True, blank=True,validators=[validate_image])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    def allows_decimal_quantity(self):
        if not self.measurement_type:
            return False
        return self.measurement_type.allows_decimal_quantity()
    
    
    