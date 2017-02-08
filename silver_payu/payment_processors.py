# Copyright (c) 2017 Presslabs SRL
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import json

from django_fsm import TransitionNotAllowed

from django.dispatch import receiver
from django.utils.dateparse import parse_datetime

from payu.payments import TokenPayment
from payu.signals import payment_authorized, alu_token_created

from silver.models import Transaction
from silver.payment_processors import PaymentProcessorBase
from silver.payment_processors.mixins import (TriggeredProcessorMixin,
                                              ManualProcessorMixin)

from silver_payu.errors import ERROR_CODES
from silver_payu.views import PayUTransactionView
from silver_payu.forms import (PayUTransactionFormManual,
                               PayUTransactionFormTriggered, PayUBillingForm)
from silver_payu.models import PayUPaymentMethod


class PayUBase(PaymentProcessorBase):
    payment_method_class = PayUPaymentMethod
    transaction_view_class = PayUTransactionView
    allowed_currencies = ('RON', 'USD', 'EUR')

    _has_been_setup = False

    def get_form(self, transaction, request):
        form = PayUBillingForm(payment_method=transaction.payment_method,
                               transaction=transaction, request=request,
                               data=request.POST)

        if form.is_valid():
            if not transaction.payment_method.archived_customer:
                address = "{} {}".format(transaction.document.customer.address_1,
                                         transaction.document.customer.address_2)

                archived_customer = form.to_payu_billing()
                archived_customer['BILL_ADDRESS'] = address

                tax_number = transaction.document.customer.sales_tax_number
                if tax_number:
                    archived_customer['BILL_FISCALCODE'] = tax_number

                transaction.payment_method.archived_customer = archived_customer
                transaction.payment_method.save()

            form = self.form_class(payment_method=transaction.payment_method,
                                   transaction=transaction, request=request,
                                   billing_details=form.to_payu_billing())

        return form

    def refund_transaction(self, transaction, payment_method=None):
        pass

    def void_transaction(self, transaction, payment_method=None):
        pass

    def handle_transaction_response(self, transaction, request):
        try:
            if request.GET.get('ctrl', None):
                transaction.data['ctrl'] = request.GET['ctrl']
                transaction.process()
            else:
                error = request.GET.get('err', None) or 'Unknown error'
                transaction.fail(fail_reason=error)
        except TransitionNotAllowed:
            pass

        transaction.save()


class PayUManual(PayUBase, ManualProcessorMixin):
    template_slug = 'payu_manual'
    form_class = PayUTransactionFormManual


class PayUTriggered(PayUBase, TriggeredProcessorMixin):
    template_slug = 'payu_triggered'
    form_class = PayUTransactionFormTriggered

    def execute_transaction(self, transaction):
        """
        :param transaction: A PayU transaction in Initial or Pending state.
        :return: True on success, False on failure.
        """

        if transaction.state not in [Transaction.States.Initial,
                                     Transaction.States.Pending]:
            return False

        return self._charge_transaction(transaction)

    def _charge_transaction(self, transaction):
        token = transaction.payment_method.token

        billing_details = transaction.payment_method.archived_customer
        try:
            delivery_details = {
                "DELIVERY_ADDRESS": billing_details["BILL_ADDRESS"],
                "DELIVERY_CITY": billing_details["BILL_CITY"],
                "DELIVERY_EMAIL": billing_details["BILL_EMAIL"],
                "DELIVERY_FNAME": billing_details["BILL_FNAME"],
                "DELIVERY_LNAME": billing_details["BILL_LNAME"],
                "DELIVERY_PHONE": billing_details["BILL_PHONE"]
            }
        except KeyError as error:
            transaction.fail(fail_reason='Invalid customer details. [{}]'.format(error))
            transaction.save()
            return False

        payment_details = {
            "AMOUNT": str(transaction.amount),
            "CURRENCY": str(transaction.currency),
            "EXTERNAL_REF": str(transaction.uuid)
        }
        payment_details.update(billing_details)
        payment_details.update(delivery_details)

        payment = TokenPayment(payment_details, token)

        try:
            result = payment.pay()
        except Exception as error:
            return False

        return self._parse_result(transaction, result)

    def _parse_result(self, transaction, result):
        try:
            result = json.loads(result)

            if "code" in result and not int(result["code"]):
                transaction.process()
                transaction.save()
                return True
            else:
                error_code, error_reason = self._parse_response_error(result)
                transaction.fail(fail_code=error_code, fail_reason=error_reason)
        except ValueError as error:
            transaction.fail(fail_reason=str(error))

        transaction.save()

        return False

    def _parse_response_error(self, payu_response):
        if not isinstance(payu_response, dict) or 'code' not in payu_response:
            return 'default', 'Missing payu error code.({})'.format(payu_response)

        if str(payu_response['code']) in ERROR_CODES:
            error = ERROR_CODES[str(payu_response['code'])]
            return error['silver_code'], error['reason']

        return 'default', 'Unknown error code {}'.format(payu_response['code'])


@receiver(payment_authorized)
def payu_ipn_received(sender, **kwargs):
    transaction = Transaction.objects.get(uuid=sender.REFNOEXT)

    try:
        transaction.settle()
        transaction.save()
    except TransitionNotAllowed as error:
        try:
            transaction.fail(fail_reason=str(error))
            transaction.save()
        except TransitionNotAllowed:
            transaction.fail_reason = str(error)
            transaction.save()


@receiver(alu_token_created)
def payu_token_received(sender, **kwargs):
    transaction = Transaction.objects.get(uuid=sender.ipn.REFNOEXT)
    payment_method = PayUPaymentMethod.objects.get(pk=transaction.payment_method_id)

    payment_method.token = sender.IPN_CC_TOKEN
    payment_method.verified = True
    payment_method.display_info = sender.IPN_CC_MASK
    payment_method.valid_until = sender.IPN_CC_EXP_DATE
    payment_method.save()
