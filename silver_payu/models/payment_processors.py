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

from django_fsm import TransitionNotAllowed

from django.utils import timezone
from django.dispatch import receiver

from payu.payments import TokenPayment
from payu.signals import payment_authorized, alu_token_created

from silver.models import Transaction
from silver.models.payment_processors.base import PaymentProcessorBase
from silver.models.payment_processors.mixins import TriggeredProcessorMixin

from .payment_methods import PayUPaymentMethod

from ..views import PayUTransactionView
from ..forms import PayUTransactionForm, PayUBillingForm


class PayUTriggered(PaymentProcessorBase, TriggeredProcessorMixin):
    reference = 'payu_triggered'
    form_class = PayUTransactionForm
    payment_method_class = PayUPaymentMethod
    transaction_view_class = PayUTransactionView

    _has_been_setup = False

    def get_form(self, transaction, request):
        form = PayUBillingForm(payment_method=transaction.payment_method,
                               transaction=transaction, request=request,
                               data=request.POST)

        if form.is_valid():
            form = PayUTransactionForm(payment_method=transaction.payment_method,
                                       transaction=transaction,
                                       billing_details=form.to_payu_billing())

        return form

    def refund_transaction(self, transaction, payment_method=None):
        pass

    def void_transaction(self, transaction, payment_method=None):
        pass

    def update_transaction_status(self, transaction, status):
        try:
            if status == "pending":
                transaction.process()
            elif status == "failed":
                transaction.process()
                transaction.fail()
            elif status == "settle":
                transaction.settle()
        except TransitionNotAllowed as e:
            # TODO handle this (probably throw something else)
            pass

        transaction.save()

    def execute_transaction(self, transaction):
        """
        :param transaction: A PayU transaction in Initial or Pending state.
        :return: True on success, False on failure.
        """

        if not transaction.payment_processor == self:
            return False

        if transaction.state not in [transaction.States.Initial,
                                     transaction.States.Pending]:
            return False

        return self._charge_transaction(transaction)

    def _charge_transaction(self, transaction):
        token = transaction.payment_method.token
        billing_name = transaction.document.customer.billing_name.split()
        address = "{} {}".format(transaction.document.customer.address1,
                                 transaction.document.customer.address2)

        print transaction.document.customer.emails
        print transaction.document.customer.emails[0]

        payment = TokenPayment({
            "AMOUNT": transaction.amount,
            "CURRENCY": transaction.currency,
            "BILL_ADDRESS": address,
            "BILL_CITY": transaction.document.customer.city,
            "BILL_EMAIL": transaction.document.customer.emails[0],
            "BILL_FNAME": billing_name[0],
            "BILL_LNAME": billing_name[1],
            "BILL_PHONE": "+40000000000",
            "EXTERNAL_REF": str(transaction.uuid),
        }, token)
        result = payment.pay()

        print result

        return True


@receiver(payment_authorized)
def payu_ipn_received(sender, **kwargs):
    transaction = Transaction.objects.get(uuid=sender.REFNOEXT)
    transaction.payment_processor.update_transaction_status(transaction,
                                                            "settle")


@receiver(alu_token_created)
def payu_token_received(sender, **kwargs):
    transaction = Transaction.objects.get(uuid=sender.ipn.REFNOEXT)

    transaction.payment_method.token = sender.IPN_CC_TOKEN
    transaction.payment_method.save()
