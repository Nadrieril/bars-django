# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bars_core', '0015_auto_20150329_1856'),
    ]

    operations = [
        migrations.AlterField(
            model_name='loginattempt',
            name='sent_username',
            field=models.CharField(max_length=512),
            preserve_default=True,
        ),
    ]
