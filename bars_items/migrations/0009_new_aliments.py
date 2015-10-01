# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('bars_core', '0018_barsettings_default_tax'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bars_items', '0008_auto_20150913_2047'),
    ]

    operations = [
        migrations.CreateModel(
            name='New_Aliments',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('more_wished', models.IntegerField(default=0)),
                ('already_added', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('bar', models.ForeignKey(to='bars_core.Bar')),
            ],
        ),
    ]
