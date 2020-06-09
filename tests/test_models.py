import pytest
from faker import Faker
from mock import MagicMock, patch
from django_dynamic_fixture import G

from django.utils.dateparse import parse_datetime

from silver.models import Transaction, PaymentMethod
from silver_payu.forms import PayUBillingForm, PayUTransactionFormBase
from silver_payu.models import PayUPaymentMethod
from silver_payu.payment_processors import payu_ipn_received, payu_token_received

from .fixtures import *

faker = Faker()


def test_payment_method_data_set():
    payment_method = PayUPaymentMethod()

    payment_method.decrypt_data = lambda value: value
    payment_method.encrypt_data = lambda value: value

    payment_method.token = "random token"
    assert payment_method.token == "random token"

    payment_method.archived_customer = {'name': 'test'}
    assert payment_method.archived_customer == {'name': 'test'}


@pytest.mark.django_db
def test_execute_transaction_wrong_payment_processor(payment_processor_triggered,
                                                     transaction_triggered):
    assert not payment_processor_triggered.execute_transaction(transaction_triggered)


@pytest.mark.django_db
def test_execute_transaction_wrong_transaction_state(payment_processor_triggered):
    payment_processor_triggered._charge_transaction = lambda x: True

    transaction_triggered = MagicMock(payment_processor=payment_processor_triggered,
                                      state=Transaction.States.Settled)
    assert not payment_processor_triggered.execute_transaction(transaction_triggered)


@pytest.mark.django_db
def test_execute_transaction_happy_path(payment_processor_triggered):
    payment_processor_triggered._charge_transaction = lambda x: True

    transaction_triggered = MagicMock(payment_processor=payment_processor_triggered,
                                      state=Transaction.States.Pending)
    assert payment_processor_triggered.execute_transaction(transaction_triggered)


@pytest.mark.django_db
@patch('silver_payu.payment_processors.TokenPayment')
def test_charge_transaction_triggered(mocked_token_payment,
                                      payment_processor_triggered,
                                      payment_method, transaction_triggered):
    mocked_token_payment.return_value.pay.return_value = '{"code": "0"}'

    payment_method.token = faker.word()
    payment_method.archived_customer = {
        "BILL_ADDRESS": faker.address(),
        "BILL_CITY": faker.city(),
        "BILL_EMAIL": faker.email(),
        "BILL_FNAME": faker.first_name(),
        "BILL_LNAME": faker.last_name(),
        "BILL_PHONE": faker.phone_number(),
    }

    assert payment_processor_triggered._charge_transaction(transaction_triggered)

    asserted_payment_details = payment_method.archived_customer
    asserted_payment_details.update({
        "DELIVERY_ADDRESS": asserted_payment_details["BILL_ADDRESS"],
        "DELIVERY_CITY": asserted_payment_details["BILL_CITY"],
        "DELIVERY_EMAIL": asserted_payment_details["BILL_EMAIL"],
        "DELIVERY_FNAME": asserted_payment_details["BILL_FNAME"],
        "DELIVERY_LNAME": asserted_payment_details["BILL_LNAME"],
        "DELIVERY_PHONE": asserted_payment_details["BILL_PHONE"],
        "AMOUNT": str(transaction_triggered.amount),
        "CURRENCY": str(transaction_triggered.currency),
        "EXTERNAL_REF": str(transaction_triggered.uuid),
    })

    mocked_token_payment.assert_called_once_with(asserted_payment_details,
                                                 payment_method.token)


@pytest.mark.django_db
@pytest.mark.parametrize('payment_result, excepted_return', [
    ('{"code": "0"}', True),
    ('{"code": "1"}', False),
    ('{code: "1"}', False),
])
def test_parse_token_payment_result(payment_processor_triggered,
                                    transaction_triggered, payment_result,
                                    excepted_return):
    assert payment_processor_triggered._parse_result(transaction_triggered,
                                                     payment_result) == excepted_return


@pytest.mark.django_db
@patch('silver.models.transactions.transaction.Transaction.update_document_state')
def test_ipn_received(mocked_document, transaction):
    payu_ipn_received(MagicMock(REFNOEXT=transaction.uuid))

    transaction.refresh_from_db()

    assert transaction.state == "settled"


@pytest.mark.django_db
def test_token_received(transaction_triggered):
    sender = MagicMock(ipn=MagicMock(REFNOEXT=transaction_triggered.uuid),
                       IPN_CC_TOKEN=faker.word(), IPN_CC_EXP_DATE='2017-07-31',
                       IPN_CC_MASK=faker.word())
    payu_token_received(sender)

    transaction_triggered.payment_method.refresh_from_db()

    expected_valid_until = parse_datetime(sender.IPN_CC_EXP_DATE + " 00:00:00")
    assert transaction_triggered.payment_method.valid_until == expected_valid_until
    assert transaction_triggered.payment_method.token == sender.IPN_CC_TOKEN
    assert transaction_triggered.payment_method.display_info == sender.IPN_CC_MASK
    assert transaction_triggered.payment_method.verified


@pytest.mark.django_db
def test_token_v2_received(transaction_triggered_v2):
    sender = MagicMock(ipn=MagicMock(REFNOEXT=transaction_triggered_v2.uuid),
                       IPN_CC_TOKEN=faker.word(), TOKEN_HASH=faker.word(),
                       IPN_CC_EXP_DATE='2017-07-31', IPN_CC_MASK=faker.word())
    payu_token_received(sender)

    transaction_triggered_v2.payment_method.refresh_from_db()

    expected_valid_until = parse_datetime(sender.IPN_CC_EXP_DATE + " 00:00:00")
    assert transaction_triggered_v2.payment_method.valid_until == expected_valid_until
    assert transaction_triggered_v2.payment_method.token == sender.TOKEN_HASH
    assert transaction_triggered_v2.payment_method.display_info == sender.IPN_CC_MASK
    assert transaction_triggered_v2.payment_method.verified
