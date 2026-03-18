from django.urls import path 
from .views import RegisterView, LoginView, LogoutView,VerifyEmailView,resend_email_verification_view 

app_name = "accounts"
urlpatterns = [
    path("register/",RegisterView.as_view()),
    path("login/",LoginView.as_view()),
    path("logout/",LogoutView.as_view(),name="token_blacklist"),
    path("verify-email/<uidb64>/<token>/",VerifyEmailView.as_view(),name="verify_email"),
    path("resend-verification-email/",resend_email_verification_view.as_view(),name="resend_verification_email"),
    # path("change-email/",change_email,name="change_email"),
]
