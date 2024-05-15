import abc
from datetime import date
from typing import Optional, Iterator

import pandas as pd
from django.db import models
from django.db.models import Q
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _
from pandas.tseries.offsets import DateOffset, BDay, BaseOffset

from account.models import TagModel, CategoryModel
from account.models.account import MoneyAccountModel
from account.models.base import CurrencyModel


class BaseTransactionManager(models.Manager):

    @staticmethod
    def build_dataframe_all(
        account: MoneyAccountModel, start_date: date, end_date: date
    ) -> pd.DataFrame:
        df_regular = RegularTransactionModel.objects.build_dataframe(
            account, start_date, end_date
        )
        df_extra = ExtraTransactionModel.objects.build_dataframe(
            account, start_date, end_date
        )

        return pd.concat([df_regular, df_extra], ignore_index=True)

    def all_for_account(self, account: MoneyAccountModel) -> models.QuerySet:
        """
        Build query set returning all transactions for an account.
        Including reverse operation on a given account.
        """
        return self.all().filter(
            Q(target_account=account) | Q(counterparty_account=account)
        )

    def all_for_account_in_range(
        self, account: MoneyAccountModel, start_date: date, end_date: date
    ) -> models.QuerySet:
        raise NotImplementedError

    def build_dataframe(
        self, account: MoneyAccountModel, start_date: date, end_date: date
    ) -> pd.DataFrame:
        transactions = self.all_for_account_in_range(account, start_date, end_date)

        result = []

        transaction: BaseTransactionModel
        for transaction in transactions:
            signum = 1 if transaction.target_account == account else -1

            for d in transaction.create_date_generator():
                if d >= start_date:
                    tags = [
                        name
                        for tag in transaction.tag.all()
                        for name in tag.get_all_names()
                    ]

                    result.append(
                        {
                            "date": d,
                            "id": transaction.id,
                            "name": transaction.name,
                            "signum": signum,
                            "amount": signum * transaction.amount,
                            "tags": tags,
                            "category": transaction.category.name,
                            "account": account.name,
                            "counter_party_account": transaction.counterparty_account.name,
                        }
                    )
                if d > end_date:
                    break

        return pd.DataFrame(result)


class ExtraTransactionManager(BaseTransactionManager):

    def all_for_account_in_range(
        self, account: MoneyAccountModel, start_date: date, end_date: date
    ) -> models.QuerySet:
        return self.all_for_account(account).filter(
            Q(date__gte=start_date) & Q(date__lte=end_date)
        )


class RegularTransactionManager(BaseTransactionManager):

    def all_for_account_in_range(
        self, account: MoneyAccountModel, start_date: date, end_date: date
    ) -> models.QuerySet:
        return self.all_for_account(account).filter(
            (Q(billing_start__gte=start_date) & Q(billing_start__lte=end_date))
            | (Q(billing_end__gte=start_date) & Q(billing_end__lte=end_date))
        )


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

    objects = BaseTransactionManager

    @property
    def currency(self) -> CurrencyModel:
        return self.target_account.currency

    def format_amount(self) -> str:
        return self.currency.format_currency(self.amount)

    @abc.abstractmethod
    def create_date_generator(self) -> Iterator[date]:
        pass

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

    objects = ExtraTransactionManager()

    def create_date_generator(self) -> Iterator[date]:
        yield self.date

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

    objects = RegularTransactionManager()

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

    def create_date_generator(self) -> Iterator[date]:
        yield self.billing_start

        new_date = self.billing_start + self._period_to_timedelta()
        while new_date <= self.billing_end:
            yield new_date
            new_date += self._period_to_timedelta()

    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        relative_to = relative_to or date.today()

        # TODO this is really inefficient implementation but hey it works
        date_generator = self.create_date_generator()
        for d in date_generator:
            if d >= relative_to:
                return d

        return None

    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        relative_to = relative_to or date.today()

        # TODO this is really inefficient implementation but hey it works
        date_generator = self.create_date_generator()
        try:
            previous_date = next(date_generator)
        except StopIteration:
            return None

        if previous_date < relative_to:
            return previous_date

        for d in date_generator:
            if d >= relative_to:
                return previous_date
            previous_date = d

        return None

    def is_billing_date(self, day: date) -> bool:
        return self.next_billing(day) == day

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
