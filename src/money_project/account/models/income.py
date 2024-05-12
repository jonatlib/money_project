from django.db import models


class BaseIncomeModel(models.Model):
    class Meta:
        abstract = True

    pass
