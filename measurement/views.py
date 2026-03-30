from django.shortcuts import render

# === rest framework imports ===
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.validators import ValidationError

from .models import ItemType, MeasurementType
from .serializers import ItemTypeSerializer, MeasurementTypeSerializer

# utils 
from core.constants.response_code import ResponseCodes 
from core.constants.response_message import GeneralMessages, SuccessMessages, ErrorMessages
from core.utils.api_response import success_response, error_response

# Create your views here.


class MeasurementView(APIView):

    def get(self, request):
        try:
            measurements = MeasurementType.objects.all()  
            serializers =  MeasurementTypeSerializer(measurements, many=True)
            return Response(
                success_response(GeneralMessages.GET_SUCCESS_MESSAGE, ResponseCodes.RETRIEVE_SUCCESS, serializers.data)
                , status=status.HTTP_200_OK)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def post(self,request):
        try:
            serializer = MeasurementTypeSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            name = serializer.validated_data.get('name')
            
            if MeasurementType.objects.filter(name__iexact=name).exists():
                return Response(
                    success_response(ErrorMessages.MEASUREMENT_ALREADY_EXISTS, ResponseCodes.MEASUREMENT_ALREADY_EXISTS, None)
                    , status=status.HTTP_400_BAD_REQUEST)  
                
            MeasurementType.objects.create(name=name)
            return Response(
                    success_response(SuccessMessages.MEASUREMENT_TYPE_CREATED, ResponseCodes.MEASUREMENT_TYPE_CREATED, serializer.data)
                    , status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            return Response(
                error_response(GeneralMessages.VALIDATION_ERROR_MESSAGE, ResponseCodes.VALIDATION_ERROR, ve.detail, str(ve))
                , status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class ItemTypeView(APIView):

    def get(self, request):
        return Response({"message": "Item Type API is working!"}, status=status.HTTP_200_OK)