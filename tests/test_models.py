import pytest
from faker import Faker
from mock import MagicMock, patch
from django_dynamic_fixture import G

from silver.models import (Transaction, Proforma, Invoice, Customer,
                           PaymentProcessorManager)

from silver_payu.models import (PayUPaymentMethod, PayUTriggered,
                                payu_ipn_received, payu_token_received)
from silver_payu.forms import PayUBillingForm, PayUTransactionFormBase

from .fixtures import (customer, transaction, transaction_triggered,
                       payment_method, proforma, invoice,
                       payment_processor, payment_processor_triggered)

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
@pytest.mark.parametrize('data, form_class, archived_customer', [
    ({
        'email': faker.email(),
        'first_name': faker.first_name(),
        'last_name': faker.last_name(),
        'phone': faker.phone_number(),
        'country': '',
        'fiscal_code': ''
    }, PayUBillingForm, {}),
    ({
        'email': 'john@acme.com',
        'first_name': 'John',
        'last_name': 'Doe',
        'phone': '+40000000000',
        'country': 'RO',
        'city': 'Timisoara',
        'fiscal_code': ''
    }, PayUTransactionFormBase, {
        'BILL_ADDRESS': '9 9',
        'BILL_CITY': 'Timisoara',
        'BILL_COUNTRYCODE': 'RO',
        'BILL_EMAIL': 'john@acme.com',
        'BILL_FNAME': 'John',
        'BILL_LNAME': 'Doe',
        'BILL_PHONE': '+40000000000'
    })
])
def test_payment_processor_get_form(payment_processor, transaction, data,
                                    form_class, archived_customer):
    form = payment_processor.get_form(transaction, MagicMock(POST=data))

    assert isinstance(form, form_class)
    assert transaction.payment_method.archived_customer == archived_customer


@pytest.mark.django_db
@pytest.mark.parametrize('initial_state, status, asserted_state', [
    (Transaction.States.Initial, "pending", Transaction.States.Pending),
    (Transaction.States.Initial, "failed", Transaction.States.Failed),
    (Transaction.States.Pending, "settle", Transaction.States.Settled),
    (Transaction.States.Settled, "pending", Transaction.States.Settled)
])
def test_update_transaction(invoice, payment_processor, payment_method, proforma,
                            initial_state, status, asserted_state):
    invoice.pay = lambda : ''
    transaction = G(Transaction, state=initial_state, invoice=invoice,
                    currency=invoice.transaction_currency, amount=invoice.total,
                    payment_method=payment_method, proforma=proforma)

    payment_processor.update_transaction_status(transaction, status)
    transaction.refresh_from_db()

    assert transaction.state == asserted_state


@pytest.mark.django_db
def test_execute_transaction_wrong_payment_processor(payment_processor_triggered, transaction_triggered):
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
                                      state=Transaction.States.Initial)
    assert payment_processor_triggered.execute_transaction(transaction_triggered)


@pytest.mark.django_db
@patch('silver_payu.models.payment_processors.TokenPayment')
def test_charge_transaction_triggered(mocked_token_payment,
                                      payment_processor_triggered,
                                      payment_method, transaction_triggered):
    mocked_token_payment.return_value.pay.return_value = '{"code": "0"}'

    payment_method.token = faker.word
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
    assert payment_processor_triggered._parse_result(transaction_triggered, payment_result) == excepted_return


@pytest.mark.django_db
@patch('silver.models.transactions._sync_transaction_state_with_document')
def test_ipn_received(mocked_sync, transaction):
    payu_ipn_received(MagicMock(REFNOEXT=transaction.uuid))

    transaction.refresh_from_db()

    assert transaction.state == "settled"


@pytest.mark.django_db
def test_token_received(transaction_triggered):
    sender = MagicMock(ipn=MagicMock(REFNOEXT=transaction_triggered.uuid),
                       IPN_CC_TOKEN=faker.word())
    payu_token_received(sender)

    transaction_triggered.payment_method.refresh_from_db()

    assert transaction_triggered.payment_method.token == sender.IPN_CC_TOKEN
    assert transaction_triggered.payment_method.verified
