import abc
from datetime import date
from typing import Optional

from django.db import models
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from account.models import TagModel, CategoryModel
from account.models.account import MoneyAccountModel
from account.models.base import CurrencyModel


class BaseExpenseModel(models.Model):
    class Meta:
        abstract = True

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=250)
    description = models.TextField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    tag = models.ManyToManyField(TagModel, blank=True)
    category = models.ForeignKey(
        CategoryModel, on_delete=models.SET_NULL, null=True, blank=True, default=None
    )

    account = models.ForeignKey(MoneyAccountModel, on_delete=models.CASCADE)
    counterparty_account = models.ForeignKey(
        MoneyAccountModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name="move_expenses_%(class)ss",
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


class ExtraExpenseModel(BaseExpenseModel):
    date = models.DateField(auto_now_add=True)

    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    def __str__(self):
        pass


class RegularExpenseModel(BaseExpenseModel):
    class Period(models.TextChoices):
        Yearly = "Yearly", _("Yearly")
        Quarterly = "Quarterly", _("Quarterly")
        HalfYearly = "Half-Yearly", _("Half-Yearly")
        Monthly = "Monthly", _("Monthly")
        Daily = "Daily", _("Daily")

    period = models.CharField(max_length=15, choices=Period.choices)
    billing_start = models.DateField(null=True, blank=True)
    billing_end = models.DateField(null=True, blank=True)

    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    def __str__(self):
        return "[{}] {} - {}: {} {}".format(
            self.period,
            date_format(self.billing_start),
            date_format(self.billing_end),
            self.name,
            self.format_amount(),
        )
