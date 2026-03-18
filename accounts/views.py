from urllib import response

from django.utils import timezone 
from django.shortcuts import render
from django.http import HttpResponse

from rest_framework.views import APIView 
from rest_framework.response import Response 
from .serializers import RegisterSerializer 

from rest_framework_simplejwt.views import TokenObtainPairView,TokenBlacklistView
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.tokens import RefreshToken 
from django.shortcuts import redirect

# ---------
class RegisterView(APIView):
    def post(self,request):
        serializer = RegisterSerializer(data=request.data,context={"request":request})

        if serializer.is_valid():
            user = serializer.save()

            # generates JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            return Response({
                "message":"User created successfully",
                "refresh_token":refresh_token,
                "access_token":access_token,
                },status=200)
        return Response(serializer.errors,status=400)


class LoginView(TokenObtainPairView):
    pass 
    

class LogoutView(TokenBlacklistView):
    pass 

#  verify the email 

User = get_user_model()
class VerifyEmailView(APIView):
    def get(self,request,uidb64,token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid) 
        except (TypeError,ValueError,OverflowError,User.DoesNotExist):
            user = None 
        
        if user and default_token_generator.check_token(user,token):
            user.is_verified = True 
            user.save() 
            return Response({"message":"Email verified successfully"},status=200)        
        return Response({"error": "Invalid verification link"}, status=400)




class resend_email_verification_view(APIView):

    def post(self,request):
        print(request.user)
        return Response({"message":"Verification email send successfully !"},status=200)

