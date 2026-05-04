from rest_framework import serializers
from .models import User 

class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User 
        fields = ["username","email","password"]
        extra_kwargs = {
            "password": {"write_only":True}
        }

    def create(self,validated_data):
        # New users must always start unverified; admins can verify later.
        user = User.objects.create_user(**validated_data, is_verified=False)
        return user




# login serializer 
class loginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
