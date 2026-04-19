from django.urls import path
from .views import place_order_view

urlpatterns = [
    path("place-order",place_order_view.as_view()),
]
