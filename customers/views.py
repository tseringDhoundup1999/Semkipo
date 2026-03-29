from django.shortcuts import render

from django.conf import settings
# ==== rest_framework ============#
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework import status

from .models import Customer
from .serializers import contactSerializers

# constants
from core.constants.response_message import SERVER_ERROR_MESSAGE,VALIDATION_ERROR_MESSAGE
from core.constants.response_code import GENERAL_CODE, ResponseCodes



# Create your views here.


class create_contact_view(APIView):
        
    def post(self,request):
        try:
            serializer = contactSerializers(data=request.data)
            if serializer.is_valid(raise_exception=True):
                contact = serializer.validated_data.get("contact")
                # check the contact exist and return the name and id 
                customer,created = Customer.objects.get_or_create(contact=contact)
                
                # if the customer is created newly
                if created:
                    return Response({
                        "success":True,
                        "message":"Customer has been created successfully.",
                        "code":ResponseCodes.CUSTOMER_CREATED,
                        "data":{
                            "customer_id":customer.id,
                            "customer_name":customer.name
                        }
                    },status=status.HTTP_201_CREATED)
                # if the customer already exists
                return Response({
                    "success":True,
                    "code":ResponseCodes.CUSTOMER_ALREADY_EXISTS,
                    "message":"Customer already exists.",
                    "data":{
                        "customer_id":customer.id,
                        "customer_name":customer.name
                    }
                },status=status.HTTP_200_OK)
                    
        #  handle validation error 
        except ValidationError as validation_error:
            return Response(
                {
                    "success":False,
                    "code":ResponseCodes.VALIDATION_ERROR,
                    "message":VALIDATION_ERROR_MESSAGE,
                    "error":validation_error.detail,
                }
                ,status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as err:
            print(err)
            response_data = {
                    "success":False,
                    "code":ResponseCodes.SERVER_ERROR,
                    "message":SERVER_ERROR_MESSAGE,
                }
            if settings.DEBUG:
                response_data["debug"] = str(err) # only in development
            return Response(response_data,status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
        
