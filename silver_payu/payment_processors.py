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
from xml.etree import ElementTree

from django.conf import settings
from django.db import transaction as django_transaction
from django.dispatch import receiver
from django_fsm import TransitionNotAllowed
from payu.payments import ALUPayment, TokenPayment
from payu.signals import payment_authorized, alu_token_created, payment_completed
from silver.models import Transaction
from silver.payment_processors import PaymentProcessorBase
from silver.payment_processors.mixins import (
    TriggeredProcessorMixin,
    ManualProcessorMixin,
)

from silver_payu.errors import TOKEN_ERROR_CODES, ALU_ERROR_CODES
from silver_payu.forms import (
    PayUTransactionFormManual,
    PayUTransactionFormTriggered,
    PayUBillingForm,
    PayUTransactionFormTriggeredV2,
)
from silver_payu.models import PayUPaymentMethod
from silver_payu.views import PayUTransactionView


class PayUBase(PaymentProcessorBase):
    payment_method_class = PayUPaymentMethod
    transaction_view_class = PayUTransactionView
    allowed_currencies = ("RON", "USD", "EUR")

    _has_been_setup = False

    def get_form(self, transaction, request):
        form = PayUBillingForm(
            payment_method=transaction.payment_method,
            transaction=transaction,
            request=request,
            data=request.POST,
        )

        if form.is_valid():
            if not transaction.payment_method.archived_customer:
                customer = transaction.document.customer
                address = f"{customer.address_1} {customer.address_2}"

                archived_customer = form.to_payu_billing()
                archived_customer["BILL_ADDRESS"] = address

                transaction.payment_method.archived_customer = archived_customer
                transaction.payment_method.save()

            form = self.form_class(
                payment_method=transaction.payment_method,
                transaction=transaction,
                request=request,
                billing_details=form.to_payu_billing(),
            )

        return form

    def refund_transaction(self, transaction, payment_method=None):
        pass

    def void_transaction(self, transaction, payment_method=None):
        pass

    def handle_transaction_response(self, transaction, request):
        with django_transaction.atomic():
            Transaction.objects.select_for_update().filter(pk=transaction.pk).get()
            transaction.refresh_from_db()

            try:
                if request.GET.get("ctrl", None):
                    transaction.data["ctrl"] = request.GET["ctrl"]
                    transaction.process()
                else:
                    error = request.GET.get("err", None) or "Unknown error"
                    transaction.fail(fail_reason=error)
            except TransitionNotAllowed:
                pass

            transaction.save()


class PayUManual(PayUBase, ManualProcessorMixin):
    template_slug = "payu_manual"
    form_class = PayUTransactionFormManual


class PayUTriggered(PayUBase, TriggeredProcessorMixin):
    """
    Uses TokenV1 API for recurrent payments.
    """

    template_slug = "payu_triggered"
    form_class = PayUTransactionFormTriggered

    def execute_transaction(self, transaction):
        """
        :param transaction: A PayU transaction in Initial or Pending state.
        :return: True on success, False on failure.
        """

        if transaction.state != Transaction.States.Pending:
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
                "DELIVERY_PHONE": billing_details["BILL_PHONE"],
            }
        except KeyError as error:
            transaction.fail(fail_reason=f"Invalid customer details. [{error}]")
            transaction.save()
            return False

        payment_details = {
            "AMOUNT": str(transaction.amount),
            "CURRENCY": str(transaction.currency),
            "EXTERNAL_REF": str(transaction.uuid),
        }
        payment_details.update(billing_details)
        payment_details.update(delivery_details)

        payment = TokenPayment(payment_details, token)

        try:
            result = payment.pay()
        except Exception as error:
            transaction.fail(fail_reason=str(error))
            transaction.save()
            return False

        return self._parse_result(transaction, result)

    def _parse_result(self, transaction, result):
        try:
            result = json.loads(result)

            if "code" in result and not int(result["code"]):
                return True

            error_code, error_reason = self._parse_response_error(result)
            transaction.fail(fail_code=error_code, fail_reason=error_reason)
        except ValueError as error:
            transaction.fail(fail_reason=str(error))

        transaction.save()

        return False

    def _parse_response_error(self, payu_response):
        if not isinstance(payu_response, dict) or "code" not in payu_response:
            return "default", f"Missing payu error code.({payu_response})"

        if str(payu_response["code"]) in TOKEN_ERROR_CODES:
            error = TOKEN_ERROR_CODES[str(payu_response["code"])]
            return error["silver_code"], error["reason"]

        return "default", f'Unknown error code {payu_response["code"]}'


