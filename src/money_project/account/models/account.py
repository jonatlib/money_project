from django.contrib.auth.models import User
from django.db import models

from base import TagModel, CurrencyModel


class MoneyAccountModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    currency = models.ForeignKey(CurrencyModel, on_delete=models.RESTRICT)

    tags = models.ManyToManyField(TagModel)

    owner = models.ForeignKey(User, on_delete=models.RESTRICT)
    allowed_users = models.ManyToManyField(User, related_name="allowed_users")


class ManualAccountStateModel(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField(auto_now_add=True)
    account = models.ForeignKey(MoneyAccountModel, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
