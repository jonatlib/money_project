from datetime import date
from typing import Optional

from django.db import models
from django.utils.formats import date_format
from django.utils.translation import gettext_lazy as _

from base import BaseExpenseModel


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