class PayUTriggeredV2(PayUBase, TriggeredProcessorMixin):
    """
    Uses ALUPaymentV3 API for recurrent payments.
    """

    template_slug = "payu_triggered"
    form_class = PayUTransactionFormTriggeredV2

    def execute_transaction(self, transaction):
        """
        :param transaction: A PayU transaction in Initial or Pending state.
        :return: True on success, False on failure.
        """

        if transaction.state != Transaction.States.Pending:
            return False

        return self._charge_transaction(transaction)

    def _charge_transaction(self, transaction):
        payment_method = transaction.payment_method
        token = payment_method.token

        customer_details = payment_method.archived_customer
        try:
            delivery_details = {
                "DELIVERY_ADDRESS": customer_details["BILL_ADDRESS"],
                "DELIVERY_CITY": customer_details["BILL_CITY"],
                "DELIVERY_EMAIL": customer_details["BILL_EMAIL"],
                "DELIVERY_FNAME": customer_details["BILL_FNAME"],
                "DELIVERY_LNAME": customer_details["BILL_LNAME"],
                "DELIVERY_PHONE": customer_details["BILL_PHONE"],
            }
        except KeyError as error:
            transaction.fail(fail_reason=f"Invalid customer details. [{error}]")
            transaction.save()
            return False

        payment_details = {
            "PRICES_CURRENCY": str(transaction.currency),
            "ORDER_REF": str(transaction.uuid),
            "PAY_METHOD": "CCVISAMC",
        }

        if transaction.document:
            pname = "{provider} {doc_type} {doc_number}".format(
                doc_type=transaction.document.kind,
                doc_number=transaction.document.series_number,
                provider=transaction.provider.name,
            )

            vat = str(int(transaction.document.sales_tax_percent or 0))
            price_type = "GROSS"  # (VAT included)
        else:
            pname = f"Payment for {transaction.provider.name}"

            vat = "0"
            price_type = "NET"  # (VAT will be added by PayU)

        order_details = [
            {
                "PNAME": pname,
                "PCODE": str(transaction.uuid),
                "PRICE": str(transaction.amount),
                "VAT": vat,
                "PRICE_TYPE": price_type,
                "QTY": "1",
            }
        ]

        payment_details.update(customer_details)
        payment_details.update(delivery_details)
        payment_details["ORDER"] = order_details

        payment = ALUPayment(
            payment_details,
            token,
            stored_credentials_use_type="merchant",
            threeds_data=payment_method.threeds_data,
        )

        try:
            result = payment.pay()
        except Exception as error:
            transaction.fail(fail_reason=str(error))
            self._log_request_response(transaction, payment)

            transaction.save()

            return False

        return self._parse_result(transaction, result, payment)

    def _log_request_response(self, transaction, payment):
        if not payment:
            return

        request = getattr(payment, "_request", {})
        redacted_fields = ["CC_TOKEN", "CC_CVV"]

        if getattr(settings, "SILVER_PAYU_REDACT_PII", False):
            redacted_fields += [
                "BROWSER_IP",
                "BILL_ADDRESS",
                "BILL_CITY",
                "BILL_PHONE",
                "BILL_FNAME",
                "BILL_LNAME",
                "BILL_EMAIL",
            ]

        for field in redacted_fields:
            if request.get(field):
                request[field] = "[REDACTED]"

        transaction.data["_request"] = str(request)

        if transaction.state == Transaction.States.Failed:
            response = getattr(payment, "_response", "")
            if isinstance(response, bytes):
                response = response.decode("utf-8")

            transaction.data["_response"] = str(response)

    def _parse_result(self, transaction, result, payment=None):
        try:
            element = ElementTree.fromstring(result)
            status = element.find("STATUS").text
            return_code = element.find("RETURN_CODE").text

            if status == "SUCCESS":
                self._log_request_response(transaction, payment)
                transaction.save()

                return True

            error_code, error_reason = self._parse_response_error(return_code)
            transaction.data.update(
                {
                    "status": status,
                    "message": error_reason,
                    "return_code": return_code,
                }
            )

            return_message = element.find("RETURN_MESSAGE")
            if return_message is not None:
                transaction.data["return_message"] = return_message.text

            transaction.fail(fail_code=error_code, fail_reason=error_reason)
        except ValueError as error:
            transaction.fail(fail_reason=str(error))

        self._log_request_response(transaction, payment)
        transaction.save()

        return False

    def _parse_response_error(self, return_code):
        if str(return_code) in ALU_ERROR_CODES:
            error = ALU_ERROR_CODES[str(return_code)]
            return error["silver_code"], error["reason"]

        return "default", f"Unknown error code {return_code}"


@receiver([payment_authorized, payment_completed])
def payu_ipn_received(sender, **kwargs):
    transaction = Transaction.objects.get(uuid=sender.REFNOEXT)

    try:
        if transaction.state != Transaction.States.Settled:
            transaction.settle()
            transaction.save()
    except TransitionNotAllowed as error:
        try:
            transaction.fail(fail_reason=str(error))
            transaction.save()
        except TransitionNotAllowed:
            transaction.fail_reason = str(error)
            transaction.save()

        raise


@receiver(alu_token_created)
def payu_token_received(sender, **kwargs):
    transaction = Transaction.objects.get(uuid=sender.ipn.REFNOEXT)
    payment_method = PayUPaymentMethod.objects.get(pk=transaction.payment_method_id)

    payment_processor = payment_method.get_payment_processor()
    if payment_processor.__class__ is PayUTriggered:
        payment_method.token = sender.IPN_CC_TOKEN
    elif payment_processor.__class__ is PayUTriggeredV2:
        if not sender.TOKEN_HASH:
            return
        payment_method.token = sender.TOKEN_HASH
    else:
        # no other PayU payment processor implementation expects tokens
        return

    payment_method.verified = True
    payment_method.display_info = sender.IPN_CC_MASK
    payment_method.valid_until = sender.IPN_CC_EXP_DATE
    payment_method.save()
