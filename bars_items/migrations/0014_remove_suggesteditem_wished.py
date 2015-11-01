# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bars_items', '0013_suggesteditem_voters_list'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='suggesteditem',
            name='wished',
        ),
    ]
