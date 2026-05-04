from django.shortcuts import render,get_object_or_404
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

# models
from customers.models import Customer
from .models import Order,OrderItem,PromotionRule
# serializer 
from .serializers import (
    OrderSerializer,
    OrderResponseSerializer,
    OrderUpdateSerializer,
    PromotionRuleSerializer,
)
# Create your views here.
from decimal import Decimal
from django.http import Http404
from django.core.exceptions import ValidationError as DjangoValidationError

# messages
from core.utils.api_response import error_response,success_response
from core.constants.response_code import ResponseCodes
from core.constants.response_message import GeneralMessages,SuccessMessages,ErrorMessages

from django.db import transaction
from django.db.models import Count, DecimalField, Max, Sum, Value
from django.db.models.functions import Coalesce, TruncDate

import time 
from django.utils import timezone
from datetime import timedelta
from django.utils.dateparse import parse_datetime
from django.core.paginator import Paginator



class Create_order(APIView):
    
    def post(self,request):
        try:
            serializer = OrderSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    error_response(
                        GeneralMessages.VALIDATION_ERROR_MESSAGE,
                        ResponseCodes.VALIDATION_ERROR,
                        serializer.errors,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

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
                total_item_quantity = Decimal("0.00")
                order_items = []
                for item in items:
                    order_item = OrderItem.objects.create(
                        order = order,
                        measurement_type = item.get("item_obj"),
                        quantity = item.get('quantity')
                        
                    )
                    order_items.append(order_item)
                    total_itemOrder_price += order_item.price 
                    total_item_quantity += Decimal(str(order_item.quantity))

                applied_promotion = None
                promotion_discount_amount = Decimal("0.00")
                active_promotion = PromotionRule.objects.filter(is_active=True).first()
                customer_current_wash_count = Decimal(
                    str(customer_from_db.loyalty_wash_count or 0)
                )

                if active_promotion and active_promotion.is_currently_applicable():
                    if active_promotion.rule_type == PromotionRule.RuleType.DISCOUNT:
                        discount_percent = Decimal(
                            str(active_promotion.discount_percent or 0)
                        )
                        promotion_discount_amount = (
                            Decimal(total_itemOrder_price) * discount_percent / Decimal("100")
                        )
                        applied_promotion = active_promotion

                    if active_promotion.rule_type == PromotionRule.RuleType.LOYALTY:
                        required_qty = Decimal(
                            str(active_promotion.required_wash_count or 0)
                        )
                        free_qty = Decimal(str(active_promotion.free_wash_count or 0))
                        next_wash_count = customer_current_wash_count + total_item_quantity

                        if required_qty > 0 and next_wash_count >= required_qty and order_items:
                            cheapest_unit_rate = min(
                                Decimal(str(item.measurement_type.price_per_unit or 0))
                                for item in order_items
                            )
                            promotion_discount_amount = cheapest_unit_rate * free_qty
                            applied_promotion = active_promotion
                            customer_from_db.loyalty_wash_count = Decimal("0.00")
                        else:
                            customer_from_db.loyalty_wash_count = next_wash_count
                    else:
                        customer_from_db.loyalty_wash_count = (
                            customer_current_wash_count + total_item_quantity
                        )
                else:
                    customer_from_db.loyalty_wash_count = (
                        customer_current_wash_count + total_item_quantity
                    )
                
                # update the order total price 
                # add delivery charge
                total_itemOrder_price = Decimal(total_itemOrder_price) + Decimal(order.delivery_charge)
                
                if promotion_discount_amount:
                    total_itemOrder_price = total_itemOrder_price - promotion_discount_amount
                    if total_itemOrder_price < 0:
                        total_itemOrder_price = Decimal("0.00")

                # apply discount
                discount_amount = Decimal(total_itemOrder_price) * (Decimal(order.discount) / Decimal(100))
                total_itemOrder_price = total_itemOrder_price - discount_amount
                
                # save final total
                order.total_price = total_itemOrder_price
                order.save()
                customer_from_db.save(update_fields=["loyalty_wash_count", "updated_at"])
                
                order_data = OrderResponseSerializer(order).data
            
            
            return Response(
                success_response(
                    SuccessMessages.ORDER_CREATED_MESSAGE,
                    ResponseCodes.ORDER_CREATED,
                    data={
                        'order':order_data,
                        "promotion": {
                            "id": applied_promotion.id,
                            "name": applied_promotion.name,
                            "rule_type": applied_promotion.rule_type,
                            "discount_amount": f"{promotion_discount_amount:.2f}",
                        } if applied_promotion else None,
                    })
                ,status=status.HTTP_201_CREATED
                )
        except DjangoValidationError as validation_error:
            return Response(
                error_response(
                    GeneralMessages.VALIDATION_ERROR_MESSAGE,
                    ResponseCodes.VALIDATION_ERROR,
                    validation_error.message_dict or validation_error.messages,
                ),
                status=status.HTTP_400_BAD_REQUEST,
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

    def get_status_counts(self, orders):
        counts = {
            'all': orders.count(),
            Order.StatusChoice.PENDING: 0,
            Order.StatusChoice.IN_PROGRESS: 0,
            Order.StatusChoice.COMPLETED: 0,
            Order.StatusChoice.CANCELLED: 0,
        }

        status_totals = (
            orders.order_by()
            .values('status')
            .annotate(total=Count('id'))
        )
        for status_total in status_totals:
            counts[status_total['status']] = status_total['total']

        return counts
    
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

            status_counts = self.get_status_counts(orders)

            # --------- STATUS FILTER -------------------------------
            order_status = ORDER_STATUS_MAPPING.get(status_key)
            if order_status is not None:
                orders = orders.filter(status =order_status) 

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
                        "status_counts": status_counts,
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
        
        
        


class Dashboard(APIView):
    RECENT_ORDER_LIMIT = 5
    TOP_LIMIT = 5

    def format_money(self, value):
        return f"{Decimal(value or 0):.2f}"

    def format_decimal(self, value):
        return f"{Decimal(value or 0):.2f}"

    def get_status_counts(self, orders):
        counts = {
            "all": orders.count(),
            Order.StatusChoice.PENDING: 0,
            Order.StatusChoice.IN_PROGRESS: 0,
            Order.StatusChoice.COMPLETED: 0,
            Order.StatusChoice.CANCELLED: 0,
        }

        for row in orders.order_by().values("status").annotate(total=Count("id")):
            counts[row["status"]] = row["total"]

        return counts

    def get_choice_counts(self, orders, field, choices):
        counts = {choice.value: 0 for choice in choices}

        for row in orders.order_by().values(field).annotate(total=Count("id")):
            counts[row[field]] = row["total"]

        return counts

    def get_metric_change(self, current_value, previous_value):
        current = Decimal(current_value or 0)
        previous = Decimal(previous_value or 0)

        if previous == 0:
            return None if current == 0 else 100

        change = ((current - previous) / previous) * Decimal(100)
        return round(change, 1)

    def get(self, request):
        try:
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            tomorrow_start = today_start + timedelta(days=1)
            week_start = today_start - timedelta(days=6)
            previous_week_start = week_start - timedelta(days=7)
            last_30_days = now - timedelta(days=30)
            month_start = today_start.replace(day=1)

            orders = Order.objects.select_related("customer").prefetch_related(
                "items__measurement_type",
            )
            order_items = OrderItem.objects.select_related(
                "order",
                "measurement_type",
                "measurement_type__measurement_type",
            )

            money_field = DecimalField(max_digits=12, decimal_places=2)
            quantity_field = DecimalField(max_digits=12, decimal_places=2)

            total_revenue = orders.aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0.00")),
                    output_field=money_field,
                ),
            )["total"]
            today_revenue = orders.filter(
                created_at__gte=today_start,
                created_at__lt=tomorrow_start,
            ).aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0.00")),
                    output_field=money_field,
                ),
            )["total"]
            month_revenue = orders.filter(created_at__gte=month_start).aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0.00")),
                    output_field=money_field,
                ),
            )["total"]
            unpaid_amount = orders.filter(
                payment_status=Order.PaymentChoice.UNPAID,
            ).aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0.00")),
                    output_field=money_field,
                ),
            )["total"]
            current_week_revenue = orders.filter(created_at__gte=week_start).aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0.00")),
                    output_field=money_field,
                ),
            )["total"]
            previous_week_revenue = orders.filter(
                created_at__gte=previous_week_start,
                created_at__lt=week_start,
            ).aggregate(
                total=Coalesce(
                    Sum("total_price"),
                    Value(Decimal("0.00")),
                    output_field=money_field,
                ),
            )["total"]

            total_orders = orders.count()
            today_orders = orders.filter(
                created_at__gte=today_start,
                created_at__lt=tomorrow_start,
            ).count()
            current_week_orders = orders.filter(created_at__gte=week_start).count()
            previous_week_orders = orders.filter(
                created_at__gte=previous_week_start,
                created_at__lt=week_start,
            ).count()
            active_orders = orders.filter(
                status__in=[
                    Order.StatusChoice.PENDING,
                    Order.StatusChoice.IN_PROGRESS,
                ],
            ).count()

            trend_rows = (
                orders.filter(created_at__gte=week_start)
                .annotate(day=TruncDate("created_at"))
                .values("day")
                .annotate(
                    order_count=Count("id"),
                    revenue=Coalesce(
                        Sum("total_price"),
                        Value(Decimal("0.00")),
                        output_field=money_field,
                    ),
                )
                .order_by("day")
            )
            trend_map = {row["day"]: row for row in trend_rows}
            revenue_trend = []
            for index in range(7):
                day = (week_start + timedelta(days=index)).date()
                row = trend_map.get(day, {})
                revenue_trend.append(
                    {
                        "date": day.isoformat(),
                        "label": day.strftime("%a"),
                        "order_count": row.get("order_count", 0),
                        "revenue": self.format_money(row.get("revenue")),
                    }
                )

            top_customers = []
            customer_rows = (
                orders.filter(customer__isnull=False)
                .values("customer_id", "customer__name", "customer__contact")
                .annotate(
                    order_count=Count("id"),
                    total_spent=Coalesce(
                        Sum("total_price"),
                        Value(Decimal("0.00")),
                        output_field=money_field,
                    ),
                    last_order=Max("created_at"),
                )
                .order_by("-total_spent", "-order_count", "-last_order")[
                    : self.TOP_LIMIT
                ]
            )
            for row in customer_rows:
                top_customers.append(
                    {
                        "id": row["customer_id"],
                        "name": row["customer__name"] or "Unnamed customer",
                        "contact": row["customer__contact"] or "-",
                        "order_count": row["order_count"],
                        "total_spent": self.format_money(row["total_spent"]),
                        "last_order": row["last_order"],
                    }
                )

            fast_selling_services = []
            service_rows = (
                order_items.filter(
                    created_at__gte=last_30_days,
                    measurement_type__isnull=False,
                )
                .values(
                    "measurement_type_id",
                    "measurement_type__name",
                    "measurement_type__measurement_type__name",
                )
                .annotate(
                    order_count=Count("order_id", distinct=True),
                    quantity_sold=Coalesce(
                        Sum("quantity"),
                        Value(Decimal("0.00")),
                        output_field=quantity_field,
                    ),
                    revenue=Coalesce(
                        Sum("price"),
                        Value(Decimal("0.00")),
                        output_field=money_field,
                    ),
                    last_sold=Max("created_at"),
                )
                .order_by("-quantity_sold", "-order_count", "-revenue")[
                    : self.TOP_LIMIT
                ]
            )
            for row in service_rows:
                fast_selling_services.append(
                    {
                        "id": row["measurement_type_id"],
                        "name": row["measurement_type__name"] or "Service",
                        "unit": row["measurement_type__measurement_type__name"]
                        or "unit",
                        "order_count": row["order_count"],
                        "quantity_sold": self.format_decimal(row["quantity_sold"]),
                        "revenue": self.format_money(row["revenue"]),
                        "last_sold": row["last_sold"],
                    }
                )

            recent_orders = OrderResponseSerializer(
                orders.order_by("-created_at")[: self.RECENT_ORDER_LIMIT],
                many=True,
            ).data

            dashboard_data = {
                "summary": {
                    "total_orders": total_orders,
                    "today_orders": today_orders,
                    "active_orders": active_orders,
                    "total_revenue": self.format_money(total_revenue),
                    "today_revenue": self.format_money(today_revenue),
                    "month_revenue": self.format_money(month_revenue),
                    "unpaid_amount": self.format_money(unpaid_amount),
                    "average_order_value": self.format_money(
                        total_revenue / total_orders if total_orders else 0,
                    ),
                    "orders_change_percent": self.get_metric_change(
                        current_week_orders,
                        previous_week_orders,
                    ),
                    "revenue_change_percent": self.get_metric_change(
                        current_week_revenue,
                        previous_week_revenue,
                    ),
                },
                "status_counts": self.get_status_counts(orders),
                "payment_counts": self.get_choice_counts(
                    orders,
                    "payment_status",
                    Order.PaymentChoice,
                ),
                "delivery_counts": self.get_choice_counts(
                    orders,
                    "delivery_type",
                    Order.DeliveryChoice,
                ),
                "top_customers": top_customers,
                "fast_selling_services": fast_selling_services,
                "revenue_trend": revenue_trend,
                "recent_orders": recent_orders,
            }

            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS,
                    data=dashboard_data,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as e:
            print(e)
            return Response(
                error_response(
                    GeneralMessages.SERVER_ERROR_MESSAGE,
                    ResponseCodes.SERVER_ERROR,
                    None,
                    str(e),
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class Update_order(APIView):
    PAYMENT_STATUS_ALIASES = {
        "paid": Order.PaymentChoice.PAID,
        "unpaid": Order.PaymentChoice.UNPAID,
    }

    def patch(self,request,id):
        try:
            order = get_object_or_404(Order,pk=id)
            data = request.data.copy()
            payment_status = data.get("payment_status")

            if payment_status in self.PAYMENT_STATUS_ALIASES:
                data["payment_status"] = self.PAYMENT_STATUS_ALIASES[payment_status]

            serializer = OrderUpdateSerializer(data=data)
            if not serializer.is_valid():
                return Response(
                    error_response(
                        GeneralMessages.VALIDATION_ERROR_MESSAGE,
                        ResponseCodes.VALIDATION_ERROR,
                        serializer.errors,
                    )
                    ,status=status.HTTP_400_BAD_REQUEST
                )

            updated_fields = []
            for field,value in serializer.validated_data.items():
                setattr(order,field,value)
                updated_fields.append(field)

            order.save(update_fields=[*updated_fields,"updated_at"])
            order_data = OrderResponseSerializer(order).data

            return Response(
                success_response(
                    "Order has been updated successfully.",
                    "ORDER_UPDATED",
                    data={
                        "order":order_data,
                    })
                ,status=status.HTTP_200_OK
            )
        except Http404:
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



class Delete_order(APIView):
    def delete(self,request,id):
        time.sleep(1)
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
        
        

class PromotionRules(APIView):
    def get(self, request):
        try:
            rules = PromotionRule.objects.all()
            serializer = PromotionRuleSerializer(rules, many=True)
            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS,
                    serializer.data,
                ),
                status=status.HTTP_200_OK,
            )
        except Exception as err:
            return Response(
                error_response(
                    GeneralMessages.SERVER_ERROR_MESSAGE,
                    ResponseCodes.SERVER_ERROR,
                    None,
                    str(err),
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def post(self, request):
        try:
            if PromotionRule.objects.exists():
                return Response(
                    error_response(
                        "Only one promotion rule is allowed. Edit the existing rule instead.",
                        ResponseCodes.VALIDATION_ERROR,
                        {"promotion": ["Only one promotion rule can exist at a time."]},
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer = PromotionRuleSerializer(data=request.data)
            if not serializer.is_valid():
                return Response(
                    error_response(
                        GeneralMessages.VALIDATION_ERROR_MESSAGE,
                        ResponseCodes.VALIDATION_ERROR,
                        serializer.errors,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            rule = serializer.save()
            return Response(
                success_response(
                    "Promotion rule created successfully.",
                    "PROMOTION_RULE_CREATED",
                    PromotionRuleSerializer(rule).data,
                ),
                status=status.HTTP_201_CREATED,
            )
        except Exception as err:
            return Response(
                error_response(
                    GeneralMessages.SERVER_ERROR_MESSAGE,
                    ResponseCodes.SERVER_ERROR,
                    None,
                    str(err),
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PromotionRuleDetail(APIView):
    def patch(self, request, id):
        try:
            rule = get_object_or_404(PromotionRule, pk=id)
            serializer = PromotionRuleSerializer(rule, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response(
                    error_response(
                        GeneralMessages.VALIDATION_ERROR_MESSAGE,
                        ResponseCodes.VALIDATION_ERROR,
                        serializer.errors,
                    ),
                    status=status.HTTP_400_BAD_REQUEST,
                )

            serializer.save()
            return Response(
                success_response(
                    "Promotion rule updated successfully.",
                    "PROMOTION_RULE_UPDATED",
                    serializer.data,
                ),
                status=status.HTTP_200_OK,
            )
        except Http404:
            return Response(
                error_response(
                    GeneralMessages.DOES_NOT_EXIST_MESSAGE,
                    ResponseCodes.DOES_NOT_EXIST,
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as err:
            return Response(
                error_response(
                    GeneralMessages.SERVER_ERROR_MESSAGE,
                    ResponseCodes.SERVER_ERROR,
                    None,
                    str(err),
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def delete(self, request, id):
        try:
            rule = get_object_or_404(PromotionRule, pk=id)
            rule.delete()
            return Response(
                success_response(
                    "Promotion rule deleted successfully.",
                    ResponseCodes.DELETED,
                    None,
                ),
                status=status.HTTP_200_OK,
            )
        except Http404:
            return Response(
                error_response(
                    GeneralMessages.DOES_NOT_EXIST_MESSAGE,
                    ResponseCodes.DOES_NOT_EXIST,
                ),
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as err:
            return Response(
                error_response(
                    GeneralMessages.SERVER_ERROR_MESSAGE,
                    ResponseCodes.SERVER_ERROR,
                    None,
                    str(err),
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
