from django.shortcuts import render

from rest_framework.views import APIView 
from rest_framework.response import Response 
from .serializers import RegisterSerializer 


class RegisterView(APIView):


    def post(self,request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({"message":"User created successfully"},status=200)
        return Response(serializer.errors,status=400)