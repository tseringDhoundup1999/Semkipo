from rest_framework import serializers
from customers.models import Customer
from .models import Order,OrderItem


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

class OrderSerializer(serializers.Serializer):
    customer = CustomerSerializer()
    delivery = DeliverySerializer()
    items = ItemSerializer(many=True)
    payment = serializers.BooleanField()


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
    
    
    