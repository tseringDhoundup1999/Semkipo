from urllib import response

from django.utils import timezone 
from django.shortcuts import render
from django.http import HttpResponse

# ==== auth related modules ======= #
from django.contrib.auth import authenticate


# --------   serializer  ----------------------------------------
from .serializers import RegisterSerializer,loginSerializer


# ==== rest_framwork modules ====== #
from rest_framework_simplejwt.views import TokenObtainPairView,TokenBlacklistView
from rest_framework import status 
from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework.exceptions import ValidationError as DRFValidationError


from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from django.shortcuts import redirect
from datetime import  timedelta
from django.utils import timezone 
import logging 
from django.core.exceptions import ValidationError as DjangoValidationError

# logg
import logging
from django.conf import settings


logger = logging.getLogger(__name__)


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


class LoginView(APIView):
    """
    API view to handle user login.
    Accepts email and password, validates the user, checks email verification,
    and returns JWT tokens if successful.
    """
    
    def post(self,request):
        try:
            # ------------------------------
            # 1️Validate incoming request
            # ------------------------------
            serializer = loginSerializer(data = request.data)
            if serializer.is_valid(raise_exception=True):
                email = serializer.validated_data.get("email")
                password = serializer.validated_data.get("password")
                
                # ------------------------------
                # 2️ Authenticate user
                # ------------------------------
                # Note: authenticate() returns None if credentials are wrong
                user = authenticate(email=email,password=password)
                
                
                # ------------------------------
                # 3️ Handle invalid credentials
                # ------------------------------
                if user is None:
                    return Response(
                        {
                            "success":False,
                            "message":"Invalid credentials. Please check your email and password.",
                            "code":"INVALID_CREDENTIALS"
                        },
                        status=status.HTTP_401_UNAUTHORIZED)
                
                
                
                # ------------------------------
                # 4 Check if email is verified
                # ------------------------------
                if not user.is_verified:
                    return Response(
                        {   "success":False,
                            "message":"Please verify your email before logging in.",
                            "code":"EMAIL_NOT_VERIFIED"
                        },
                        status=status.HTTP_403_FORBIDDEN)
                
                # ------------------------------
                # 5 Generate JWT tokens
                # ------------------------------
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                
                # ------------------------------
                # 6 Handle invalid credentials
                # ------------------------------
                return Response(
                    {
                        "success":True,
                        "message":"Login successful! Welcome back.",
                        "code":"LOGIN_SUCCESS",
                        "data":{
                            "access_token":access_token,
                            "refresh_token":refresh_token,
                            "user":{
                                "id":user.id,
                                "username":user.username,
                                "email":user.email
                            }
                        },
                     },
                    status=status.HTTP_200_OK
                )
                
        # ------------------------------
        # 7️ Handle serializer validation errors
        # ------------------------------
        except DRFValidationError as validation_error:
            return Response(
                {   
                    "success":False,
                    "message":"Validation failed!",
                    "code":"VALIDATION_ERROR",
                    "errors":validation_error.detail
                },
                status=status.HTTP_400_BAD_REQUEST
                )
        # ------------------------------
        # 8 Handle serializer validation errors
        # ------------------------------
        except Exception as err:
            logger.exception("Unexpected error during login")
            response_data = {
                    "success":False,
                    "message":"Something went wrong on the server. please try again later.",
                    "code":"SERVER_ERROR"
                }
            if settings.DEBUG:
               response_data["debug"] = str(err) # only in development 

            return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

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

        except (TypeError,ValueError,OverflowError,DRFValidationError):
            return Response(
                {"success": False,
                 "message": "The verification link appears to be invalid. Please check the link or request a new verification email."},
                status=400
            )
        except User.DoesNotExist:
            return Response(
                {"success":False,"message":"We could not find an account with this link. Please check the link or register again."},
                status=404
            )
        except Exception as e:
            logger.exception("Unexpected error",e)
            return Response(
               {"success":False,"message":"Something went wrong. Please try again later."},
                status=500
            )
        
        # ------------ handle link expire ------------------------------------
        if self._is_link_expired(user):
            return Response(
                {"success": False, "message": "This verification link has expired. Please request a new verification email to continue."},
                status=410
            )
        # ------------- Token invalid --------------------------------------- 
        if not default_token_generator.check_token(user,token):
            return Response(
                {"success": False, "message": "This verification token is invalid or has been tampered with. Please request a new verification email."},
                status=400
            )
        # ---------- check if email is already verified --------------------
        if user.is_verified:
            return Response(
                {"success": True, "message": "Your email is already verified. You can now log in and enjoy our services."},
                status=200
            )
            
        # ------------ Save Users -------------------------------------
        
        try:
            user.is_verified = True
            user.email_verification_sent_at = None  
            user.save(update_fields=['is_verified',"email_verification_sent_at"])

        except Exception as e:
            logger.exception("DB error while verifying user_id=%s", user.pk,e)
            return Response(
                {"success": False, "message": "We couldn’t complete your email verification. Please try again in a few minutes."},
                status=500
                )
            # ------------ Success -----------------------------------------------
        return Response(
            {"success": True, "message": "Your email has been verified successfully! You can now log in and start using your account."},
            status=200
        )        


      
    def _is_link_expired(self,user):
        if not user.email_verification_sent_at:
            return True 
        expiry = user.email_verification_sent_at + timedelta(minutes=self.VERIFICATION_TIMEOUT_MINUTES)
        return timezone.now() > expiry



class resend_email_verification_view(APIView):

    def post(self,request):
        print(request.user)
        return Response({"message":"Verification email send successfully !"},status=200)

