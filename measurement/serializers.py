from rest_framework import serializers
from .models import ItemType, MeasurementType


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
    
    measurement_type_detail = MeasurementTypeSerializer(
        source="measurement_type",read_only=True
    )
    class Meta:
        model = ItemType
        fields = "__all__"