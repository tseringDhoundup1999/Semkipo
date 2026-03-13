from django.urls import path 
from .views import RegisterView, LoginView, LogoutView,VerifyEmailView

app_name = "accounts"
urlpatterns = [
    path("register/",RegisterView.as_view()),
    path("login/",LoginView.as_view()),
    path("logout/",LogoutView.as_view(),name="token_blacklist"),
    path("verify-email/<uidb64>/<token>/",VerifyEmailView.as_view(),name="verify_email"),
]
