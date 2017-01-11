from payu.forms import PayULiveUpdateForm

from silver.forms import GenericTransactionForm


class PayUTransactionForm(GenericTransactionForm, PayULiveUpdateForm):
    def __init__(self, payment_method, transaction,
                 request=None, *args, **kwargs):

        kwargs['initial'] = self._build_form_body(transaction)
        super(PayUTransactionForm, self).__init__(payment_method,
                                                    transaction,
                                                     request, **kwargs)

    def _build_form_body(self, transaction):
        return {
            'ORDER_REF': '789456123',
            'ORDER_DATE': '2017-01-06 17:12:40',
            'PRICES_CURRENCY': 'RON',
            'CURRENCY': 'RON',
            'PAY_METHOD': 'CCVISAMC',
            'AUTOMODE': '1',
            'BILL_FNAME': 'VLAD',
            'BILL_LNAME': 'TEMIAN',
            'BILL_COUNTRYCODE': 'RO',
            'BILL_PHONE': '+000000000000',
            'BILL_EMAIL': 'vladtemian@gmail.com',
            'LU_ENABLE_TOKEN': '1',
            'ORDER': [{
                'PNAME': 'CD Player',
                'PCODE': 'PROD_04891',
                'PINFO': 'Extended Warranty - 5 Years',
                'PRICE': '1',
                'PRICE_TYPE': 'GROSS',
                'QTY': '1',
                'VAT':'19'
            }]
        }
