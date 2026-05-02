from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# models
from customers.models import Customer
from .models import Order,OrderItem
from measurement.models import ItemType
# serializer 
from .serializers import OrderSerializer,OrderResponseSerializer
# Create your views here.
from decimal import Decimal
from django.http import Http404

# messages
from core.utils.api_response import error_response,success_response
from core.constants.response_code import ResponseCodes
from core.constants.response_message import GeneralMessages,SuccessMessages,ErrorMessages

from django.db import transaction


class place_order_view(APIView):
    
    def post(self,request):
        try:
            serializer = OrderSerializer(data=request.data)
            if serializer.is_valid():
                
                customer = serializer.validated_data.get('customer')
                delivery = serializer.validated_data.get('delivery','PICKUP')
                items = serializer.validated_data.get('items',[])
                
                # handle customer not found 
                try:
                    customer_from_db = get_object_or_404(Customer,pk=customer['id'])  
                                     
                except Http404:
                    return Response(error_response(
                        GeneralMessages.CUSTOMER_NOT_FOUND,
                        ResponseCodes.CUSTOMER_NOT_FOUND,
                        ),status=status.HTTP_404_NOT_FOUND)
                
                with transaction.atomic():
                        # delivery type 
                    DELIVERY_TYPE_MAP = {
                        "PICKUP":Order.DeliveryChoice.PICKUP,
                        "DELIVERY":Order.DeliveryChoice.DELIVERY,
                    }
                    delivery_type = DELIVERY_TYPE_MAP.get(delivery.get('type'),Order.DeliveryChoice.PICKUP)
                    
                    # payment type  
                    # first set the payment_status to unpaid
                    payment_status = Order.PaymentChoice.UNPAID
                    if serializer.validated_data.get('payment'): #check payment is paid (true,false)
                        payment_status = Order.PaymentChoice.PAID  #if payment is true then set the payment status to "PAID"
                    
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
                    
                    order_data = OrderResponseSerializer(order).data
            
            
            return Response(
                success_response(
                    SuccessMessages.ORDER_CREATED_MESSAGE,
                    ResponseCodes.ORDER_CREATED,
                    data={
                        'order':order_data,
                    })
                ,status=status.HTTP_201_CREATED
                )
        except Exception as e:
            print(e)
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            


class Orders(APIView):
    
    def clean_data(self,value):
        if value is None:
            return None

        value = str(value).strip()

        if value.lower() in ['undefined', 'null', '']:
            return None

        return value
        
    def get(self,request):
        try:
            query = request.GET
            # order_status = request.GET.get('status','all')
            status_key = self.clean_data(request.GET.get('status'))
            payment_key = self.clean_data(request.GET.get('payment_status'))
            search = self.clean_data(request.GET.get('search'))
            sort = self.clean_data(request.GET.get('sort'))
            date_from =self.clean_data( request.GET.get('date_from'))
            date_to = self.clean_data(request.GET.get('date_to'))
            
            # order status mapping 
            ORDER_STATUS_MAPPING = {
                'in_progress':Order.StatusChoice.IN_PROGRESS,
                'pending':Order.StatusChoice.PENDING,
                'completed':Order.StatusChoice.COMPLETED,
                'cancelled':Order.StatusChoice.CANCELLED
                
            }
            PAYMENT_STATUS_MAPPING = {
                'paid':Order.PaymentChoice.PAID,
                'unpaid':Order.PaymentChoice.UNPAID
            }
            
            order_status = ORDER_STATUS_MAPPING.get(status_key)
            payment_status = PAYMENT_STATUS_MAPPING.get(payment_key)
            print(payment_status)

            orders = Order.objects.all()
            if order_status is not None:
                print(order_status)
                orders = orders.filter(status =order_status) 
            
            if date_from:
                orders = orders.filter(created_at__gte=date_from)
            
            if date_to:
                orders = orders.filter(created_at__lte=date_to)

            
            # sort 
            if sort:
                if sort =='date-desc':
                    orders = orders.order_by('-created_at')
                elif sort == 'date-asc':
                    orders = orders.order_by('created_at')
                elif sort == "amount-asc":
                    orders = orders.order_by('total_price')
                elif sort == "amount-desc":
                    orders = orders.order_by('-total_price')

            # sort by payment type 
            if payment_status:
                orders = orders.filter(payment_status=payment_status)
                    
            
           
               
            
            
            order_data = OrderResponseSerializer(orders, many=True).data
            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS,
                    data={
                        'orders':order_data
                    }
                   )
                ,status=status.HTTP_200_OK
                )
            
            
        except Exception as e:
            print(e)
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        