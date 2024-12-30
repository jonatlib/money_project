from typing import Optional

from django.contrib.auth.models import User
from django.db import models
from django.utils.formats import date_format
from simple_history.models import HistoricalRecords

from .base import CurrencyModel, LedgerName, TagModel


class MoneyAccountModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    description = models.TextField(default="", null=True, blank=True)
    currency = models.ForeignKey(CurrencyModel, on_delete=models.RESTRICT)

    tags = models.ManyToManyField(TagModel, blank=True)
    show_in_overview = models.BooleanField(default=True)
    include_in_statistics = models.BooleanField(default=True)

    owner = models.ForeignKey(User, on_delete=models.RESTRICT)
    allowed_users = models.ManyToManyField(
        User, related_name="allowed_users", blank=True
    )

    ledger_name = models.ForeignKey(LedgerName, on_delete=models.SET_NULL, null=True)

    history = HistoricalRecords()

    def __str__(self):
        return f"[{self.id}] {self.name} ({self.currency})"

    def get_ledger(self) -> Optional[str]:
        return self.ledger_name.get_name(0) if self.ledger_name else None


class ManualAccountStateModel(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.DateField()
    account = models.ForeignKey(MoneyAccountModel, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    history = HistoricalRecords()

    def format_amount(self):
        return self.account.currency.format_currency(self.amount)

    def __str__(self):
        return f"{date_format(self.date)}: {self.account} = {self.format_amount()}"
