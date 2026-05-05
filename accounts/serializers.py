from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import CompanySettings
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

    def validate_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.messages)
        return value




# login serializer 
class loginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class CompanySettingsSerializer(serializers.ModelSerializer):
    shopName = serializers.CharField(source="shop_name", max_length=120)
    companyPhone = serializers.CharField(
        source="company_phone",
        allow_blank=True,
        required=False,
        max_length=40,
    )
    panNumber = serializers.CharField(
        source="pan_number",
        allow_blank=True,
        required=False,
        max_length=40,
    )
    companyAddress = serializers.CharField(
        source="company_address",
        allow_blank=True,
        required=False,
        max_length=255,
    )
    updatedAt = serializers.DateTimeField(source="updated_at", read_only=True)

    class Meta:
        model = CompanySettings
        fields = [
            "shopName",
            "companyPhone",
            "panNumber",
            "companyAddress",
            "updatedAt",
        ]

    def validate_shopName(self, value):
        if not value.strip():
            raise serializers.ValidationError("Shop name is required.")

        return value.strip()


class ChangePasswordSerializer(serializers.Serializer):
    currentPassword = serializers.CharField(write_only=True)
    newPassword = serializers.CharField(write_only=True, min_length=6)
    confirmPassword = serializers.CharField(write_only=True)

    def validate_currentPassword(self, value):
        user = self.context["request"].user

        if not user.check_password(value):
            raise serializers.ValidationError("Current password is incorrect.")

        return value

    def validate(self, attrs):
        if attrs["newPassword"] != attrs["confirmPassword"]:
            raise serializers.ValidationError(
                {"confirmPassword": "Passwords must match."}
            )

        if attrs["currentPassword"] == attrs["newPassword"]:
            raise serializers.ValidationError(
                {"newPassword": "New password must be different."}
            )

        try:
            validate_password(attrs["newPassword"], self.context["request"].user)
        except DjangoValidationError as error:
            raise serializers.ValidationError({"newPassword": error.messages})

        return attrs

    def save(self, **kwargs):
        user = self.context["request"].user
        user.set_password(self.validated_data["newPassword"])
        user.save(update_fields=["password"])
        return user
    
