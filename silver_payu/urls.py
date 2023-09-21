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


from django.conf.urls import include
from django.urls import re_path

from silver.views import pay_transaction_view, complete_payment_view

from silver_payu.views import threeds_data_view


urlpatterns = [
    re_path(r"^", include("payu.urls")),
    re_path(r"pay/(?P<token>[0-9a-zA-Z-_\.]+)/$", pay_transaction_view, name="payment"),
    re_path(
        r"pay/(?P<token>[0-9a-zA-Z-_\.]+)/complete$",
        complete_payment_view,
        name="payment-complete",
    ),
    re_path(
        r"silver-payu/3ds_data/(?P<token>[0-9a-zA-Z-_\.]+)",
        threeds_data_view,
        name="silver-payu-payment-complete",
    ),
]
