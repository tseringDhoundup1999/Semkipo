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

import time 
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator



class Create_order(APIView):
    
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
    WEEK_STRING = "this_week"
    MONTH_STRING = "this_month"
    YEAR_STRING= "this_year"
    TODAY_STRING = "today"
    
    OBJECT_LIMIT = 10
    
    
    def clean_data(self,value):
        if value is None:
            return None

        value = str(value).strip()

        if value.lower() in ['undefined', 'null', '']:
            return None

        return value
    
    def get_today_range(self):
        now = timezone.now()
        today_date = now.replace(hour=0,minute=0,second=0,microsecond=0)
        today_end_date =today_date + timedelta(days=1)
        return  today_date,today_end_date
    
    def get_this_month_range(self):
        now = timezone.now()
        start_month = now.replace(day=1,hour=0,minute=0,second=0,microsecond=0)
        if now.month == 12:
            end_month = start_month.replace(year=start_month.year+1,month=1)
        else:
            end_month = start_month.replace(month=now.month+1)
        return start_month,end_month
    
    def get_this_week_range(self):
        now = timezone.now()

        # Start of today (00:00)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

        # Python: Monday=0 ... Sunday=6
        # Convert so Sunday becomes 0
        days_since_sunday = (today_start.weekday() + 1) % 7

        # Start of week (Sunday)
        start_of_week = today_start - timedelta(days=days_since_sunday)

        # End of week (next Sunday)
        end_of_week = start_of_week + timedelta(days=7)

        return start_of_week, end_of_week
    
    def get_this_year_range(self):
        now = timezone.now()
        
        start_year = now.replace(month=1,day=1,hour=0,minute=0,second=0,microsecond=0)
        end_year = start_year.replace(year=now.year+1)
        
        return start_year,end_year
        
        
        
        
    def get(self,request):
        time.sleep(1)
        try:
            # --------------- CLEAN INPUT ------------------
            status_key = self.clean_data(request.GET.get('status'))
            payment_key = self.clean_data(request.GET.get('payment_status'))
            search = self.clean_data(request.GET.get('search'))
            sort = self.clean_data(request.GET.get('sort'))
            from django.utils.dateparse import parse_datetime
            date_from =self.clean_data( request.GET.get('date_from'))
            date_to = self.clean_data(request.GET.get('date_to'))
            quick_date = self.clean_data(request.GET.get('quick_date'))
            page_num = self.clean_data(request.GET.get('page'))
            
            
            # -------------- MAPPING --------------------------
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
            SORT_MAPPING = {
                'date-desc': '-created_at',
                'date-asc': 'created_at',
                'amount-asc': 'total_price',
                'amount-desc': '-total_price',
            }
            
            
            
            # ----------- BASE QUERY ------------------
            orders = Order.objects.all()
            
            
            # --------- SEARCH FILTER ---------------------------
            if search:
                orders = orders.filter(customer__name__icontains=search) 
                
                
                
            # --------- STATUS FILTER -------------------------------
            order_status = ORDER_STATUS_MAPPING.get(status_key)
            if order_status is not None:
                orders = orders.filter(status =order_status) 
            
            payment_status = PAYMENT_STATUS_MAPPING.get(payment_key)
            if payment_status is not None:
                orders = orders.filter(payment_status=payment_status)
            
            #------------ DATE RANGE FILTER -------------------------
            if date_from:
                date_from = parse_datetime(date_from)
                orders = orders.filter(created_at__gte=date_from)
            
            if date_to:
                date_to = parse_datetime(date_to)
                orders = orders.filter(created_at__lte=date_to)
            
            
            # ----------- SORTING -----------
            if sort in SORT_MAPPING:
                orders = orders.order_by(SORT_MAPPING[sort])
            else:
                orders = orders.order_by('-created_at')  # default

            
            # ----------- QUICK DATE FILTER -----------
            if quick_date:
                if quick_date == self.TODAY_STRING:
                    start, end = self.get_today_range()

                elif quick_date == self.WEEK_STRING:
                    start, end = self.get_this_week_range()

                elif quick_date == self.MONTH_STRING:
                    start, end = self.get_this_month_range()

                elif quick_date == self.YEAR_STRING:
                    start, end = self.get_this_year_range()

                else:
                    start = end = None
                if start and end:
                    orders = orders.filter(created_at__gte=start, created_at__lt=end)

            # ------------ PAGINATION ----------------------------
            paginator = Paginator(orders,self.OBJECT_LIMIT)
            try:
                page_num = int(page_num)
            except (TypeError, ValueError):
                page_num = 1
            page_obj = paginator.get_page(page_num or 1)
            
            # ----------- SERIALIZE ------------------------------     
            order_data = OrderResponseSerializer(page_obj, many=True).data
            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS,
                  
                    data={
                        "count": paginator.count,
                        "total_pages": paginator.num_pages,
                        "current_page": page_obj.number,
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
        
        



class Delete_order(APIView):
    def delete(self,request,id):
        try:
            order = get_object_or_404(Order,pk=id)
            order.delete()
            return Response(
                success_response(
                    SuccessMessages.DELETE_ORDER,
                    ResponseCodes.DELETED,      
                   )
                ,status=status.HTTP_204_NO_CONTENT
                )
        except Order.DoesNotExist:
            return Response(
                error_response(
                    GeneralMessages.DOES_NOT_EXIST_MESSAGE,
                    ResponseCodes.DOES_NOT_EXIST,      
                   )
                ,status=status.HTTP_404_NOT_FOUND
                )
            
        except Exception as e:
            print(e)
            return Response(
                error_response(GeneralMessages.SERVER_ERROR_MESSAGE, ResponseCodes.SERVER_ERROR, None, str(e))
                , status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        