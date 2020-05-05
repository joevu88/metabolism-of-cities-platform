# Generated by Django 3.0.3 on 2020-05-05 05:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0077_auto_20200504_1359'),
    ]

    operations = [
        migrations.AlterField(
            model_name='webpagedesign',
            name='header',
            field=models.CharField(choices=[('inherit', 'No custom header - use the project header'), ('full', 'Full header with title and subtitle'), ('small', 'Small header; menu only'), ('image', 'Image underneath menu')], default='full', max_length=7),
        ),
    ]
