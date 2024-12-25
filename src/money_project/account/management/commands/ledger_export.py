import datetime
import itertools

from django.core.management.base import BaseCommand
from django.db.models import Q

from account.models import (
    ExtraTransactionModel,
    ManualAccountStateModel,
    RegularTransactionModel,
)
from . import ledger


class Command(BaseCommand):
    help = "Exports all data to ledger"

    def handle(self, *args, **options):
        start_date = datetime.date(2024, 1, 1)
        end_date = datetime.date(2024, 12, 31)

        extra_transactions = ExtraTransactionModel.objects.filter(
            Q(date__gte=start_date) & Q(date__lte=end_date)
        ).order_by("date")
        regular_transactions = RegularTransactionModel.objects.filter(
            (Q(billing_start__gte=start_date) & Q(billing_start__lte=end_date))
        ).order_by("billing_start")
        account_manual_states = ManualAccountStateModel.objects.filter(
            Q(date__gte=start_date) & Q(date__lte=end_date)
        ).order_by("date")

        months = [
            datetime.date(
                start_date.year + (start_date.month + i - 1) // 12,
                (start_date.month + i - 1) % 12 + 1,
                1,
            )
            for i in range(
                (end_date.year - start_date.year) * 12
                + end_date.month
                - start_date.month
                + 1
            )
        ]

        # TODO split ledgers to files...
        regular = list(ledger.regular_transaction_ledgers(regular_transactions))
        regular_to_transactions = [
            t
            for r in regular
            for month in months
            for t in r.generate_transactions(month)
        ]

        ledgers = itertools.chain(
            # regular,
            ledger.manual_account_state_ledgers(account_manual_states),
            regular_to_transactions,
            ledger.extra_transaction_ledgers(extra_transactions),
        )

        sorted_ledgers = list(ledgers)
        sorted_ledgers.sort(key=lambda x: x.date)

        for element in sorted_ledgers:
            self.stdout.write(str(element))
            self.stdout.write("\n")
            self.stdout.write("\n")
