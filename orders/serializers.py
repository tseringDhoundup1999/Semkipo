from rest_framework import serializers


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