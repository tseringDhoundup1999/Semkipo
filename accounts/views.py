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
from datetime import datetime,timedelta
from django.utils import timezone 
import logging 
from django.core.exceptions import ValidationError 

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

logger = logging.getLogger(__name__)

User = get_user_model()
class VerifyEmailView(APIView):
    VERIFICATION_TIMEOUT_MINUTES = 2
    def get(self,request,uidb64,token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)

        except (TypeError,ValueError,OverflowError,ValidationError):
            return Response(
                {"success":False,"message":"Invalid verification link."},
                status=400
            )
        except User.DoesNotExist:
            return Response(
                {"success":False,"message":"Account not found."},
                status=404
            )
        except Exception as e:
            logger.exception("Unexpected error",e)
            return Response(
               {"success":False,"message":"Something went wrong. Please try again later."},
                status=500
            )
        
        # ------------- Token invalid --------------------------------------- 
        if not default_token_generator.check_token(user,token):
            return Response(
                {"message":"Invalid or tempered verification token."},
                status=400
            )
        # ---------- check if email is verified already --------------------
        if user.is_verified:
            return Response({"message":"Email is already verified."},status=200)
            
          
            # ------------ handle link expire ------------------------------------
        if self._is_link_expired(user):
            return Response(
                    {"message":"Verification link has expired. Please request a new one."},
                    status=410
                )
        # ------------ Save Users -------------------------------------
        
        try:
            user.is_verified = True
            user.email_verification_sent_at = None  
            user.save(update_fields=['is_verified',"email_verification_sent_at"])

        except Exception as e:
            logger.exception("DB error while verifying user_id=%s", user.pk,e)
            return Response(
                {"success":False,"message":"Could not complete the verification. Please try again later."},
                status=500
                )
            # ------------ Success -----------------------------------------------
        return Response({"success":True,"message":"Email verified successfully"},status=200)        


      
    def _is_link_expired(self,user):
        if not user.email_verification_sent_at:
            return True 
        expiry = user.email_verification_sent_at + timedelta(minutes=self.VERIFICATION_TIMEOUT_MINUTES)
        return timezone.now > expiry



class resend_email_verification_view(APIView):

    def post(self,request):
        print(request.user)
        return Response({"message":"Verification email send successfully !"},status=200)

