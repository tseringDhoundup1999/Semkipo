from django.urls import path 
from .views import create_contact_view,update_name_view

urlpatterns = [
    path("contact/create",create_contact_view.as_view()),
    path("name/update",update_name_view.as_view()),
]
