from django.shortcuts import render

from rest_framework.views import APIView 
from rest_framework.response import Response 
from .serializers import RegisterSerializer 

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from django.contrib.auth import authenticate

class RegisterView(APIView):


    def post(self,request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message":"User created successfully"},status=200)
        return Response(serializer.errors,status=400)


class LoginView(TokenObtainPairView):
    pass 
    

