# Generated by Django 3.1.2 on 2021-05-25 11:26

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0040_recordhistory_comments'),
    ]

    operations = [
        migrations.CreateModel(
            name='CityLoopsSCAReport',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('sector', models.IntegerField(choices=[(1, 'Construction'), (2, 'Biomass')], db_index=True)),
                ('space_population', models.IntegerField(blank=True, null=True)),
                ('space_size', models.IntegerField(blank=True, null=True)),
                ('space_gdp', models.IntegerField(blank=True, null=True)),
                ('space_employees', models.IntegerField(blank=True, null=True)),
                ('nuts3_population', models.IntegerField(blank=True, null=True)),
                ('nuts3_size', models.IntegerField(blank=True, null=True)),
                ('nuts3_gdp', models.IntegerField(blank=True, null=True)),
                ('nuts3_employees', models.IntegerField(blank=True, null=True)),
                ('nuts2_population', models.IntegerField(blank=True, null=True)),
                ('nuts2_size', models.IntegerField(blank=True, null=True)),
                ('nuts2_gdp', models.IntegerField(blank=True, null=True)),
                ('nuts2_employees', models.IntegerField(blank=True, null=True)),
                ('country_population', models.IntegerField(blank=True, null=True)),
                ('country_size', models.IntegerField(blank=True, null=True)),
                ('country_gdp', models.IntegerField(blank=True, null=True)),
                ('country_employees', models.IntegerField(blank=True, null=True)),
                ('space', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.referencespace')),
            ],
            options={
                'ordering': ['space', 'sector'],
            },
        ),
    ]
