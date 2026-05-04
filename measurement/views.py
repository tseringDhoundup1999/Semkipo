from django.shortcuts import render

# === rest framework imports ===
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import ValidationError as DRFValidationError

from .models import ItemType, MeasurementType
from .serializers import ItemTypeSerializer, MeasurementTypeSerializer
from orders.models import OrderItem

# utils 
from core.constants.response_code import ResponseCodes 
from core.constants.response_message import GeneralMessages, SuccessMessages, ErrorMessages
from core.utils.api_response import success_response, error_response

# Create your views here.


class measurementView(APIView):

    """ 
        get - Retrieve all measurement types.
        post - Create a new measurement type.
            - if already exists, cancle the request  
    """
    def get(self, request):
        try:
            measurements = MeasurementType.objects.all()  
            serializer =  MeasurementTypeSerializer(measurements, many=True)
            return Response(
                success_response(GeneralMessages.GET_SUCCESS_MESSAGE, ResponseCodes.RETRIEVE_SUCCESS, serializer.data)
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
                    success_response(ErrorMessages.MEASUREMENT_ALREADY_EXISTS, ResponseCodes.MEASUREMENT_ALREADY_EXISTS, serializer.data)
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
    


class measurementDetailView(APIView):
    """ 
        get - Retrieve a measurement type by id.
    """
    def get(self, request, id):
        try:
            measurement = MeasurementType.objects.get(id=id)  
            serializer =  MeasurementTypeSerializer(measurement)
            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS, serializer.data)
                , status=status.HTTP_200_OK)
        
        except MeasurementType.DoesNotExist:
            return Response(
                error_response(ErrorMessages.MEASUREMENT_DOES_NOT_EXIST, ResponseCodes.DOES_NOT_EXIST, None, f"Measurement type with id {id} does not exist.")
                , status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, id):
        try:
            measurement = MeasurementType.objects.get(id=id)  
            if ItemType.objects.filter(measurement_type=measurement).exists():
                return Response(
                    error_response(
                        "This measurement unit is used by service items and cannot be deleted.",
                        ResponseCodes.VALIDATION_ERROR,
                        {
                            "measurement": [
                                "Delete or move related service items before deleting this unit."
                            ]
                        },
                    )
                    , status=status.HTTP_409_CONFLICT)

            measurement.delete()
            return Response(
                success_response(SuccessMessages.MEASUREMENT_DELETED, ResponseCodes.DELETED,None)
                , status=status.HTTP_200_OK)
        
        except MeasurementType.DoesNotExist:
            return Response(
                error_response(ErrorMessages.MEASUREMENT_DOES_NOT_EXIST, ResponseCodes.DOES_NOT_EXIST, None, f"Measurement type with id {id} does not exist.")
                , status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    


class itemTypeView(APIView):
    """ 
            get - Retrieve all item types.
            post - Create a new item type.
                - if already exists, cancle the request  
    """
    def get(self, request):
        try:
            items = ItemType.objects.all() 
            serializers = ItemTypeSerializer(items,many=True)
            return Response(
                success_response(GeneralMessages.GET_SUCCESS_MESSAGE, ResponseCodes.RETRIEVE_SUCCESS, serializers.data)
                , status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def post(self,request):
        try:
            serializer = ItemTypeSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    error_response(
                        GeneralMessages.VALIDATION_ERROR_MESSAGE,
                        ResponseCodes.VALIDATION_ERROR,
                        serializer.errors,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            item = serializer.save()
            
            return Response(
                    success_response(
                        SuccessMessages.ITEM_TYPE_CREATED,
                        ResponseCodes.MEASUREMENT_ITEM_TYPE_CREATED,
                        ItemTypeSerializer(item).data,
                    )
                    , status=status.HTTP_201_CREATED)
        except DRFValidationError as ve:
            return Response(
                error_response(GeneralMessages.VALIDATION_ERROR_MESSAGE, ResponseCodes.VALIDATION_ERROR, ve.detail, str(ve))
                , status=status.HTTP_400_BAD_REQUEST)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            


class itemTypeDetailView(APIView):
    """ 
        get - Retrieve an item type by id.
    """
    def get(self, request, id):
        try:
            item = ItemType.objects.get(id=id)  
            serializer =  ItemTypeSerializer(item)
            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS, serializer.data)
                , status=status.HTTP_200_OK)
        
        except ItemType.DoesNotExist:
            return Response(
                error_response(
                    ErrorMessages.MEASUREMENT_ITEM_TYPE_DOES_NOT_EXIST, 
                    ResponseCodes.DOES_NOT_EXIST,
                    None,
                    f"Item type with id {id} does not exist.")
                , status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def delete(self, request, id):
        try:
            item = ItemType.objects.get(id=id)  
            if OrderItem.objects.filter(measurement_type=item).exists():
                return Response(
                    error_response(
                        "This service item is used in existing orders and cannot be deleted.",
                        ResponseCodes.VALIDATION_ERROR,
                        {
                            "item": [
                                "Keeping it protects the service details on old orders."
                            ]
                        },
                    )
                    , status=status.HTTP_409_CONFLICT)

            item.delete()
            return Response(
                success_response(
                    SuccessMessages.MEASUREMENT_ITEM_TYPE_DELETED,
                    ResponseCodes.DELETED,
                    None
                )
                , status=status.HTTP_200_OK)
        
        except ItemType.DoesNotExist:
            return Response(
                error_response(
                    ErrorMessages.MEASUREMENT_DOES_NOT_EXIST,
                    ResponseCodes.DOES_NOT_EXIST,
                    None,
                    f"Item type with id {id} does not exist.")
                , status=status.HTTP_404_NOT_FOUND)
        
        except Exception as e:
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
