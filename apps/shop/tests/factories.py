from decimal import Decimal

from django.utils.timezone import get_current_timezone

import factory

from ...core.tests.factories import AdminFactory, AuditBaseFactory

from ..models import Customer, Employee, Inventory, Order, OrderItem
from ..signals import post_save


# Model factories

class CustomerFactory(AuditBaseFactory):
    """
    Factory for the **Customer** model.
    """
    name = factory.Faker('name')
    address = factory.Faker('address')
    phone_number = '+254722000000'
    user = factory.LazyAttribute(lambda c: c.created_by)

    class Meta:
        model = Customer


class EmployeeFactory(AuditBaseFactory):
    """
    Factory for the **Employee** model.
    """
    name = factory.Faker('name_male')
    gender = Employee.Gender.MALE.choice_value
    user = factory.LazyAttribute(lambda e: e.created_by)
    created_by = factory.SubFactory(AdminFactory)

    class Meta:
        model = Employee

    class Params:
        female = factory.Trait(
            name=factory.Faker('name_female'),
            gender=Employee.Gender.FEMALE.choice_value
        )


class InventoryFactory(AuditBaseFactory):
    """
    Factory for the **Inventory** model.
    """
    beverage_name = factory.Sequence(lambda n: 'Beverage%s' % n)
    beverage_type = Inventory.BeverageTypes.COFFEE.choice_value
    caffeinated = factory.Faker('boolean', chance_of_getting_true=89)
    flavored = factory.Faker('boolean', chance_of_getting_true=75)
    on_hand = factory.Faker('pyint', min_value=0, max_value=9999, step=1)
    price = factory.Faker(
        'pydecimal',
        min_value=Decimal('1.00'),
        max_value=Decimal('10.00'),
        right_digits=2
    )
    warn_limit = factory.Faker('pyint', min_value=3, max_value=100, step=1)
    created_by = factory.SubFactory(AdminFactory)

    class Meta:
        model = Inventory

    class Params:
        low_stock = factory.Trait(
            on_hand=factory.LazyAttribute(lambda i: i.warn_limit)
        )
        no_stock = factory.Trait(on_hand=0)
        tea = factory.Trait(
            beverage_type=Inventory.BeverageTypes.TEA.choice_value,
            caffeinated=factory.Faker('boolean', chance_of_getting_true=30)
        )


@factory.django.mute_signals(post_save)
class OrderFactory(AuditBaseFactory):
    """
    Factory for the **Order** model.
    """
    customer = factory.SubFactory(CustomerFactory)
    state = Order.OrderState.CREATED.choice_value
    handler = None
    review_date = None
    comments = None

    class Meta:
        model = Order

    class Params:
        approved = factory.Trait(
            comments=factory.Faker('text', max_nb_chars=50),
            handler=factory.SubFactory(EmployeeFactory),
            review_date=factory.Faker(
                'future_datetime',
                end_date='+3d',
                tzinfo=get_current_timezone()
            ),
            state=Order.OrderState.APPROVED.choice_value
        )
        canceled = factory.Trait(
            comments=factory.Faker('text', max_nb_chars=250),
            handler=None,
            review_date=None,
            state=Order.OrderState.CANCELED.choice_value
        )
        pending = factory.Trait(
            comments=None,
            handler=None,
            review_date=None,
            state=Order.OrderState.PENDING.choice_value
        )
        rejected = factory.Trait(
            comments=factory.Faker('text', max_nb_chars=250),
            handler=factory.SubFactory(EmployeeFactory),
            review_date=factory.Faker(
                'future_datetime',
                end_date='+3d',
                tzinfo=get_current_timezone()
            ),
            state=Order.OrderState.REJECTED.choice_value
        )


class OrderItemFactory(AuditBaseFactory):
    """
    Factory for the **OrderItem** model.
    """
    order = factory.SubFactory(OrderFactory)
    item = factory.SubFactory(InventoryFactory)
    quantity = factory.Faker('pyint', min_value=0, max_value=9999, step=1)
    unit_price = factory.LazyAttribute(lambda oi: oi.item.price)

    class Meta:
        model = OrderItem

    class Params:
        random_price = factory.Trait(
            unit_price=factory.Faker(
                'pydecimal',
                min_value=Decimal('1.00'),
                max_value=Decimal('10.00'),
                right_digits=2
            )
        )
