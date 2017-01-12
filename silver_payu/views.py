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

from uuid import UUID

from django_fsm import TransitionNotAllowed

from django.conf import settings
from django.http import (HttpResponseRedirect, HttpResponseBadRequest,
                         Http404, HttpResponseGone)
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_GET
from django.views.decorators.csrf import csrf_exempt

from silver.views import GenericTransactionView
from silver.models.transactions import Transaction


class PayUTransactionView(GenericTransactionView):
    pass


@require_GET
@csrf_exempt
def process_transaction(request, transaction_uuid):
    try:
        uuid = UUID(transaction_uuid, version=4)
    except ValueError:
        raise Http404

    transaction = get_object_or_404(Transaction, uuid=uuid)

    if not transaction.can_be_consumed:
        return HttpResponseGone("The transaction is no longer available.")

    transaction.last_access = timezone.now()
    transaction.save()

    redirect_url = ''
    if request.GET.get('ctrl', None):
        transaction.data['ctrl'] = request.GET['ctrl']
        transaction.payment_processor.update_transaction_status(transaction,
                                                                "pending")
        redirect_url = transaction.success_url
    else:
        error = request.GET.get('err', None) or 'Unknown error'
        transaction.data['err'] = error

        transaction.payment_processor.update_transaction_status(transaction,
                                                                "failed")
        redirect_url = transaction.failed_url

    return HttpResponseRedirect(redirect_url)
