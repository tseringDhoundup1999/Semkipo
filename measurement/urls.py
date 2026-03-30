from django.urls import path
from .views import MeasurementView, ItemTypeView

urlpatterns = [
    path("", MeasurementView.as_view(), name="measurement"),
    path("/item/type", ItemTypeView.as_view(), name="item-types"),
]