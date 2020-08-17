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

import sys
import datetime

import django
from django.conf import settings


settings.configure(
    DEBUG=True,
    DATABASES={
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
        }
    },
    PAYU_MERCHANT='PAYUDEMO',
    PAYU_KEY='1231234567890123',
    PAYMENT_METHOD_SECRET=b'MOW_x1k-ayes3KqnFHNZUxvKipC8iLjxiczEN76TIEA=',
    PAYMENT_PROCESSORS={
        'payu_triggered_v2': {
            'class': 'silver_payu.payment_processors.PayUTriggeredV2',
            'setup_data': {}
        },
        'payu_triggered': {
            'class': 'silver_payu.payment_processors.PayUTriggered',
            'setup_data': {}
        },
        'payu_manual': {
            'class': 'silver_payu.payment_processors.PayUManual',
            'setup_data': {}
        }
    },
    SILVER_AUTOMATICALLY_CREATE_TRANSACTIONS=True,
    SILVER_PAYMENT_TOKEN_EXPIRATION=datetime.timedelta(minutes=5),
    INSTALLED_APPS=('django.contrib.auth',
                    'django.contrib.contenttypes',
                    'django.contrib.sessions',
                    'django.contrib.admin',
                    'silver',
                    'payu',
                    'silver_payu',
                    'dal',
                    'dal_select2',
                    ),
    ROOT_URLCONF='silver_payu.urls',
    CACHES={
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'unique-snowflake',
        }
    }
)

django.setup()
