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

    def __str__(self):
        return self.name

class ItemType(models.Model):
    name = models.CharField(max_length=100)
    measurement_type = models.ForeignKey(MeasurementType, on_delete=models.SET_NULL, null=True)
    price_per_unit = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='measurement_items/', null=True, blank=True,validators=[validate_image])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    
    