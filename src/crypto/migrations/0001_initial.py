# Generated by Django 4.1 on 2022-08-28 08:12

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Crypto',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('user', models.IntegerField()),
                ('notes', models.CharField(blank=True, max_length=80, null=True)),
                ('goal', models.IntegerField(blank=True, null=True)),
                ('symbol', models.CharField(max_length=20)),
                ('units', models.DecimalField(blank=True, decimal_places=20, max_digits=30, null=True)),
                ('buy_price', models.DecimalField(decimal_places=10, max_digits=30, verbose_name='Buy Price')),
                ('buy_value', models.DecimalField(decimal_places=10, max_digits=30, verbose_name='Buy Value')),
                ('latest_conversion_rate', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='Latest Conversion Price')),
                ('latest_price', models.DecimalField(decimal_places=10, default=0, max_digits=30, verbose_name='Latest Price')),
                ('latest_value', models.DecimalField(decimal_places=10, default=0, max_digits=30, verbose_name='Latest Value')),
                ('as_on_date', models.DateField(blank=True, null=True, verbose_name='As On Date')),
                ('unrealised_gain', models.DecimalField(decimal_places=10, default=0, max_digits=30, verbose_name='Unrealised Gain')),
                ('realised_gain', models.DecimalField(decimal_places=10, default=0, max_digits=30, verbose_name='Realised Gain')),
                ('xirr', models.DecimalField(blank=True, decimal_places=2, max_digits=20, null=True, verbose_name='XIRR')),
            ],
            options={
                'unique_together': {('symbol', 'user')},
            },
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('trans_date', models.DateField(verbose_name='Transaction Date')),
                ('trans_type', models.CharField(choices=[('Buy', 'Buy'), ('Sell', 'Sell'), ('Receive', 'Receive'), ('Send', 'Send')], max_length=10)),
                ('units', models.DecimalField(decimal_places=20, max_digits=30)),
                ('price', models.DecimalField(decimal_places=10, max_digits=30, verbose_name='Price')),
                ('conversion_rate', models.DecimalField(decimal_places=2, default=1, max_digits=20, verbose_name='Conversion Rate')),
                ('trans_price', models.DecimalField(decimal_places=10, default=0, max_digits=20, verbose_name='Total Price')),
                ('notes', models.CharField(blank=True, max_length=80, null=True)),
                ('broker', models.CharField(blank=True, max_length=20, null=True)),
                ('buy_currency', models.CharField(default='USD', max_length=3)),
                ('fees', models.DecimalField(decimal_places=10, default=0, max_digits=20, verbose_name='Total Price')),
                ('crypto', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='crypto.crypto')),
            ],
            options={
                'unique_together': {('crypto', 'trans_date', 'price', 'units', 'trans_type', 'broker')},
            },
        ),
    ]