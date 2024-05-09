import abc
from datetime import date
from decimal import Decimal
from typing import Optional

from django.db import models

from account import MoneyAccountModel


class TagModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    used_for_grouping = models.BooleanField(default=False)


class CategoryModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)


class CurrencyModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    prefix = models.CharField(max_length=5, null=True, blank=True)
    suffix = models.CharField(max_length=5, null=True, blank=True)

    def __str__(self):
        return self.name

    def format_currency(self, number: Decimal) -> str:
        result = ""
        if self.prefix:
            result = self.prefix + result

        result += str(number)

        if self.suffix:
            result = result + self.suffix

        return result


class BaseExpenseModel(models.Model):
    class Meta:
        abstract = True

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    tag = models.ManyToManyField(TagModel)
    category = models.ForeignKey(
        CategoryModel, on_delete=models.SET_NULL, null=True, blank=True, default=None
    )

    account = models.ForeignKey(MoneyAccountModel, on_delete=models.CASCADE)
    counterparty_account = models.ForeignKey(
        MoneyAccountModel, on_delete=models.CASCADE, null=True, blank=True, default=None
    )

    @property
    def currency(self) -> CurrencyModel:
        return self.account.currency

    def format_amount(self) -> str:
        return self.currency.format_currency(self.amount)

    @abc.abstractmethod
    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    @abc.abstractmethod
    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    @abc.abstractmethod
    def __str__(self):
        pass
