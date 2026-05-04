from django.urls import path
from .views import (
    Create_order,
    Dashboard,
    Orders,
    Delete_order,
    Update_order,
    PromotionRules,
    PromotionRuleDetail,
)

urlpatterns = [
    path("", Orders.as_view()),
    path("dashboard", Dashboard.as_view()),
    path("place-order",Create_order.as_view()),
    path("update/<int:id>",Update_order.as_view()),
    path("delete/<int:id>",Delete_order.as_view()),
    path("promotions/", PromotionRules.as_view()),
    path("promotions/<int:id>/", PromotionRuleDetail.as_view()),
]
