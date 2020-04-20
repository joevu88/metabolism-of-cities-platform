# Generated by Django 3.0.3 on 2020-04-20 12:23

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20200409_1237'),
    ]

    operations = [
        migrations.CreateModel(
            name='Organization',
            fields=[
                ('record_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='core.Record')),
                ('url', models.CharField(blank=True, max_length=255, null=True)),
                ('logo', models.ImageField(blank=True, null=True, upload_to='organizations')),
                ('type', models.CharField(choices=[('academic', 'Research Institution'), ('universities', 'Universities'), ('city_government', 'City Government'), ('regional_government', 'Regional Government'), ('national_government', 'National Government'), ('statistical_agency', 'Statistical Agency'), ('private_sector', 'Private Sector'), ('publisher', 'Publishers'), ('ngo', 'NGO'), ('other', 'Other')], max_length=20)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='core.Organization')),
            ],
            bases=('core.record',),
        ),
    ]
