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

from django_fsm import transition

from silver.models import PaymentMethod


class PayUPaymentMethod(PaymentMethod):
    class Meta:
        proxy = True

    @property
    def token(self):
        return self.decrypt_data(self.data.get('token'))

    @token.setter
    def token(self, value):
        self.data['token'] = self.encrypt_data(value)

    @property
    def archived_customer(self):
        raw_customer = self.data.get('archived_customer', '')
        return json.loads(self.decrypt_data(raw_customer) or '{}')

    @archived_customer.setter
    def archived_customer(self, value):
        raw_customer = json.dumps(value)
        self.data['archived_customer'] = self.encrypt_data(raw_customer)
