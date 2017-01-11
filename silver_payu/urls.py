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


from django.conf.urls import include, url

from silver.views import pay_transaction_view

from .views import successful_transaction, failed_transaction


urlpatterns = [
    url(r'payu/(?P<transaction_uuid>[0-9a-z-]+)/success$',
        successful_transaction, name='successful-transaction'),
    url(r'payu/(?P<transaction_uuid>[0-9a-z-]+)/fail$',
        failed_transaction, name='failed-transaction'),
]

urlpatterns += patterns('',
    (r'^payu/', include('payu.urls')),
)
