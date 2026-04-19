from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# models
from customers.models import Customer
from .models import Order,OrderItem
from measurement.models import ItemType
# serializer 
from .serializers import OrderSerializer
# Create your views here.
from decimal import Decimal

# messages
from core.utils.api_response import error_response,success_response
from core.constants.response_code import ResponseCodes
from core.constants.response_message import GeneralMessages,SuccessMessages,ErrorMessages

class place_order_view(APIView):
    
    def post(self,request):
        try:
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                
                print(serializer.validated_data)
                customer = serializer.validated_data.get('customer')
                delivery = serializer.validated_data.get('delivery')
                
                items = serializer.validated_data.get('items')
                
                
                customer_from_db = Customer.objects.filter(pk=customer['id']).first()
                delivery_type = Order.DeliveryChoice.PICKUP
                DELIVERY_TYPE_MAP = {
                    "PICKUP":Order.DeliveryChoice.PICKUP,
                    "DELIVERY":Order.DeliveryChoice.PICKUP,
                }
        
                delivery_type = DELIVERY_TYPE_MAP.get(delivery.get('type'),Order.DeliveryChoice.PICKUP)
                payment_status = Order.PaymentChoice.UNPAID
                if serializer.validated_data.get('payment'):
                    payment_status = Order.PaymentChoice.PAID,
                
                # create a order 
                order = Order.objects.create(
                    customer = customer_from_db,
                    delivery_type= delivery_type,
                    
                    delivery_address = delivery.get('address',""),
                    delivery_charge = delivery.get('amount',0),
                    payment_status= payment_status,
                
                )
                # get item type 
                total_itemOrder_price= 0
                for item in items:
                    # print(item)
                    measurement_item = ItemType.objects.filter(id=item.get('item_id')).first()
                    order_item = OrderItem.objects.create(
                        order = order,
                        measurement_type = measurement_item,
                        quantity = item.get('quantity')
                        
                    )
                    total_itemOrder_price += order_item.price 
                
                # update the order total price 
                # add delivery charge
                total_itemOrder_price = Decimal(total_itemOrder_price) + Decimal(order.delivery_charge)
                
                # apply discount
                discount_amount = Decimal(total_itemOrder_price) * (Decimal(order.discount) / Decimal(100))
                total_itemOrder_price = total_itemOrder_price - discount_amount
                
                # save final total
                order.total_price = total_itemOrder_price
                order.save()
            
            # order_serializer = OrderSerializer(order).data
            return Response(
                success_response(
                    SuccessMessages.ORDER_CREATED_MESSAGE,
                    ResponseCodes.ORDER_CREATED)
                ,status=status.HTTP_201_CREATED
                )
        except Exception as e:
            print(e)
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)