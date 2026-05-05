from django.urls import path 
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    ChangePasswordView,
    CompanySettingsView,
    LoginView,
    LogoutView,
    RegisterView,
)

app_name = "accounts"
urlpatterns = [
    path("register/",RegisterView.as_view()),
    path("login/",LoginView.as_view()),
    path("logout/",LogoutView.as_view(),name="token_blacklist"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("settings/", CompanySettingsView.as_view(), name="company_settings"),
    path("change-password/", ChangePasswordView.as_view(), name="change_password"),
]
