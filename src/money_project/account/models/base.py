from decimal import Decimal
from typing import Optional

from django.db import models
from mptt.models import MPTTModel, TreeForeignKey
from simple_history import register
from simple_history.models import HistoricalRecords


class LedgerName(models.Model):
    id = models.AutoField(primary_key=True)
    common_name = models.CharField(max_length=255, null=True, blank=True)
    negative_ledger_name = models.CharField(max_length=150)
    positive_ledger_name = models.CharField(max_length=150, null=True, blank=True)

    history = HistoricalRecords()

    def __str__(self):
        if self.common_name:
            return self.common_name

        return self.negative_ledger_name

    def get_name(self, amount: Decimal) -> str:
        if amount <= 0:
            return self.negative_ledger_name
        else:
            if self.positive_ledger_name:
                return self.positive_ledger_name
            else:
                return self.negative_ledger_name


class TagModel(MPTTModel):
    class MPTTMeta:
        order_insertion_by = ["name"]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    used_for_grouping = models.BooleanField(default=False)
    color = models.CharField(max_length=10, default="#AAAAAA")
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    ledger_name = models.ForeignKey(
        LedgerName, on_delete=models.SET_NULL, null=True, blank=True
    )

    # FIXME beware of cycles -  self-parent, handle in save

    def get_all_names(self) -> list[str]:
        names = [self.name]
        current_parent = self.parent
        while current_parent:
            names.append(current_parent.name)
            current_parent = current_parent.parent
        return names

    def get_all_ids(self) -> list[int]:
        ids = [self.id]
        current_parent = self.parent
        while current_parent:
            ids.append(current_parent.id)
            current_parent = current_parent.parent
        return ids

    def __str__(self):
        return self.name

    def get_ledger(self, amount: Decimal) -> Optional[str]:
        if self.ledger_name:
            return self.ledger_name.get_name(amount)

        p = self.parent
        while p is not None:
            if name := p.get_ledger(amount):
                return name

            p = p.parent

        return None


register(TagModel)


class CategoryModel(MPTTModel):
    class MPTTMeta:
        order_insertion_by = ["name"]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    color = models.CharField(max_length=10, default="#AAAAAA")
    parent = TreeForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )

    ledger_name = models.ForeignKey(
        LedgerName, on_delete=models.SET_NULL, null=True, blank=True
    )

    def __str__(self):
        return self.name

    def get_ledger(self, amount: Decimal) -> Optional[str]:
        if self.ledger_name:
            return self.ledger_name.get_name(amount)

        p = self.parent
        while p is not None:
            if name := p.get_ledger(amount):
                return name

            p = p.parent

        return None


register(CategoryModel)


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

        result += "{:,.1f}".format(number).replace(",", " ").replace(".0", "")

        if self.suffix:
            result = result + " " + self.suffix

        return result
