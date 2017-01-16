import pytest
from faker import Faker
from mock import MagicMock, patch
from django_dynamic_fixture import G

from silver.models import Transaction, Proforma, Invoice

from silver_payu.models import (PayUPaymentMethod, PayUTriggered,
                                payu_ipn_received, payu_token_received)
from silver_payu.forms import PayUBillingForm, PayUTransactionForm

faker = Faker()


@pytest.mark.django_db
@patch('silver_payu.forms.datetime')
def test_payu_transaction_form_build_body(mocked_datetime):
    mocked_datetime.now.return_value.strftime.return_value = 'order_date'

    transaction = G(Transaction)
    payment_method = G(PayUPaymentMethod)
    form = PayUTransactionForm(payment_method, transaction, {})

    assert form._build_form_body(transaction, None) == {
        'AUTOMODE': '1',
        'BACK_REF': u'/%s/proccess' % transaction.uuid,
        'CURRENCY': 'USD',
        'LU_ENABLE_TOKEN': '1',
        'ORDER': [{'PCODE': '%s-%s' % (transaction.document.series,
                                       transaction.document.number),
                   'PNAME': 'Payment for %s %s-%s' % (transaction.document.kind,
                                                      transaction.document.series,
                                                      transaction.document.number),
                   'PRICE': str(transaction.amount),
                   'PRICE_TYPE': 'GROSS',
                   'VAT': str(transaction.sales_tax_percent)}],
        'ORDER_DATE': 'order_date',
        'ORDER_REF': '%s' % transaction.uuid,
        'PAY_METHOD': 'CCVISAMC',
        'PRICES_CURRENCY': 'USD'
    }
