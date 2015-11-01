# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bars_items', '0014_remove_suggesteditem_wished'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='suggesteditem',
            name='bar',
        ),
        migrations.RemoveField(
            model_name='suggesteditem',
            name='voters_list',
        ),
        migrations.DeleteModel(
            name='SuggestedItem',
        ),
    ]
