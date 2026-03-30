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
    
    customer = models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,related_name="orders")
    status = models.CharField(max_length=20, choices=StatusChoice.choices,default=StatusChoice.PENDING)
    discount = models.PositiveSmallIntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(100)])  # Discount percentage (0-100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def pre_save(self, *args, **kwargs):
        total = self.total_price 
        discount_amount = total * (self.discount / 100)
        self.total_price = total - discount_amount
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.name if self.customer else 'No Customer'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
    ItemType = models.ForeignKey(ItemType,on_delete=models.SET_NULL,null=True)
    quantity = models.PositiveIntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OrderItem #{self.id} - {self.ItemType.name if self.ItemType else 'No ItemType'}"
    
    def pre_save(self,*args,**kwargs):
        item_price = self.ItemType.price_per_unit if self.ItemType else 0 
        self.price = item_price * self.quantity
        super().save(*args,**kwargs)
    