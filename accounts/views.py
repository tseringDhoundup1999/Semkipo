# ==== auth related modules ======= #
from django.contrib.auth import authenticate, update_session_auth_hash


# --------   serializer  ----------------------------------------
from .models import CompanySettings
from .serializers import (
    ChangePasswordSerializer,
    CompanySettingsSerializer,
    RegisterSerializer,
    loginSerializer,
)


# ==== rest_framwork modules ====== #
from rest_framework_simplejwt.views import TokenObtainPairView,TokenBlacklistView
from rest_framework import status 
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework_simplejwt.tokens import RefreshToken 
from rest_framework.exceptions import ValidationError as DRFValidationError


import logging 

# logg
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
                "success": True,
                "message":"Registration successful. Your account is under review and will be verified soon.",
                "code":"REGISTER_SUCCESS",
                "data": {
                    "access_token":access_token,
                    "refresh_token":refresh_token,
                    "user": {
                        "id": user.id,
                        "username": user.username,
                        "email": user.email,
                        "is_verified": user.is_verified,
                    },
                },
                },status=status.HTTP_201_CREATED)
        return Response(serializer.errors,status=400)


class LoginView(APIView):
    """
    API view to handle user login.
    Accepts email and password, validates the user, and returns JWT tokens.
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
                
                # Allow login only after admin/superuser verifies the account.
                if not user.is_verified:
                    return Response(
                        {
                            "success": False,
                            "message": "Your account is under review. Please wait for admin approval before logging in.",
                            "code": "ACCOUNT_NOT_VERIFIED",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )
                
                
                # ------------------------------
                # 4 Generate JWT tokens
                # ------------------------------
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)
                
                
                # ------------------------------
                # 5 Handle valid credentials
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


def get_company_settings():
    settings_obj, _ = CompanySettings.objects.get_or_create(pk=1)
    return settings_obj


class CompanySettingsView(APIView):
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]

        return [IsAuthenticated()]

    def get(self, request):
        serializer = CompanySettingsSerializer(get_company_settings())
        return Response(
            {
                "success": True,
                "message": "Company settings loaded.",
                "data": serializer.data,
            },
            status=status.HTTP_200_OK,
        )

    def patch(self, request):
        serializer = CompanySettingsSerializer(
            get_company_settings(),
            data=request.data,
            partial=True,
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Company settings updated.",
                    "data": serializer.data,
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "code": "VALIDATION_ERROR",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )


class ChangePasswordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={"request": request},
        )

        if serializer.is_valid():
            user = serializer.save()
            update_session_auth_hash(request, user)
            return Response(
                {
                    "success": True,
                    "message": "Password changed successfully.",
                },
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "message": "Validation failed.",
                "code": "VALIDATION_ERROR",
                "errors": serializer.errors,
            },
            status=status.HTTP_400_BAD_REQUEST,
        )
