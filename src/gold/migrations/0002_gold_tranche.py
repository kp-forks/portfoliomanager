# Generated by Django 4.1.10 on 2023-09-18 04:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0004_sovereigngoldbond_sgbdividend'),
        ('gold', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='gold',
            name='tranche',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='common.sovereigngoldbond'),
        ),
    ]