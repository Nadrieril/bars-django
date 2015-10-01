# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('bars_core', '0018_barsettings_default_tax'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('bars_items', '0009_new_aliments'),
    ]

    operations = [
        migrations.CreateModel(
            name='SuggestedItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100)),
                ('timestamp', models.DateTimeField(auto_now_add=True)),
                ('wished', models.IntegerField(default=0)),
                ('already_added', models.BooleanField(default=False)),
                ('author', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
                ('bar', models.ForeignKey(to='bars_core.Bar')),
            ],
        ),
        migrations.RemoveField(
            model_name='new_aliments',
            name='author',
        ),
        migrations.RemoveField(
            model_name='new_aliments',
            name='bar',
        ),
        migrations.DeleteModel(
            name='New_Aliments',
        ),
    ]
