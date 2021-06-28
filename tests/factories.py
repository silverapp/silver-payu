import factory
from factory.django import mute_signals, DjangoModelFactory

from django.db.models import signals
from silver.fixtures.factories import CustomerFactory

from silver_payu.models import PayUPaymentMethod


@mute_signals(signals.pre_save, signals.post_save)
class PayUPaymentMethodFactory(DjangoModelFactory):
    class Meta:
        model = PayUPaymentMethod

    payment_processor = 'payu_triggered_v2'
    customer = factory.SubFactory(CustomerFactory)
    data = factory.Sequence(lambda i: {})
