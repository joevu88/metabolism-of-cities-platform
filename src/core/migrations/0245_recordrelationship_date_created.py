# Generated by Django 3.0.6 on 2020-08-07 15:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0244_coursecontent_type'),
    ]

    operations = [
        migrations.AddField(
            model_name='recordrelationship',
            name='date_created',
            field=models.DateTimeField(auto_now_add=True, null=True),
        ),
    ]
