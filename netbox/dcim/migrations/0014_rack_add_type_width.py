# -*- coding: utf-8 -*-
# Generated by Django 1.9.8 on 2016-08-08 21:11
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('dcim', '0013_add_interface_form_factors'),
    ]

    operations = [
        migrations.AddField(
            model_name='rack',
            name='type',
            field=models.PositiveSmallIntegerField(blank=True, choices=[(100, b'2-post frame'), (200, b'4-post frame'), (300, b'4-post cabinet'), (1000, b'Wall-mounted frame'), (1100, b'Wall-mounted cabinet')], null=True, verbose_name=b'Type'),
        ),
        migrations.AddField(
            model_name='rack',
            name='width',
            field=models.PositiveSmallIntegerField(choices=[(19, b'19 inches'), (23, b'23 inches')], default=19, help_text=b'Rail-to-rail width', verbose_name=b'Width'),
        ),
    ]