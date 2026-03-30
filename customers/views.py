from django.shortcuts import render

from django.conf import settings
# ==== rest_framework ============#
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework import status

from .models import Customer
from .serializers import contactSerializers,customerNameSerializer

# constants
from core.constants.response_message import SuccessMessages,ErrorMessages,GeneralMessages
from core.constants.response_code import ResponseCodes
from core.utils.api_response import error_response, success_response



# Create your views here.


class create_contact_view(APIView):
     
    """
     API view to create a customer contact. 
     - if the contact does not exits, create new customer.
     - if the contact already exits, return existing customer info.
    """   
    def post(self,request):
        try:
            serializer = contactSerializers(data=request.data)
            if serializer.is_valid(raise_exception=True):
                contact = serializer.validated_data.get("contact")
                # check the contact exist and return the name and id 
                customer,created = Customer.objects.get_or_create(contact=contact)
                
                # if the customer is created newly
                if created:
                    return Response(success_response(SuccessMessages.CUSTOMER_CREATED_MESSAGE,ResponseCodes.CUSTOMER_CREATED,data={
                        "customer_id":customer.id,
                        "customer_name":customer.name
                    }),status=status.HTTP_201_CREATED)
                
                return Response(success_response(SuccessMessages.CUSTOMER_ALREADY_EXISTS, ResponseCodes.CUSTOMER_ALREADY_EXISTS, {
                    "customer_id":customer.id,
                    "customer_name":customer.name
                }), status=status.HTTP_200_OK)

                    
        #  handle validation error 
        except ValidationError as validation_error:
            return Response(error_response(GeneralMessages.VALIDATION_ERROR_MESSAGE,ResponseCodes.VALIDATION_ERROR,validation_error.detail)
                ,status=status.HTTP_400_BAD_REQUEST
            )
            
        except Exception as err:
            print(err)
            return Response(error_response(GeneralMessages.SERVER_ERROR_MESSAGE,ResponseCodes.SERVER_ERROR,None,err),status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
        

class update_name_view(APIView):
    
    def patch(self,request):
        """
            API View to update a customer's name using their contact number.
            Method: PATCH
            {
                "contact": "98XXXXXXXX",
                "name": "New Name"
            }
        """
        try:
            serializer = customerNameSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            contact = serializer.validated_data.get("contact")
            name = serializer.validated_data.get("name")
            
            customer = Customer.objects.filter(contact=contact).first()
            
            if not customer: 
                return Response(error_response(ErrorMessages.CUSTOMER_DOES_NOT_EXIST,ResponseCodes.CUSTOMER_DOES_NOT_EXIST,None),status=status.HTTP_404_NOT_FOUND)
            
            customer.name = name
            customer.save(update_fields=["name","updated_at"])
            
            return Response(success_response(SuccessMessages.CUSTOMER_UPDATE_NAME,ResponseCodes.CUSTOMER_NAME_UPDATED,{
                "customer_id":customer.id,
                "customer_name":customer.name,
                "customer_contact":customer.contact
            }),status=status.HTTP_200_OK)
        
        except ValidationError as validation_error:
            return Response(error_response(GeneralMessages.VALIDATION_ERROR_MESSAGE,ResponseCodes.VALIDATION_ERROR,validation_error.detail)
                ,status=status.HTTP_400_BAD_REQUEST
            )
        
        except Exception as err:
            print(err)
            return Response(error_response(GeneralMessages.SERVER_ERROR_MESSAGE,ResponseCodes.SERVER_ERROR,None,err),status=status.HTTP_500_INTERNAL_SERVER_ERROR)
         
        
    
        


