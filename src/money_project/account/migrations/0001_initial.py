# Generated by Django 5.0.6 on 2024-05-14 11:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CategoryModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
            ],
        ),
        migrations.CreateModel(
            name='CurrencyModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('prefix', models.CharField(blank=True, max_length=5, null=True)),
                ('suffix', models.CharField(blank=True, max_length=5, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='MoneyAccountModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('allowed_users', models.ManyToManyField(blank=True, related_name='allowed_users', to=settings.AUTH_USER_MODEL)),
                ('currency', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to='account.currencymodel')),
                ('owner', models.ForeignKey(on_delete=django.db.models.deletion.RESTRICT, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='ManualAccountStateModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('date', models.DateField(auto_now_add=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.moneyaccountmodel')),
            ],
        ),
        migrations.CreateModel(
            name='TagModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=50)),
                ('used_for_grouping', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='account.tagmodel')),
            ],
        ),
        migrations.CreateModel(
            name='RegularTransactionModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=250)),
                ('description', models.TextField(blank=True, null=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('period', models.CharField(choices=[('Yearly', 'Yearly'), ('Quarterly', 'Quarterly'), ('Half-Yearly', 'Half-Yearly'), ('Monthly', 'Monthly'), ('Daily', 'Daily'), ('Work-Day', 'Work-Day')], max_length=15)),
                ('billing_start', models.DateField(blank=True, null=True)),
                ('billing_end', models.DateField(blank=True, null=True)),
                ('category', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.categorymodel')),
                ('counterparty_account', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='move_transaction_%(class)ss', to='account.moneyaccountmodel')),
                ('target_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.moneyaccountmodel')),
                ('tag', models.ManyToManyField(blank=True, to='account.tagmodel')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='moneyaccountmodel',
            name='tags',
            field=models.ManyToManyField(blank=True, to='account.tagmodel'),
        ),
        migrations.CreateModel(
            name='ExtraTransactionModel',
            fields=[
                ('id', models.AutoField(primary_key=True, serialize=False)),
                ('name', models.CharField(max_length=250)),
                ('description', models.TextField(blank=True, null=True)),
                ('amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('date', models.DateField()),
                ('category', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='account.categorymodel')),
                ('counterparty_account', models.ForeignKey(blank=True, default=None, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='move_transaction_%(class)ss', to='account.moneyaccountmodel')),
                ('target_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='account.moneyaccountmodel')),
                ('tag', models.ManyToManyField(blank=True, to='account.tagmodel')),
            ],
            options={
                'abstract': False,
            },
        ),
    ]
