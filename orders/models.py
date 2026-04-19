from django.db import models
from customers.models import Customer
from measurement.models import ItemType
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.

class Order(models.Model):
    class StatusChoice(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
    
    class DeliveryChoice(models.TextChoices):
        PICKUP = "pk","Pickup"
        DELIVERY = "d","Delivery"
    
    class PaymentChoice(models.TextChoices):
        PAID = 'p','Paid'
        UNPAID = 'up', 'Unpaid'
        
    
    customer = models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,related_name="orders")
    status = models.CharField(max_length=20, choices=StatusChoice.choices,default=StatusChoice.PENDING)
    payment_status = models.CharField(max_length=4,choices=PaymentChoice.choices,default=PaymentChoice.UNPAID)
    delivery_type = models.CharField(max_length=4,choices=DeliveryChoice.choices,default=DeliveryChoice.PICKUP)
    delivery_address = models.CharField(max_length=255,blank=True,null=True)
    delivery_charge = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    discount = models.PositiveSmallIntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(100)])  # Discount percentage (0-100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.name if self.customer else 'No Customer'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
    measurement_type = models.ForeignKey(ItemType,on_delete=models.SET_NULL,null=True)
    quantity = models.DecimalField(max_digits=10,decimal_places=2,default=1.0)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OrderItem #{self.id} - {self.measurement_type.name if self.measurement_type else 'No ItemType'}"
    
    def save(self,*args,**kwargs):
        item_price = self.measurement_type.price_per_unit if self.measurement_type else 0 
        self.price = item_price * self.quantity
        super().save(*args,**kwargs)
    