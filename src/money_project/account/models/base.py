from decimal import Decimal

from django.db import models


class TagModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    used_for_grouping = models.BooleanField(default=False)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

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


class CategoryModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name


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
