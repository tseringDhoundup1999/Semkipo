from django.db import models

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=200,null=True,blank=True)
    contact= models.CharField(max_length=20,unique=True)
    address= models.CharField(max_length=255,null=True,blank=True)
    loyalty_wash_count = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    def __str__(self):
        return f"{self.name} -- {self.contact}"