from datetime import datetime

import pytz

from payu.forms import PayULiveUpdateForm

from django import forms
from rest_framework.reverse import reverse

from silver.forms import GenericTransactionForm
from silver.utils.international import countries


class PayUTransactionForm(GenericTransactionForm, PayULiveUpdateForm):
    def __init__(self, payment_method, transaction, billing_details,
                 request=None, *args, **kwargs):

        kwargs['initial'] = self._build_form_body(transaction, request)
        kwargs['initial'].update(billing_details)

        super(PayUTransactionForm, self).__init__(payment_method,
                                                  transaction,
                                                  request, **kwargs)

    def _build_form_body(self, transaction, request):
        form_body = {
            'ORDER_REF': str(transaction.uuid),
            'ORDER_DATE':  datetime.now(pytz.UTC).strftime('%Y-%m-%d %H:%M:%S'),
            'PRICES_CURRENCY': transaction.currency,
            'CURRENCY': transaction.currency,
            'PAY_METHOD': 'CCVISAMC',
            'AUTOMODE': '1',
            'LU_ENABLE_TOKEN': '1',
            'BACK_REF': self._get_callback_url(transaction, request),
            'ORDER': self._get_order(transaction)
        }

        return form_body

    def _get_callback_url(self, transaction, request):
        return reverse('process-transaction',
                       kwargs={'transaction_uuid': str(transaction.uuid)},
                       request=request)

    def _get_order(self, transaction):
        document = transaction.document
        product_name = 'Payment for {} {}-{}'.format(document.kind,
                                                     document.series,
                                                     document.number)
        return [{
            'PNAME': product_name,
            'PCODE': '{}-{}'.format(document.series, document.number),
            'PRICE': str(transaction.amount),
            'PRICE_TYPE': 'GROSS',
            'VAT': str(document.sales_tax_percent) or '0'
        }]


class PayUBillingForm(GenericTransactionForm):
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone = forms.CharField()
    city = forms.CharField()
    country = forms.ChoiceField(choices=countries)
    fiscal_code = forms.CharField(required=False)

    def __init__(self, payment_method, transaction,
                 request=None, data=None, *args, **kwargs):

        if not data:
            data = self._build_form_body(payment_method.customer)

        super(PayUBillingForm, self).__init__(payment_method, transaction,
                                              request, data, **kwargs)
    def to_payu_billing(self):
        data = self.cleaned_data
        return {
            'BILL_FNAME': data['first_name'],
            'BILL_LNAME': data['last_name'],
            'BILL_EMAIL': data['email'],
            'BILL_PHONE': data['phone'],
            'BILL_CITY': data['city'],
            'BILL_COUNTRYCODE': data['country'],
            'BILL_FISCALCODE': data['fiscal_code']
        }

    def _build_form_body(self, customer):
        billing_name = customer.billing_name.split()

        form_body = {
            'first_name': billing_name[0],
            'last_name': billing_name[1] if len(billing_name) > 1 else '',
            'email': customer.email or '',
            'phone': customer.phone or '',
            'country': customer.country,
            'city': customer.city
        }

        if customer.sales_tax_number:
            form_body['fiscal_code'] = customer.sales_tax_number

        return form_body
