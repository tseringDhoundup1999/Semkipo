from django.db import models

# Create your models here.

class Customer(models.Model):
    name = models.CharField(max_length=200)
    contact= models.CharField(max_length=20,unique=True)
    email = models.EmailField(blank=True,null=True)
    secondary_contact = models.CharField(max_length=20,null=True,blank=True)
    
    def __str__(self):
        return f"{self.name} -- {self.contact}"