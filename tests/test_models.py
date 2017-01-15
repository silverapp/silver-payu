import pytest

import silver_payu

from silver_payu.models import PayUPaymentMethod


def test_payment_method_data_set():
    payment_method = PayUPaymentMethod()

    payment_method.decrypt_data = lambda value: value
    payment_method.encrypt_data = lambda value: value

    payment_method.token = "random token"
    assert payment_method.token == "random token"

    payment_method.archived_customer = {'name': 'test'}
    assert payment_method.archived_customer == {'name': 'test'}
