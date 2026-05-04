from rest_framework import serializers
from customers.models import Customer
from .models import Order,OrderItem
from measurement.models import ItemType
from decimal import Decimal, InvalidOperation


class CustomerSerializer(serializers.Serializer):
    id = serializers.IntegerField()

class DeliverySerializer(serializers.Serializer):
    type=serializers.CharField()
    address = serializers.CharField(allow_blank=True)
    amount = serializers.IntegerField()


class ItemSerializer(serializers.Serializer):
    item_id = serializers.IntegerField()
    measurement_type_id = serializers.IntegerField()
    quantity = serializers.DecimalField(max_digits=10,decimal_places=2)

    def validate(self, attrs):
        item_id = attrs.get("item_id")
        measurement_type_id = attrs.get("measurement_type_id")
        quantity = attrs.get("quantity")

        try:
            item = ItemType.objects.select_related("measurement_type").get(id=item_id)
        except ItemType.DoesNotExist:
            raise serializers.ValidationError({"item_id": "Service item does not exist."})

        item_measurement_type_id = item.measurement_type_id
        if item_measurement_type_id != measurement_type_id:
            raise serializers.ValidationError(
                {"measurement_type_id": "Selected unit does not match the service item."}
            )

        try:
            quantity_decimal = Decimal(str(quantity))
        except (InvalidOperation, TypeError, ValueError):
            raise serializers.ValidationError({"quantity": "Enter a valid quantity."})

        if quantity_decimal <= 0:
            raise serializers.ValidationError(
                {"quantity": "Quantity must be greater than zero."}
            )

        if not item.allows_decimal_quantity() and quantity_decimal % 1 != 0:
            unit_name = item.measurement_type.name if item.measurement_type else "this unit"
            raise serializers.ValidationError(
                {"quantity": f"Quantity for '{unit_name}' must be a whole number."}
            )

        attrs["item_obj"] = item
        return attrs

class OrderSerializer(serializers.Serializer):
    customer = CustomerSerializer()
    delivery = DeliverySerializer()
    items = ItemSerializer(many=True)
    payment = serializers.BooleanField()


class OrderUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=Order.StatusChoice.choices, required=False)
    payment_status = serializers.ChoiceField(
        choices=Order.PaymentChoice.choices, required=False
    )

    def validate(self, attrs):
        if not attrs:
            raise serializers.ValidationError(
                "Provide status or payment_status to update."
            )

        return attrs


# response serializers 

class CustomerResponseSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Customer
        fields = ['name','contact']


class OrderItemResponseSerializer(serializers.ModelSerializer):
    name = serializers.CharField(source='measurement_type.name',read_only=True)
    unit = serializers.CharField(source='measurement_type.measurement_type',read_only=True)
    price_per_unit = serializers.CharField(source='measurement_type.price_per_unit',read_only=True)
    
    total_price = serializers.DecimalField(source='price',max_digits=10,decimal_places=2,read_only=True)
    class Meta:
        model = OrderItem
        fields = ['quantity','total_price','name','unit','price_per_unit']


class OrderResponseSerializer(serializers.ModelSerializer):
    customer = CustomerResponseSerializer(read_only=True)
    items = OrderItemResponseSerializer(many=True,read_only=True)
    payment_status = serializers.SerializerMethodField()

    def get_payment_status(self, obj):
        return {
            "value": obj.payment_status,
            "label": obj.get_payment_status_display()
        }
    class Meta:
        model = Order
        fields = [
            "id",
            "customer",
            "status",
            "delivery_type",
            "delivery_address",
            "delivery_charge",
            "payment_status",
            "discount",
            "total_price",
            "items",
            'created_at',
        ]
    
    
    
