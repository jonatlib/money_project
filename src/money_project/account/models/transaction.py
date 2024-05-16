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
        accounts: list[MoneyAccountModel], start_date: date, end_date: date
    ) -> pd.DataFrame:
        df_regular = RegularTransactionModel.objects.build_dataframe(
            accounts, start_date, end_date
        )
        df_extra = ExtraTransactionModel.objects.build_dataframe(
            accounts, start_date, end_date
        )

        return pd.concat([df_regular, df_extra], ignore_index=True)

    def all_for_accounts(self, accounts: list[MoneyAccountModel]) -> models.QuerySet:
        """
        Build query set returning all transactions for an account.
        Including reverse operation on a given account.
        """
        return self.all().filter(
            Q(target_account__in=accounts) | Q(counterparty_account__in=accounts)
        )

    def get_model_name(self) -> str:
        return self.model.__name__.lower()

    def get_id(self, id: int) -> str:
        return f"{self.get_model_name()}-{id}"

    def all_for_account_in_range(
        self, accounts: list[MoneyAccountModel], start_date: date, end_date: date
    ) -> models.QuerySet:
        raise NotImplementedError

    def build_dataframe(
        self, accounts: list[MoneyAccountModel], start_date: date, end_date: date
    ) -> pd.DataFrame:
        transactions = self.all_for_account_in_range(accounts, start_date, end_date)

        result = []

        transaction: BaseTransactionModel
        for transaction in transactions:
            for d in transaction.create_date_generator():
                if d > end_date:
                    break

                if d >= start_date:
                    transaction_tags = transaction.tag.all()
                    tags = [
                        name for tag in transaction_tags for name in tag.get_all_names()
                    ]

                    tag_ids = [
                        ids for tag in transaction_tags for ids in tag.get_all_ids()
                    ]

                    counter_party_account = transaction.counterparty_account
                    category = transaction.category

                    data = {
                        "id": self.get_id(transaction.id),
                        "raw_id": transaction.id,
                        # Transaction details
                        "date": d,
                        "name": transaction.name,
                        "amount": transaction.amount,
                        # Grouping info
                        "tags": tags,
                        "category": category.name if category else None,
                        # Account info
                        "account": transaction.target_account.name,
                        "counter_party_account": (
                            counter_party_account.name
                            if counter_party_account
                            else None
                        ),
                        # Debug info
                        "tag_ids": tag_ids,
                        "category_id": category.id if category else None,
                        "account_id": transaction.target_account.id,
                        "counter_party_account_id": (
                            counter_party_account.id if counter_party_account else None
                        ),
                        "model": transaction.__class__.__name__.lower(),
                    }
                    result.append(data)

                    if counter_party_account and counter_party_account in accounts:
                        counter_data = {
                            **data,
                            "amount": -data["amount"],
                            "account": data["counter_party_account"],
                            "counter_party_account": data["account"],
                            "account_id": data["counter_party_account_id"],
                            "counter_party_account_id": data["account_id"],
                        }
                        result.append(counter_data)

        return pd.DataFrame(result)


class ExtraTransactionManager(BaseTransactionManager):

    def all_for_account_in_range(
        self, accounts: list[MoneyAccountModel], start_date: date, end_date: date
    ) -> models.QuerySet:
        return self.all_for_accounts(accounts).filter(
            Q(date__gte=start_date) & Q(date__lte=end_date)
        )


class RegularTransactionManager(BaseTransactionManager):

    def all_for_account_in_range(
        self, accounts: list[MoneyAccountModel], start_date: date, end_date: date
    ) -> models.QuerySet:
        return self.all_for_accounts(accounts).filter(
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
        while self.billing_end is None or new_date <= self.billing_end:
            yield new_date.date()
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
