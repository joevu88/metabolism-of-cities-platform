# Generated by Django 3.0.3 on 2020-06-12 20:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0166_unit_multiplication_factor'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='forumtopic',
            options={'ordering': ['-last_update']},
        ),
    ]
