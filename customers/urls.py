from django.urls import path 
from .views import Customers_view, create_contact_view, update_name_view

urlpatterns = [
    path("", Customers_view.as_view()),
    path("contact/create/",create_contact_view.as_view()),
    path("name/update/",update_name_view.as_view()),
]
