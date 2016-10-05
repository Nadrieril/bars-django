# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bars_items', '0009_suggesteditem'),
    ]

    operations = [
        migrations.AddField(
            model_name='sellitem',
            name='sell_fraction',
            field=models.BooleanField(default=True),
        ),
    ]
