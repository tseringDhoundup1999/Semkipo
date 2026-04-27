from django.urls import path
from .views import place_order_view,Orders

urlpatterns = [
    path("", Orders.as_view()),
    path("place-order",place_order_view.as_view()),
]
