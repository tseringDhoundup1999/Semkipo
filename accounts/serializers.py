from rest_framework import serializers
from django.conf import settings 
from .models import User 
from django.contrib.auth import authenticate

from django.contrib.auth.tokens import default_token_generator 
from django.utils.http import urlsafe_base64_encode 
from django.utils.encoding import force_bytes
from django.urls import reverse
from django.core.mail import send_mail 
from django.template.loader import render_to_string
from django.conf import settings 
from datetime import datetime;

class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = User 
        fields = ["username","email","password"]
        extra_kwargs = {
            "password": {"write_only":True}
        }

    def create(self,validated_data):
        user = User.objects.create_user(**validated_data)
        user.is_verified = False # Set the user as unverified by default
        user.save()  


        # generate verification token and encode the user id in base64
        token = default_token_generator.make_token(user) 
        uid =  urlsafe_base64_encode(force_bytes(user.pk))

        # generate a verification link  
        verification_url = f"{settings.FRONTEND_URL}/verify-email/{uid}/{token}" 

        # send email 
        subject = "Verify your email"
        message = render_to_string(
                "accounts/email_verification.html",{"user":user,"verification_url":verification_url}
        )
        from_email = settings.DEFAULT_FROM_EMAIL 
        recipient_list = [user.email]
        send_mail(subject, message, from_email, recipient_list)
        # after email send set the email_send_datetime
        user.email_verification_sent_at = datetime.now()
        user.save()

        return user


