# Generated by Django 3.0.6 on 2020-07-02 05:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0214_materialcatalog_original_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='materialcatalog',
            name='original_file',
            field=models.FileField(blank=True, null=True, upload_to='material_catalogs'),
        ),
    ]
