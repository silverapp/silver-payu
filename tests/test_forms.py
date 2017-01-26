import pytest
from mock import patch

from silver_payu.forms import PayUTransactionFormBase

from .fixtures import (customer, transaction, payment_method,
                       payment_processor, proforma, invoice)


@pytest.mark.django_db
@patch('silver_payu.forms.datetime')
def test_payu_transaction_form_build_body(mocked_datetime, transaction,
                                          payment_method):
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
