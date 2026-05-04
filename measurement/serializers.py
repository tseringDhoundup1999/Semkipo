from rest_framework import serializers
from .models import ItemType, MeasurementType
from orders.models import OrderItem


class MeasurementTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MeasurementType
        fields = "__all__"
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        data['name'] = data['name'].capitalize()  # Capitalize the name field
        return data         



class ItemTypeSerializer(serializers.ModelSerializer):
    measurement_type = serializers.PrimaryKeyRelatedField(queryset=MeasurementType.objects.all())
    can_delete = serializers.SerializerMethodField()
    delete_block_reason = serializers.SerializerMethodField()
    
    measurement_type_detail = MeasurementTypeSerializer(
        source="measurement_type",read_only=True
    )
    class Meta:
        model = ItemType
        fields = "__all__"

    def get_can_delete(self, obj):
        return not OrderItem.objects.filter(measurement_type=obj).exists()

    def get_delete_block_reason(self, obj):
        if OrderItem.objects.filter(measurement_type=obj).exists():
            return "Used in existing orders."
        return ""