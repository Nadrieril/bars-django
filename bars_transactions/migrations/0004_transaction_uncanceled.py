# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bars_transactions', '0003_transaction_moneyflow'),
    ]

    operations = [
        migrations.AddField(
            model_name='transaction',
            name='uncanceled',
            field=models.BooleanField(default=False),
        ),
    ]
