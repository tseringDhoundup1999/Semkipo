import random
from datetime import datetime, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from customers.models import Customer
from measurement.models import ItemType, MeasurementType
from orders.models import Order, OrderItem


CUSTOMER_NAMES = [
    "Aarav Sharma",
    "Aditi Gurung",
    "Anil Shrestha",
    "Asmita Rai",
    "Bikash Tamang",
    "Binita Lama",
    "Deepak Karki",
    "Diksha Thapa",
    "Gaurav Basnet",
    "Isha Maharjan",
    "Kiran Bhandari",
    "Laxmi KC",
    "Manish Adhikari",
    "Maya Sherpa",
    "Nabin Khadka",
    "Nisha Pandey",
    "Prabin Gurung",
    "Prakriti Joshi",
    "Ramesh Magar",
    "Rita Bista",
    "Roshan Dangol",
    "Sabina Tamrakar",
    "Sagar Rana",
    "Samjhana Poudel",
    "Sandesh Lama",
    "Sanjita Shahi",
    "Saraswati Nepal",
    "Saugat Koirala",
    "Sita Bhattarai",
    "Suman Shrestha",
    "Sunita Tamang",
    "Suraj Maharjan",
    "Susmita Rai",
    "Ujjwal Karki",
    "Yogesh Thapa",
]

DEFAULT_SERVICES = [
    ("Wash & Fold", "Kg", Decimal("120.00")),
    ("Dry Cleaning", "Piece", Decimal("250.00")),
    ("Ironing", "Piece", Decimal("60.00")),
    ("Blanket Wash", "Piece", Decimal("350.00")),
    ("Shoe Cleaning", "Pair", Decimal("300.00")),
    ("Curtain Cleaning", "Meter", Decimal("180.00")),
]


