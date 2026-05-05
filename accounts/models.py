from django.db import models
from django.contrib.auth.models import AbstractUser 


class User(AbstractUser):
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/",null=True,blank=True)
    is_verified = models.BooleanField(default=False)
    email_verification_sent_at = models.DateTimeField(null=True, blank=True)

    # This tell Django to use email as the unique identifier for authentication instead of username
    USERNAME_FIELD = "email"

    # These field will be prompted when creating a superuser 
    REQUIRED_FIELDS = ["username"]


class CompanySettings(models.Model):
    shop_name = models.CharField(max_length=120, default="Semkipo Laundry")
    company_phone = models.CharField(max_length=40, blank=True, default="9813694977")
    pan_number = models.CharField(max_length=40, blank=True, default="123456789")
    company_address = models.CharField(
        max_length=255,
        blank=True,
        default="Boudha, Kathmandu, Nepal",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Company setting"
        verbose_name_plural = "Company settings"

    def __str__(self):
        return self.shop_name
