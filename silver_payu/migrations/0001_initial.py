# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('silver', '0032_auto_20170201_1342'),
    ]

    operations = [
        migrations.CreateModel(
            name='PayUPaymentMethod',
            fields=[
            ],
            options={
                'proxy': True,
            },
            bases=('silver.paymentmethod',),
        ),
    ]
