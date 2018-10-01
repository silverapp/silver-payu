import pytest
from faker import Faker
from mock import patch, MagicMock

from silver_payu.forms import PayUTransactionFormBase, PayUBillingForm

from .fixtures import *


faker = Faker()


@patch('silver_payu.forms.datetime')
def test_payu_transaction_form_build_body(mocked_datetime, transaction, payment_method):
    mocked_datetime.now.return_value.strftime.return_value = 'order_date'

    with patch('silver.utils.payments._get_jwt_token') as mocked_token:
        mocked_token.return_value = 'token'

        form = PayUTransactionFormBase(payment_method, transaction, {})

        assert form._build_form_body(transaction, None) == {
            'AUTOMODE': '1',
            'BACK_REF': '/pay/token/complete',
            'CURRENCY': 'RON',
            'ORDER': [{'PCODE': '%s-%s' % (transaction.document.series,
                                           transaction.document.number),
                       'PNAME': 'Payment for %s %s-%s' % (transaction.document.kind,
                                                          transaction.document.series,
                                                          transaction.document.number),
                       'PRICE': str(transaction.amount),
                       'PRICE_TYPE': 'GROSS',
                       'VAT': str(transaction.document.sales_tax_percent)}],
            'ORDER_DATE': 'order_date',
            'ORDER_REF': '%s' % transaction.uuid,
            'PAY_METHOD': 'CCVISAMC',
            'PRICES_CURRENCY': 'RON'
        }


@pytest.mark.parametrize('data, form_class, archived_customer', [
    ({
        'email': faker.email(),
        'first_name': faker.first_name(),
        'last_name': faker.last_name(),
        'phone': faker.phone_number(),
        'country': '',
        'fiscal_code': ''
    }, PayUBillingForm, {}),
    ({
        'email': 'john@acme.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '+40000000000',
        'country': 'RO',
        'city': 'Timisoara',
        'fiscal_code': ''
    }, PayUTransactionFormBase, {
        'BILL_ADDRESS': u"Zalaegerszegi utca 65.\nH-5484 ligetv\xc3\xa1r 9",
        'BILL_CITY': 'Timisoara',
        'BILL_COUNTRYCODE': 'RO',
        'BILL_EMAIL': 'john@acme.com',
        'BILL_FNAME': 'John',
        'BILL_LNAME': 'Doe',
        'BILL_PHONE': '+40000000000'
    })
])
def test_payment_processor_get_form(payment_processor, transaction, data,
                                    form_class, archived_customer):
    form = payment_processor.get_form(transaction, MagicMock(POST=data))

    assert isinstance(form, form_class)
    assert transaction.payment_method.archived_customer == archived_customer
