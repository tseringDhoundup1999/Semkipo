from django.db import models
from django.contrib.auth.models import AbstractUser 


class User(AbstractUser):
    email = models.EmailField(unique=True)

    # This tell Django to use email as the unique identifier for authentication instead of username
    USERNAME_FIELD = "email"

    # These field will be prompted when creating a superuser 
    REQUIRED_FIELDS = ["username"]


