# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-07-30 15:49
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('server', '0052_auto_20170726_0113'),
    ]

    operations = [
        migrations.AddField(
            model_name='wfmodule',
            name='is_collapsed',
            field=models.BooleanField(default=True),
        ),
    ]