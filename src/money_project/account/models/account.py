from django.contrib.auth.models import User
from django.db import models
from django.utils.formats import date_format

from .base import TagModel, CurrencyModel


class MoneyAccountModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(default="")
    currency = models.ForeignKey(CurrencyModel, on_delete=models.RESTRICT)

    tags = models.ManyToManyField(TagModel, blank=True)

    owner = models.ForeignKey(User, on_delete=models.RESTRICT)
    allowed_users = models.ManyToManyField(
        User, related_name="allowed_users", blank=True
    )

    def __str__(self):
        return f"[{self.id}] {self.name} ({self.currency})"


class ManualAccountStateModel(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    account = models.ForeignKey(MoneyAccountModel, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    def format_amount(self):
        return self.account.currency.format_currency(self.amount)

    def __str__(self):
        return f"{date_format(self.date)}: {self.account} = {self.format_amount()}"
