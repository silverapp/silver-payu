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

from ipware import get_client_ip
from rest_framework.reverse import reverse

from django.http import HttpResponse, HttpResponseNotAllowed, HttpResponseServerError
from django.views.decorators.csrf import csrf_exempt
from silver.models import Transaction

from silver.payment_processors.views import GenericTransactionView
from silver.utils.decorators import get_transaction_from_token
from silver.utils.payments import _get_jwt_token


class PayUTransactionView(GenericTransactionView):
    def get_context_data(self):
        data = super(PayUTransactionView, self).get_context_data()
        data["3ds_data_url"] = threeds_data_url(self.transaction, self.request)

        return data

    def post(self, request):
        return HttpResponse(self.render_template())


def threeds_data_url(transaction, request):
    kwargs = {'token': _get_jwt_token(transaction)}
    return reverse('silver-payu-payment-complete', kwargs=kwargs, request=request)


@csrf_exempt
@get_transaction_from_token
def threeds_data_view(request, transaction, expired=None):
    if transaction.state not in [Transaction.States.Initial, Transaction.States.Pending]:
        return HttpResponseNotAllowed()

    payment_method = transaction.payment_method
    if not payment_method:
        return HttpResponseNotAllowed()

    if payment_method.verified or payment_method.canceled:
        return HttpResponseNotAllowed()

    client_ip, _ = get_client_ip(request)
    if not client_ip:
        return HttpResponseServerError()

    threeds_data = {
        "BROWSER_IP": client_ip,
        "BROWSER_ACCEPT_HEADER": request.META.get('HTTP_ACCEPT'),
        "BROWSER_JAVA_ENABLED": request.POST.get('browser-java-enabled'),
        "BROWSER_LANGUAGE": request.POST.get('browser-language'),
        "BROWSER_COLOR_DEPTH": request.POST.get('browser-color-depth'),
        "BROWSER_SCREEN_HEIGHT": request.POST.get('browser-screen-height'),
        "BROWSER_SCREEN_WIDTH": request.POST.get('browser-screen-width'),
        "BROWSER_TIMEZONE": request.POST.get('browser-timezone'),
        "BROWSER_USER_AGENT": request.META.get('HTTP_USER_AGENT'),
    }

    payment_method.threeds_data = threeds_data
    payment_method.save()

    return HttpResponse()
