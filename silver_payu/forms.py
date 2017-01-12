from payu.forms import PayULiveUpdateForm

from rest_framework.reverse import reverse

from silver.forms import GenericTransactionForm


class PayUTransactionForm(GenericTransactionForm, PayULiveUpdateForm):
    def __init__(self, payment_method, transaction,
                 request=None, *args, **kwargs):

        kwargs['initial'] = self._build_form_body(transaction, request)
        super(PayUTransactionForm, self).__init__(payment_method,
                                                  transaction,
                                                  request, **kwargs)

    def _build_form_body(self, transaction, request):
        form_body = {
            'ORDER_REF': transaction.uuid,
            'ORDER_DATE': '2017-01-06 17:12:40',
            'PRICES_CURRENCY': transaction.currency,
            'CURRENCY': transaction.currency,
            'PAY_METHOD': 'CCVISAMC',
            'AUTOMODE': '1',
            'LU_ENABLE_TOKEN': '1',
            'TESTORDER': 'TRUE',
            'BACK_REF': self._get_callback_url(transaction, request),
            'ORDER': self._get_order(transaction)
        }
        form_body.update(self._get_billing_details(transaction.document.customer))

        return form_body

    def _get_callback_url(self, transaction, request):
        return reverse('process-transaction', request=request,
                       kwargs={'transaction_uuid': str(transaction.uuid)})

    def _get_order(self, transaction):
        document = transaction.document
        product_name = 'Payment for {} {}-{}'.format(document.kind,
                                                     document.series,
                                                     document.number)
        return [{
            'PNAME': product_name,
            'PCODE': '{}-{}'.format(document.series, document.number),
            'PRICE': transaction.amount,
            'PRICE_TYPE': 'GROSS',
            'VAT': document.sales_tax_percent or '0'
        }]

    def _get_billing_details(self, customer):
        billing_name = customer.billing_name.split()

        billing_details = {
            'BILL_FNAME': billing_name[0],
            'BILL_LNAME': billing_name[1] if len(billing_name) > 1 else '',
            'BILL_COUNTRYCODE': customer.country,
            'BILL_EMAIL': customer.emails[0],
            'BILL_PHONE': ''
        }

        if customer.sales_tax_number:
            billing_details['BILL_FISCALCODE'] = customer.sales_tax_number

        return billing_details
