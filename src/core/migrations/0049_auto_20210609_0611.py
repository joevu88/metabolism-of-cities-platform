# Generated by Django 3.1.2 on 2021-06-09 06:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0048_merge_20210609_0534'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='blog',
            options={'ordering': ['-date', 'name']},
        ),
        migrations.DeleteModel(
            name='DataPortal',
        ),
    ]
