from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CompanySettings, User

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ("email", "username", "is_verified", "is_staff", "is_superuser")
    list_filter = ("is_verified", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username")
    ordering = ("email",)

    fieldsets = UserAdmin.fieldsets + (
        ("Verification", {"fields": ("is_verified", "email_verification_sent_at")}),
    )


@admin.register(CompanySettings)
class CompanySettingsAdmin(admin.ModelAdmin):
    list_display = ("shop_name", "company_phone", "pan_number", "updated_at")
    search_fields = ("shop_name", "company_phone", "pan_number")
