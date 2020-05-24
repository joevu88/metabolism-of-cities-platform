# Generated by Django 3.0.3 on 2020-05-24 09:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0141_project_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='event',
            name='site',
        ),
        migrations.AddField(
            model_name='event',
            name='projects',
            field=models.ManyToManyField(to='core.Project'),
        ),
    ]
