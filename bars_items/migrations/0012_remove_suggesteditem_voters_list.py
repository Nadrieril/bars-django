# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bars_items', '0011_auto_20150919_0649'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='suggesteditem',
            name='voters_list',
        ),
    ]
