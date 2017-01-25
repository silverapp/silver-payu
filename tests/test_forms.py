import pytest
from mock import MagicMock, patch
from django_dynamic_fixture import G

from silver.models import (Transaction, Proforma, Invoice, Customer,
                           PaymentProcessorManager)

from silver_payu.models import (PayUPaymentMethod, PayUTriggered,
                                payu_ipn_received, payu_token_received)
from silver_payu.forms import PayUTransactionFormBase


@pytest.mark.django_db
@patch('silver_payu.forms.datetime')
def test_payu_transaction_form_build_body(mocked_datetime):
    mocked_datetime.now.return_value.strftime.return_value = 'order_date'

    customer = G(Customer, currency='RON')
    payment_processor = PaymentProcessorManager.get_instance('payu_triggered')
    payment_method = G(PayUPaymentMethod, customer=customer,
                       payment_processor=payment_processor)
    proforma = G(Proforma, state=Invoice.STATES.ISSUED, customer=customer,
                 transaction_currency='RON')
    invoice = G(Invoice, proforma=proforma, state=Invoice.STATES.ISSUED,
                customer=customer, transaction_currency='RON')
    transaction = G(Transaction, invoice=invoice, proforma=proforma,
                    amount=invoice.total,
                    payment_method=payment_method, currency='RON')

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
