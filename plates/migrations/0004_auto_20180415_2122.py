# Generated by Django 2.0.4 on 2018-04-15 21:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plates', '0003_auto_20180415_2120'),
    ]

    operations = [
        migrations.AlterField(
            model_name='listing',
            name='original_id',
            field=models.CharField(default=0, max_length=255, unique=True),
        ),
    ]