class Command(BaseCommand):
    help = "Seed realistic dummy orders across a date range."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=500,
            help="Number of dummy orders to create.",
        )
        parser.add_argument(
            "--start-date",
            default="2023-01-01",
            help="First possible order date in YYYY-MM-DD format.",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=20260504,
            help="Random seed for repeatable data shape.",
        )

    def handle(self, *args, **options):
        count = options["count"]
        rng = random.Random(options["seed"])
        start_date = self.get_start_date(options["start_date"])
        end_date = timezone.now()

        if count <= 0:
            self.stdout.write(self.style.WARNING("No orders created."))
            return

        if start_date >= end_date:
            raise ValueError("start-date must be before the current date.")

        with transaction.atomic():
            customers = self.ensure_customers()
            services = self.ensure_services()
            created_orders = self.create_orders(
                count=count,
                customers=customers,
                services=services,
                start_date=start_date,
                end_date=end_date,
                rng=rng,
            )

        self.stdout.write(
            self.style.SUCCESS(
                f"Created {created_orders} dummy orders from "
                f"{start_date.date().isoformat()} to {end_date.date().isoformat()}."
            )
        )

    def get_start_date(self, value):
        parsed_date = datetime.strptime(value, "%Y-%m-%d")
        return timezone.make_aware(parsed_date)

    def ensure_customers(self):
        customers = []

        for index, name in enumerate(CUSTOMER_NAMES, start=1):
            customer, _ = Customer.objects.get_or_create(
                contact=f"98050{index:05d}",
                defaults={
                    "name": name,
                    "address": self.get_address(index),
                },
            )
            customers.append(customer)

        return customers

    def get_address(self, index):
        areas = [
            "Boudha",
            "Lazimpat",
            "Thamel",
            "Patan",
            "Baneshwor",
            "Maharajgunj",
            "Kalanki",
            "Kumaripati",
        ]

        return f"{areas[index % len(areas)]}, Kathmandu"

    def ensure_services(self):
        services = list(ItemType.objects.select_related("measurement_type").all())

        if services:
            return services

        measurement_cache = {}

        for service_name, unit_name, price in DEFAULT_SERVICES:
            measurement = measurement_cache.get(unit_name)

            if measurement is None:
                measurement, _ = MeasurementType.objects.get_or_create(
                    name=unit_name,
                )
                measurement_cache[unit_name] = measurement

            service, _ = ItemType.objects.get_or_create(
                name=service_name,
                defaults={
                    "measurement_type": measurement,
                    "price_per_unit": price,
                },
            )
            services.append(service)

        return services

    def create_orders(self, count, customers, services, start_date, end_date, rng):
        created_orders = 0
        total_seconds = int((end_date - start_date).total_seconds())
        customer_weights = self.get_customer_weights(len(customers))
        service_weights = self.get_service_weights(len(services))

        for _ in range(count):
            created_at = start_date + timedelta(
                seconds=rng.randint(0, total_seconds),
            )
            customer = rng.choices(customers, weights=customer_weights, k=1)[0]
            delivery_type = rng.choices(
                [Order.DeliveryChoice.PICKUP, Order.DeliveryChoice.DELIVERY],
                weights=[72, 28],
                k=1,
            )[0]
            delivery_charge = (
                Decimal(rng.choice([80, 100, 120, 150, 180]))
                if delivery_type == Order.DeliveryChoice.DELIVERY
                else Decimal("0.00")
            )
            discount = rng.choices([0, 5, 10, 15], weights=[76, 12, 9, 3], k=1)[
                0
            ]
            status = self.get_status(created_at, rng)
            payment_status = self.get_payment_status(status, rng)

            order = Order.objects.create(
                customer=customer,
                status=status,
                payment_status=payment_status,
                delivery_type=delivery_type,
                delivery_address=customer.address
                if delivery_type == Order.DeliveryChoice.DELIVERY
                else "",
                delivery_charge=delivery_charge,
                discount=discount,
            )

            item_total = Decimal("0.00")
            item_count = rng.choices([1, 2, 3, 4], weights=[44, 34, 16, 6], k=1)[
                0
            ]
            selected_services = rng.choices(
                services,
                weights=service_weights,
                k=item_count,
            )

            for service in selected_services:
                quantity = self.get_quantity(service, rng)
                order_item = OrderItem.objects.create(
                    order=order,
                    measurement_type=service,
                    quantity=quantity,
                )
                item_total += order_item.price
                OrderItem.objects.filter(pk=order_item.pk).update(
                    created_at=created_at,
                    updated_at=created_at,
                )

            subtotal = item_total + delivery_charge
            discount_amount = subtotal * (Decimal(discount) / Decimal(100))
            order.total_price = subtotal - discount_amount
            order.save(update_fields=["total_price", "updated_at"])
            Order.objects.filter(pk=order.pk).update(
                created_at=created_at,
                updated_at=created_at,
            )
            created_orders += 1

        return created_orders

    def get_customer_weights(self, total_customers):
        return [
            max(2, total_customers - index)
            for index in range(total_customers)
        ]

    def get_service_weights(self, total_services):
        weights = [max(3, total_services - index + 3) for index in range(total_services)]

        if weights:
            weights[0] *= 3

        if len(weights) > 1:
            weights[1] *= 2

        return weights

    def get_status(self, created_at, rng):
        age_days = (timezone.now() - created_at).days

        if age_days <= 7:
            statuses = [
                Order.StatusChoice.PENDING,
                Order.StatusChoice.IN_PROGRESS,
                Order.StatusChoice.COMPLETED,
                Order.StatusChoice.CANCELLED,
            ]
            weights = [44, 34, 18, 4]
        elif age_days <= 30:
            statuses = [
                Order.StatusChoice.PENDING,
                Order.StatusChoice.IN_PROGRESS,
                Order.StatusChoice.COMPLETED,
                Order.StatusChoice.CANCELLED,
            ]
            weights = [20, 26, 48, 6]
        else:
            statuses = [
                Order.StatusChoice.COMPLETED,
                Order.StatusChoice.CANCELLED,
                Order.StatusChoice.PENDING,
            ]
            weights = [86, 9, 5]

        return rng.choices(statuses, weights=weights, k=1)[0]

    def get_payment_status(self, order_status, rng):
        if order_status == Order.StatusChoice.CANCELLED:
            return rng.choices(
                [Order.PaymentChoice.UNPAID, Order.PaymentChoice.PAID],
                weights=[80, 20],
                k=1,
            )[0]

        if order_status == Order.StatusChoice.COMPLETED:
            return rng.choices(
                [Order.PaymentChoice.PAID, Order.PaymentChoice.UNPAID],
                weights=[82, 18],
                k=1,
            )[0]

        return rng.choices(
            [Order.PaymentChoice.UNPAID, Order.PaymentChoice.PAID],
            weights=[64, 36],
            k=1,
        )[0]

    def get_quantity(self, service, rng):
        unit = (service.measurement_type.name if service.measurement_type else "").lower()

        if unit in ["kg", "kilogram", "kilograms"]:
            value = rng.choice([1, 1.5, 2, 2.5, 3, 4, 5, 6, 8])
        elif unit in ["meter", "metre", "meters", "metres"]:
            value = rng.choice([2, 3, 4, 5, 6, 8, 10, 12])
        else:
            value = rng.choice([1, 1, 1, 2, 2, 3, 4])

        return Decimal(str(value)).quantize(Decimal("0.01"))
