import pytest
from mock import MagicMock
from django_dynamic_fixture import G

from silver.models import Transaction

from silver_payu.models import PayUPaymentMethod, PayUTriggered
from silver_payu.forms import PayUBillingForm, PayUTransactionForm


def test_payment_method_data_set():
    payment_method = PayUPaymentMethod()

    payment_method.decrypt_data = lambda value: value
    payment_method.encrypt_data = lambda value: value

    payment_method.token = "random token"
    assert payment_method.token == "random token"

    payment_method.archived_customer = {'name': 'test'}
    assert payment_method.archived_customer == {'name': 'test'}


@pytest.mark.django_db
@pytest.mark.parametrize('data, form_class, archived_customer', [
    ({
        'email': 'test@test.com',
        'first_name': 'Jhon',
        'last_name': 'Doe',
        'phone': '+40000000000',
        'country': '',
        'fiscal_code': ''
    }, PayUBillingForm, {}),
    ({
        'email': 'test@test.com',
        'first_name': 'Jhon',
        'last_name': 'Doe',
        'phone': '+40000000000',
        'country': 'RO',
        'city': 'Timisoara',
        'fiscal_code': ''
    }, PayUTransactionForm, {
        'BILL_ADDRESS': '9 9',
        'BILL_CITY': 'Timisoara',
        'BILL_COUNTRYCODE': 'RO',
        'BILL_EMAIL': 'test@test.com',
        'BILL_FISCALCODE': '',
        'BILL_FNAME': 'Jhon',
        'BILL_LNAME': 'Doe',
        'BILL_PHONE': '+40000000000'
    })
])
def test_payment_processor_get_form(data, form_class, archived_customer):
    transaction = G(Transaction, payment_method=G(PayUPaymentMethod))

    form = PayUTriggered().get_form(transaction, MagicMock(POST=data))
    assert isinstance(form, form_class)

    assert transaction.payment_method.archived_customer == archived_customer
