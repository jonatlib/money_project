from typing import Optional

from django.db import models

from base import BaseExpenseModel


class ExtraExpenseModel(BaseExpenseModel):
    date = models.DateField(auto_now_add=True)

    def next_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    def previous_billing(self, relative_to: Optional[date] = None) -> Optional[date]:
        pass

    def __str__(self):
        pass
