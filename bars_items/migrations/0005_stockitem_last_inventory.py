# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc


def set_last_inventory(apps, schema_editor):
    StockItem = apps.get_model('bars_items', 'StockItem')
    ItemOperation = apps.get_model("bars_transactions", "ItemOperation")

    for si in StockItem.objects.all():
        operations = ItemOperation.objects.all(
        ).filter(transaction__type__contains="inventory"
        ).filter(target=si
        ).order_by('-transaction__timestamp')
        if not operations:
            si.last_inventory = datetime.datetime(2015, 2, 24, 21, 17, 0, 0, tzinfo=utc)
        else:
            si.last_inventory = operations[0].transaction.timestamp
        si.save()


class Migration(migrations.Migration):

    dependencies = [
        ('bars_items', '0004_auto_20150329_1819'),
        ('bars_transactions', '0002_manual'),
    ]

    operations = [
        migrations.AddField(
            model_name='stockitem',
            name='last_inventory',
            field=models.DateTimeField(default=datetime.datetime(2015, 2, 24, 21, 17, 0, 0, tzinfo=utc)),
            preserve_default=True,
        ),
        migrations.RunPython(set_last_inventory)
    ]
