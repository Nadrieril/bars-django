# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bars_items', '0010_auto_20150917_1800'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='suggesteditem',
            name='author',
        ),
        migrations.AddField(
            model_name='suggesteditem',
            name='voters_list',
            field=models.ManyToManyField(to=settings.AUTH_USER_MODEL),
        ),
    ]
