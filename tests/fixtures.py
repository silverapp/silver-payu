import pytest

from silver import payment_processors
from silver.fixtures.factories import CustomerFactory, ProformaFactory, InvoiceFactory, \
    TransactionFactory
from silver.models import Invoice

from tests.factories import PayUPaymentMethodFactory


@pytest.fixture()
def customer():
    return CustomerFactory.create(
        address_1=u"Zalaegerszegi utca 65.\nH-5484 ligetv\xc3\xa1r", address_2='9'
    )


@pytest.fixture()
def payment_processor():
    return payment_processors.get_instance('payu_manual')


@pytest.fixture()
def payment_processor_triggered():
    return payment_processors.get_instance('payu_triggered')


@pytest.fixture()
def payment_processor_triggered_v2():
    return payment_processors.get_instance('payu_triggered_v2')


@pytest.fixture()
def payment_method(customer, payment_processor):
    return PayUPaymentMethodFactory.create(
        customer=customer,
        payment_processor=payment_processor.name
    )


@pytest.fixture()
def payment_method_triggered(customer, payment_processor_triggered):
    return PayUPaymentMethodFactory.create(
        customer=customer,
        payment_processor=payment_processor_triggered.name
    )


@pytest.fixture()
def payment_method_triggered_v2(customer, payment_processor_triggered_v2):
    return PayUPaymentMethodFactory.create(
        customer=customer,
        payment_processor=payment_processor_triggered_v2.name
    )


@pytest.fixture()
def proforma(customer):
    return ProformaFactory.create(
        state=Invoice.STATES.ISSUED,
        customer=customer,
        transaction_currency='RON'
    )


@pytest.fixture()
def invoice(customer, proforma):
    return InvoiceFactory.create(
        related_document=proforma,
        state=Invoice.STATES.ISSUED,
        customer=customer,
        transaction_currency='RON'
    )


@pytest.fixture()
def transaction(db, customer, payment_processor, payment_method, proforma, invoice):
    return TransactionFactory.create(
        invoice=invoice,
        proforma=proforma,
        currency='RON',
        amount=invoice.total,
        payment_method=payment_method
    )


@pytest.fixture()
def transaction_triggered(customer, payment_method_triggered, proforma, invoice):
    return TransactionFactory.create(
        invoice=invoice,
        proforma=proforma,
        currency='RON',
        amount=invoice.total,
        payment_method=payment_method_triggered
    )


@pytest.fixture()
def transaction_triggered_v2(customer, payment_method_triggered_v2, proforma, invoice):
    return TransactionFactory.create(
        invoice=invoice,
        proforma=proforma,
        currency='RON',
        amount=invoice.total,
        payment_method=payment_method_triggered_v2
    )
