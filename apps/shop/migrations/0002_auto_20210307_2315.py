# Generated by Django 2.2.18 on 2021-03-07 20:15

import apps.shop.models
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('shop', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='customer',
            managers=[
                ('objects', apps.shop.models.CustomerManager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='employee',
            managers=[
                ('objects', apps.shop.models.EmployeeManager()),
            ],
        ),
        migrations.AlterModelManagers(
            name='inventory',
            managers=[
                ('objects', apps.shop.models.InventoryManager()),
            ],
        ),
    ]
