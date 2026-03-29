from django.urls import path 
from .views import create_contact_view

urlpatterns = [
    path("contact/create",create_contact_view.as_view())
]
