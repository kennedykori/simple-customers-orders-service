import logging

from typing import Type

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

import africastalking
from africastalking.Service import AfricasTalkingException

from .models import Order


# Constants

NEW_ORDER_MSG = (
    'Dear customer, a new order with order no %d, has been added.'
)

ORDER_APPROVED_MSG = (
    'Dear customer, your order with order no %d, has been approved and will '
    'be delivered soon.'
)

ORDER_CANCELED_MSG = (
    'Dear customer, your order with order no %d, has been canceled.'
)

ORDER_PENDING_MSG = (
    'Dear customer, your order with order no %d, is now awaiting review. You '
    'can still add, remove or update items in the order before it is '
    'reviewed.'
)

ORDER_REJECTED_MSG = (
    'Dear customer, we regret to inform you that your order with order no '
    '%d, was not accepted and thus will not be delivered. Visit our site to '
    "get more details regarding the order's rejection."
)

logger = logging.getLogger('apps.shop.signals')


# Initialize Africa's Talking client

try:
    africastalking.initialize(
        settings.AFRICASTALKING_API['USERNAME'],
        settings.AFRICASTALKING_API['API_KEY']
    )
except AfricasTalkingException:
    logging.exception('Unable to initialize africastalking service')

SMS = africastalking.SMS


# Signal Receivers

@receiver(post_save, sender=Order)
def notify_customer(
        sender: Type[Order],
        instance: Order,
        created: bool, **kwargs) -> None:
    if not SMS:
        logging.error(
            'SMS service not initialized, cannot send sms notifications.'
        )

    try:
        if created:
            SMS.send(NEW_ORDER_MSG, [instance.customer.phone_number])
            return

        update_fields = kwargs.get('update_fields', None)
        # Do not send a notification sms if the order's state did not change
        if not(update_fields and 'state' in update_fields):
            return

        if instance.state == Order.OrderState.APPROVED.choice_value:
            SMS.send(
                ORDER_APPROVED_MSG % instance.pk,
                [instance.customer.phone_number]
            )
        elif instance.state == Order.OrderState.CANCELED.choice_value:
            SMS.send(
                ORDER_CANCELED_MSG % instance.pk,
                [instance.customer.phone_number]
            )
        elif instance.state == Order.OrderState.PENDING.choice_value:
            SMS.send(
                ORDER_PENDING_MSG % instance.pk,
                [instance.customer.phone_number]
            )
        elif instance.state == Order.OrderState.REJECTED.choice_value:
            SMS.send(
                ORDER_REJECTED_MSG % instance.pk,
                [instance.customer.phone_number]
            )
    except AfricasTalkingException:
        logging.exception('Unable to send sms notifications.')
