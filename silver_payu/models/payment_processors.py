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

from silver.models.payment_processors.base import PaymentProcessorBase
from silver.models.payment_processors.mixins import TriggeredProcessorMixin

from .payment_methods import PayUPaymentMethod

from ..views import PayUTransactionView
from ..forms import PayUTransactionForm


class PayUTriggered(PaymentProcessorBase, TriggeredProcessorMixin):
    reference = 'payu_triggered'
    form_class = PayUTransactionForm
    payment_method_class = PayUPaymentMethod
    transaction_view_class = PayUTransactionView

    _has_been_setup = False

    def refund_transaction(self, transaction, payment_method=None):
        pass

    def void_transaction(self, transaction, payment_method=None):
        pass

    def _update_payment_method(self, payment_method, result_details,
                               instrument_type):
        """
        :param payment_method: A PayUPaymentMethod.
        :param result_details: A (part of) payuSDK result(response)
                               containing payment method information.
        :param instrument_type: The type of the instrument (payment method);
                                see PayUPaymentMethod.Types.
        :description: Updates a given payment method's data with data from a
                      payuSDK result payment method.
        """
        payment_method.save()

    def _update_transaction_status(self, transaction, result_transaction):
        """
        :param transaction: A Transaction.
        :param result_transaction: A transaction from a payuSDK
                                      result(response).
        :description: Updates a given transaction's data with data from a
                      payuSDK result payment method.
        """
        if not transaction.data:
            transaction.data = {}

        try:
            transaction.process()

            if status in [payu.Transaction.Status.AuthorizationExpired,
                          payu.Transaction.Status.SettlementDeclined,
                          payu.Transaction.Status.Failed,
                          payu.Transaction.Status.GatewayRejected,
                          payu.Transaction.Status.ProcessorDeclined]:
                if transaction.state != transaction.States.Failed:
                    transaction.fail()

            elif status == payu.Transaction.Status.Voided:
                if transaction.state != transaction.States.Canceled:
                    transaction.cancel()

            elif status in [payu.Transaction.Status.Settling,
                            payu.Transaction.Status.SettlementPending,
                            payu.Transaction.Status.Settled]:
                if transaction.state != transaction.States.Settled:
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

        return True
