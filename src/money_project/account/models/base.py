from decimal import Decimal

from django.db import models


class TagModel(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50)
    used_for_grouping = models.BooleanField(default=False)
    parent = models.ForeignKey("self", on_delete=models.CASCADE, null=True, blank=True)

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
