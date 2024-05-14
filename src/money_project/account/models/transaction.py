import abc
from datetime import date
from typing import Optional

from django.db import models
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from pandas.tseries.offsets import DateOffset, BDay, BaseOffset

from account.models import TagModel, CategoryModel
from account.models.account import MoneyAccountModel
from account.models.base import CurrencyModel


class BaseTransactionModel(models.Model):
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

    target_account = models.ForeignKey(MoneyAccountModel, on_delete=models.CASCADE)
    counterparty_account = models.ForeignKey(
        MoneyAccountModel,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
        related_name="move_transaction_%(class)ss",
    )

    @property
    def currency(self) -> CurrencyModel:
        return self.target_account.currency

    def format_amount(self) -> str:
        return self.currency.format_currency(self.amount)

    @abc.abstractmethod
    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    @abc.abstractmethod
    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    @abc.abstractmethod
    def is_billing_date(self, day: date) -> bool:
        pass

    @abc.abstractmethod
    def __str__(self):
        pass


class ExtraTransactionModel(BaseTransactionModel):
    date = models.DateField()

    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        relative_to = relative_to or date.today()
        if relative_to <= self.date:
            return self.date
        return None

    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        relative_to = relative_to or date.today()
        if relative_to > self.date:
            return self.date
        return None

    def is_billing_date(self, day: date) -> bool:
        return day == self.date

    def __str__(self):
        return "{}: {} {}".format(
            date_format(self.date),
            self.name,
            self.format_amount(),
        )


class RegularTransactionModel(BaseTransactionModel):
    class Period(models.TextChoices):
        Yearly = "Yearly", _("Yearly")
        Quarterly = "Quarterly", _("Quarterly")
        HalfYearly = "Half-Yearly", _("Half-Yearly")
        Monthly = "Monthly", _("Monthly")
        Daily = "Daily", _("Daily")
        WorkDay = "Work-Day", _("Work-Day")

    period = models.CharField(max_length=15, choices=Period.choices)
    billing_start = models.DateField()
    billing_end = models.DateField(null=True, blank=True)

    def _period_to_timedelta(self) -> BaseOffset:
        match self.period:
            case "Yearly":
                return DateOffset(years=1)
            case "Quarterly":
                return DateOffset(months=3)
            case "Half-Yearly":
                return DateOffset(months=6)
            case "Monthly":
                return DateOffset(months=1)
            case "Daily":
                return DateOffset(days=1)
            case "Work-Day":
                return BDay(1)

    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        relative_to = relative_to or date.today()
        pass

    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        relative_to = relative_to or date.today()
        pass

    def is_billing_date(self, day: date) -> bool:
        pass

    def __str__(self):
        start = (
            date_format(self.billing_start)
            if self.billing_start is not None
            else "No start date"
        )
        end = (
            date_format(self.billing_end)
            if self.billing_end is not None
            else "No end date"
        )

        return "[{}] {} - {}: {} {}".format(
            self.period,
            start,
            end,
            self.name,
            self.format_amount(),
        )
