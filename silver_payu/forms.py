from datetime import datetime
from typing import Dict, List

import pytz

from payu.forms import PayULiveUpdateForm

from django import forms

from silver.payment_processors.forms import GenericTransactionForm
from silver.utils.payments import get_payment_complete_url
from silver.utils.international import countries


class PayUTransactionFormBase(GenericTransactionForm, PayULiveUpdateForm):
    def __init__(
        self,
        payment_method,
        transaction,
        billing_details,
        request=None,
        *args,
        **kwargs,
    ):
        kwargs["initial"] = self._build_form_body(transaction, request)
        kwargs["initial"].update(billing_details)

        super(PayUTransactionFormBase, self).__init__(
            payment_method, transaction, request, **kwargs
        )

    def _build_form_body(self, transaction, request) -> Dict[str, str]:
        return {
            "ORDER_REF": str(transaction.uuid),
            "ORDER_DATE": datetime.now(pytz.UTC).strftime("%Y-%m-%d %H:%M:%S"),
            "PRICES_CURRENCY": transaction.currency,
            "CURRENCY": transaction.currency,
            "PAY_METHOD": "CCVISAMC",
            "AUTOMODE": "1",
            "BACK_REF": get_payment_complete_url(transaction, request),
            "ORDER": self._get_order(transaction),
        }

    def _get_order(self, transaction) -> List[Dict[str, str]]:
        document = transaction.document
        product_name = (
            f"Payment for {document.kind} {document.series}-{document.number}"
        )

        return [
            {
                "PNAME": product_name,
                "PCODE": f"{document.series}-{document.number}",
                "PRICE": str(transaction.amount),
                "PRICE_TYPE": "GROSS",
                "VAT": str(document.sales_tax_percent or "0"),
            }
        ]


class PayUTransactionFormManual(PayUTransactionFormBase):
    pass


class PayUTransactionFormTriggered(PayUTransactionFormBase):
    def _build_form_body(self, transaction, request):
        form_body = super(PayUTransactionFormTriggered, self)._build_form_body(
            transaction, request
        )

        form_body["LU_ENABLE_TOKEN"] = "1"

        return form_body


class PayUTransactionFormTriggeredV2(PayUTransactionFormBase):
    def _build_form_body(self, transaction, request):
        form_body = super(PayUTransactionFormTriggeredV2, self)._build_form_body(
            transaction, request
        )

        form_body["LU_ENABLE_TOKEN"] = "1"
        form_body["LU_TOKEN_TYPE"] = "PAY_ON_TIME"

        return form_body


class PayUBillingForm(GenericTransactionForm):
    email = forms.EmailField()
    first_name = forms.CharField()
    last_name = forms.CharField()
    phone = forms.CharField()
    city = forms.CharField()
    country = forms.ChoiceField(choices=countries)

    def __init__(
        self, payment_method, transaction, request=None, data=None, *args, **kwargs
    ):
        if not data:
            data = self._build_form_body(payment_method.customer)

        super(PayUBillingForm, self).__init__(
            payment_method, transaction, request, data, **kwargs
        )

    def to_payu_billing(self):
        data = self.cleaned_data
        return {
            "BILL_FNAME": data["first_name"],
            "BILL_LNAME": data["last_name"],
            "BILL_EMAIL": data["email"],
            "BILL_PHONE": data["phone"],
            "BILL_CITY": data["city"],
            "BILL_COUNTRYCODE": data["country"],
        }

    def _build_form_body(self, customer):
        form_body = {
            "first_name": customer.first_name,
            "last_name": customer.last_name,
            "email": customer.email,
            "phone": customer.phone or "",
            "country": customer.country,
            "city": customer.city,
        }

        return form_body
