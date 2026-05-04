from django.shortcuts import render

from django.conf import settings
from django.db.models import Prefetch, Q
# ==== rest_framework ============#
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.validators import ValidationError
from rest_framework import status
from decimal import Decimal

from .models import Customer
from .serializers import contactSerializers,customerNameSerializer
from orders.models import Order

# constants
from core.constants.response_message import SuccessMessages,ErrorMessages,GeneralMessages
from core.constants.response_code import ResponseCodes
from core.utils.api_response import error_response, success_response



# Create your views here.


class Customers_view(APIView):
    SERVICE_BREAKDOWN_LIMIT = 6
    DEFAULT_PAGE_SIZE = 20
    MIN_PAGE_SIZE = 15
    MAX_PAGE_SIZE = 20

    def clean_data(self, value):
        if value is None:
            return None

        value = str(value).strip()

        if value.lower() in ["undefined", "null", ""]:
            return None

        return value

    def decimal_value(self, value):
        return Decimal(str(value or "0"))

    def format_money(self, value):
        return f"{self.decimal_value(value):.2f}"

    def format_quantity(self, value):
        return f"{self.decimal_value(value):.2f}"

    def get_service_key(self, item):
        if item.measurement_type_id:
            return f"service-{item.measurement_type_id}"

        return f"unknown-{item.id}"

    def get_service_name(self, item):
        if item.measurement_type:
            return item.measurement_type.name

        return "Unknown service"

    def get_service_unit(self, item):
        if item.measurement_type and item.measurement_type.measurement_type:
            return item.measurement_type.measurement_type.name

        return "unit"

    def get_customer_payload(self, customer):
        orders = list(customer.orders.all())
        service_map = {}
        status_counts = {
            Order.StatusChoice.PENDING: 0,
            Order.StatusChoice.IN_PROGRESS: 0,
            Order.StatusChoice.COMPLETED: 0,
            Order.StatusChoice.CANCELLED: 0,
        }
        payment_due = Decimal("0.00")
        total_spent = Decimal("0.00")
        total_wash_quantity = Decimal("0.00")

        for order in orders:
            order_total = self.decimal_value(order.total_price)
            total_spent += order_total
            status_counts[order.status] = status_counts.get(order.status, 0) + 1

            if order.payment_status == Order.PaymentChoice.UNPAID:
                payment_due += order_total

            for item in order.items.all():
                quantity = self.decimal_value(item.quantity)
                revenue = self.decimal_value(item.price)
                service_key = self.get_service_key(item)
                service = service_map.setdefault(
                    service_key,
                    {
                        "id": item.measurement_type_id,
                        "name": self.get_service_name(item),
                        "unit": self.get_service_unit(item),
                        "quantity": Decimal("0.00"),
                        "revenue": Decimal("0.00"),
                        "order_ids": set(),
                    },
                )

                service["quantity"] += quantity
                service["revenue"] += revenue
                service["order_ids"].add(order.id)
                total_wash_quantity += quantity

        service_breakdown = sorted(
            service_map.values(),
            key=lambda service: (
                service["quantity"],
                len(service["order_ids"]),
                service["revenue"],
            ),
            reverse=True,
        )
        formatted_breakdown = [
            {
                "id": service["id"],
                "name": service["name"],
                "unit": service["unit"],
                "quantity": self.format_quantity(service["quantity"]),
                "revenue": self.format_money(service["revenue"]),
                "order_count": len(service["order_ids"]),
            }
            for service in service_breakdown[: self.SERVICE_BREAKDOWN_LIMIT]
        ]
        favorite_service = formatted_breakdown[0] if formatted_breakdown else None
        last_order = orders[0] if orders else None

        return {
            "id": customer.id,
            "name": customer.name or "Unnamed customer",
            "contact": customer.contact,
            "address": customer.address or "",
            "created_at": customer.created_at,
            "last_order_at": last_order.created_at if last_order else None,
            "order_count": len(orders),
            "completed_orders": status_counts[Order.StatusChoice.COMPLETED],
            "active_orders": (
                status_counts[Order.StatusChoice.PENDING]
                + status_counts[Order.StatusChoice.IN_PROGRESS]
            ),
            "cancelled_orders": status_counts[Order.StatusChoice.CANCELLED],
            "payment_due": self.format_money(payment_due),
            "total_spent": self.format_money(total_spent),
            "total_wash_quantity": self.format_quantity(total_wash_quantity),
            "favorite_service": favorite_service,
            "service_breakdown": formatted_breakdown,
            "recent_orders": [
                {
                    "id": order.id,
                    "status": order.status,
                    "payment_status": order.payment_status,
                    "total_price": self.format_money(order.total_price),
                    "created_at": order.created_at,
                }
                for order in orders[:3]
            ],
            "_sort_due": payment_due,
            "_sort_spent": total_spent,
            "_sort_wash": total_wash_quantity,
            "_sort_last_order": last_order.created_at if last_order else customer.created_at,
            "_sort_has_order": bool(last_order),
        }

    def get_service_mix(self, customers):
        service_map = {}

        for customer in customers:
            for service in customer["service_breakdown"]:
                service_key = service["id"] or service["name"]
                entry = service_map.setdefault(
                    service_key,
                    {
                        "id": service["id"],
                        "name": service["name"],
                        "unit": service["unit"],
                        "quantity": Decimal("0.00"),
                        "revenue": Decimal("0.00"),
                        "customer_count": 0,
                    },
                )
                entry["quantity"] += self.decimal_value(service["quantity"])
                entry["revenue"] += self.decimal_value(service["revenue"])
                entry["customer_count"] += 1

        service_mix = sorted(
            service_map.values(),
            key=lambda service: (
                service["quantity"],
                service["customer_count"],
                service["revenue"],
            ),
            reverse=True,
        )

        return [
            {
                "id": service["id"],
                "name": service["name"],
                "unit": service["unit"],
                "quantity": self.format_quantity(service["quantity"]),
                "revenue": self.format_money(service["revenue"]),
                "customer_count": service["customer_count"],
            }
            for service in service_mix[: self.SERVICE_BREAKDOWN_LIMIT]
        ]

    def sort_customers(self, customers, sort):
        sort_mapping = {
            "name-asc": lambda customer: customer["name"].lower(),
            "orders-desc": lambda customer: customer["order_count"],
            "due-desc": lambda customer: customer["_sort_due"],
            "spent-desc": lambda customer: customer["_sort_spent"],
            "wash-desc": lambda customer: customer["_sort_wash"],
            "recent-desc": lambda customer: (
                customer["_sort_has_order"],
                customer["_sort_last_order"],
            ),
        }
        sort_key = sort_mapping.get(sort or "recent-desc", sort_mapping["recent-desc"])
        reverse = sort != "name-asc"

        return sorted(customers, key=sort_key, reverse=reverse)

    def parse_positive_int(self, value, default_value):
        try:
            parsed_value = int(value)
            return parsed_value if parsed_value > 0 else default_value
        except (TypeError, ValueError):
            return default_value

    def get(self, request):
        try:
            search = self.clean_data(request.GET.get("search"))
            sort = self.clean_data(request.GET.get("sort")) or "recent-desc"
            page = self.parse_positive_int(request.GET.get("page"), 1)
            requested_page_size = self.parse_positive_int(
                request.GET.get("page_size"),
                self.DEFAULT_PAGE_SIZE,
            )
            page_size = max(
                self.MIN_PAGE_SIZE,
                min(requested_page_size, self.MAX_PAGE_SIZE),
            )

            orders_queryset = Order.objects.prefetch_related(
                "items__measurement_type__measurement_type",
            ).order_by("-created_at")
            customers_queryset = Customer.objects.prefetch_related(
                Prefetch("orders", queryset=orders_queryset),
            )

            if search:
                customers_queryset = customers_queryset.filter(
                    Q(name__icontains=search) | Q(contact__icontains=search),
                )

            customers = [
                self.get_customer_payload(customer)
                for customer in customers_queryset.order_by("name", "contact")
            ]
            customers = self.sort_customers(customers, sort)

            total_customers = len(customers)
            total_pages = max((total_customers + page_size - 1) // page_size, 1)
            current_page = min(page, total_pages)
            start_index = (current_page - 1) * page_size
            end_index = start_index + page_size
            paginated_customers = customers[start_index:end_index]
            active_customers = sum(1 for customer in customers if customer["order_count"])
            customers_with_due = sum(
                1 for customer in customers if customer["_sort_due"] > Decimal("0.00")
            )
            total_due = sum(
                (customer["_sort_due"] for customer in customers),
                Decimal("0.00"),
            )
            total_spent = sum(
                (customer["_sort_spent"] for customer in customers),
                Decimal("0.00"),
            )
            total_washes = sum(
                (customer["_sort_wash"] for customer in customers),
                Decimal("0.00"),
            )
            service_mix = self.get_service_mix(customers)

            for customer in customers:
                customer.pop("_sort_due", None)
                customer.pop("_sort_spent", None)
                customer.pop("_sort_wash", None)
                customer.pop("_sort_last_order", None)
                customer.pop("_sort_has_order", None)

            return Response(
                success_response(
                    GeneralMessages.GET_SUCCESS_MESSAGE,
                    ResponseCodes.RETRIEVE_SUCCESS,
                    data={
                        "summary": {
                            "total_customers": total_customers,
                            "active_customers": active_customers,
                            "customers_with_due": customers_with_due,
                            "total_payment_due": self.format_money(total_due),
                            "total_spent": self.format_money(total_spent),
                            "total_wash_quantity": self.format_quantity(total_washes),
                            "average_orders_per_customer": round(
                                sum(
                                    customer["order_count"]
                                    for customer in customers
                                )
                                / total_customers,
                                1,
                            )
                            if total_customers
                            else 0,
                            "top_service": service_mix[0] if service_mix else None,
                        },
                        "service_mix": service_mix,
                        "customers": paginated_customers,
                        "pagination": {
                            "count": total_customers,
                            "current_page": current_page,
                            "total_pages": total_pages,
                            "page_size": page_size,
                            "has_next": current_page < total_pages,
                            "has_prev": current_page > 1,
                        },
                    },
                ),
                status=status.HTTP_200_OK,
            )

        except Exception as err:
            print(err)
            return Response(
                error_response(
                    GeneralMessages.SERVER_ERROR_MESSAGE,
                    ResponseCodes.SERVER_ERROR,
                    None,
                    err,
                ),
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


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
         
        
    
        
