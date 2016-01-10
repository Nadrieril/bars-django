# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bars_core', '0020_auto_20151116_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='role',
            name='name',
            field=models.CharField(max_length=127, choices=[(b'customer', b'customer'), (b'policeman', b'policeman'), (b'admin', b'admin'), (b'itemmanager', b'itemmanager'), (b'itemcreator', b'itemcreator'), (b'appromanager', b'appromanager'), (b'barmanager', b'barmanager'), (b'usermanager', b'usermanager'), (b'newsmanager', b'newsmanager'), (b'treasurer', b'treasurer'), (b'stockmanager', b'stockmanager'), (b'inventorymanager', b'inventorymanager'), (b'usercreator', b'usercreator'), (b'accountmanager', b'accountmanager'), (b'agios_daemon', b'agios_daemon'), (b'staff', b'staff')]),
        ),
    ]
