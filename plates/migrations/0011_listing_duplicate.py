# Generated by Django 2.0.6 on 2018-07-19 06:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('plates', '0010_listing_not_a_plate'),
    ]

    operations = [
        migrations.AddField(
            model_name='listing',
            name='duplicate',
            field=models.BooleanField(default=False),
        ),
    ]