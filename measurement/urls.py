from django.urls import path
from .views import measurementView, itemTypeView, measurementDetailView

urlpatterns = [
    path("", measurementView.as_view(), name="measurement"),
    path('<int:id>', measurementDetailView.as_view(), name="measurement-detail"),
    path("item/type", itemTypeView.as_view(), name="item-types"),
]