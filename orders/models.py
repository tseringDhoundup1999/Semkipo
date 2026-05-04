from django.db import models
from customers.models import Customer
from measurement.models import ItemType
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from decimal import Decimal, InvalidOperation
from django.utils import timezone

# Create your models here.

class Order(models.Model):
    class StatusChoice(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
    
    class DeliveryChoice(models.TextChoices):
        PICKUP = "pk","Pickup"
        DELIVERY = "d","Delivery"
    
    class PaymentChoice(models.TextChoices):
        PAID = 'p','Paid'
        UNPAID = 'up', 'Unpaid'
        
    
    customer = models.ForeignKey(Customer,on_delete=models.SET_NULL,null=True,related_name="orders")
    status = models.CharField(max_length=20, choices=StatusChoice.choices,default=StatusChoice.PENDING)
    payment_status = models.CharField(max_length=4,choices=PaymentChoice.choices,default=PaymentChoice.UNPAID)
    delivery_type = models.CharField(max_length=4,choices=DeliveryChoice.choices,default=DeliveryChoice.PICKUP)
    delivery_address = models.CharField(max_length=255,blank=True,null=True)
    delivery_charge = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)
    discount = models.PositiveSmallIntegerField(default=0,validators=[MinValueValidator(0), MaxValueValidator(100)])  # Discount percentage (0-100)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.name if self.customer else 'No Customer'}"


class OrderItem(models.Model):
    order = models.ForeignKey(Order,on_delete=models.CASCADE,related_name="items")
    measurement_type = models.ForeignKey(ItemType,on_delete=models.SET_NULL,null=True)
    quantity = models.DecimalField(max_digits=10,decimal_places=2,default=1.0)
    price = models.DecimalField(max_digits=10, decimal_places=2,default=0.0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"OrderItem #{self.id} - {self.measurement_type.name if self.measurement_type else 'No ItemType'}"

    def clean(self):
        quantity_value = self.quantity
        try:
            quantity_decimal = Decimal(str(quantity_value))
        except (InvalidOperation, TypeError, ValueError):
            raise ValidationError({"quantity": "Enter a valid quantity."})

        if quantity_decimal <= 0:
            raise ValidationError({"quantity": "Quantity must be greater than zero."})

        if self.measurement_type and not self.measurement_type.allows_decimal_quantity():
            if quantity_decimal % 1 != 0:
                unit_name = (
                    self.measurement_type.measurement_type.name
                    if self.measurement_type.measurement_type
                    else "this unit"
                )
                raise ValidationError(
                    {
                        "quantity": (
                            f"Quantity for '{unit_name}' must be a whole number."
                        )
                    }
                )
    
    def save(self,*args,**kwargs):
        self.full_clean()
        item_price = self.measurement_type.price_per_unit if self.measurement_type else 0 
        self.price = item_price * self.quantity
        super().save(*args,**kwargs)


class PromotionRule(models.Model):
    class RuleType(models.TextChoices):
        DISCOUNT = "discount", "Discount"
        LOYALTY = "loyalty", "Loyalty"

    class ScheduleType(models.TextChoices):
        DAY = "day", "Day"
        RANGE = "range", "Date range"

    class Weekday(models.TextChoices):
        MONDAY = "monday", "Monday"
        TUESDAY = "tuesday", "Tuesday"
        WEDNESDAY = "wednesday", "Wednesday"
        THURSDAY = "thursday", "Thursday"
        FRIDAY = "friday", "Friday"
        SATURDAY = "saturday", "Saturday"
        SUNDAY = "sunday", "Sunday"

    name = models.CharField(max_length=120)
    rule_type = models.CharField(max_length=20, choices=RuleType.choices)
    is_active = models.BooleanField(default=True)
    description = models.CharField(max_length=255, blank=True, default="")

    # Discount rule fields
    discount_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    schedule_type = models.CharField(
        max_length=20,
        choices=ScheduleType.choices,
        null=True,
        blank=True,
    )
    weekday = models.CharField(
        max_length=20,
        choices=Weekday.choices,
        null=True,
        blank=True,
    )
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)

    # Loyalty rule fields
    required_wash_count = models.PositiveIntegerField(null=True, blank=True)
    free_wash_count = models.PositiveIntegerField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.rule_type})"

    def clean(self):
        if self.rule_type == self.RuleType.DISCOUNT:
            if self.discount_percent is None:
                raise ValidationError(
                    {"discount_percent": "Discount percent is required."}
                )
            if not self.schedule_type:
                raise ValidationError({"schedule_type": "Schedule type is required."})

            if self.schedule_type == self.ScheduleType.DAY:
                if not self.weekday:
                    raise ValidationError(
                        {"weekday": "Select weekday for day-based discount."}
                    )
                self.start_date = None
                self.end_date = None
            elif self.schedule_type == self.ScheduleType.RANGE:
                if not self.start_date or not self.end_date:
                    raise ValidationError(
                        {
                            "start_date": "Start and end date are required for range discount.",
                            "end_date": "Start and end date are required for range discount.",
                        }
                    )
                if self.end_date < self.start_date:
                    raise ValidationError(
                        {"end_date": "End date must be after start date."}
                    )
                self.weekday = None

            self.required_wash_count = None
            self.free_wash_count = None

        if self.rule_type == self.RuleType.LOYALTY:
            if not self.required_wash_count or self.required_wash_count <= 0:
                raise ValidationError(
                    {"required_wash_count": "Required wash count must be at least 1."}
                )
            if not self.free_wash_count or self.free_wash_count <= 0:
                raise ValidationError(
                    {"free_wash_count": "Free wash count must be at least 1."}
                )

            self.discount_percent = None
            self.schedule_type = None
            self.weekday = None
            self.start_date = None
            self.end_date = None

    def is_currently_applicable(self, check_date=None):
        if not self.is_active:
            return False

        check_date = check_date or timezone.now().date()

        if self.rule_type == self.RuleType.LOYALTY:
            return True

        if self.schedule_type == self.ScheduleType.DAY and self.weekday:
            return check_date.strftime("%A").lower() == self.weekday

        if (
            self.schedule_type == self.ScheduleType.RANGE
            and self.start_date
            and self.end_date
        ):
            return self.start_date <= check_date <= self.end_date

        return False
    