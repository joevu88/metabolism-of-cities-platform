# Generated by Django 3.0.3 on 2020-04-22 08:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0012_auto_20200422_0630'),
    ]

    operations = [
        migrations.AddField(
            model_name='tag',
            name='is_public',
            field=models.BooleanField(db_index=True, default=True),
        ),
    ]
