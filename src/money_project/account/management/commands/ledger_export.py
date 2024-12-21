import itertools

from django.core.management.base import BaseCommand

from account.models import ExtraTransactionModel, RegularTransactionModel
from . import ledger


class Command(BaseCommand):
    help = "Exports all data to ledger"

    def handle(self, *args, **options):
        extra_transactions = ExtraTransactionModel.objects.all().order_by("date")
        regular_transactions = RegularTransactionModel.objects.all().order_by(
            "billing_start"
        )

        # TODO split ledgers to files...
        ledgers = itertools.chain(
            ledger.extra_transaction_ledgers(extra_transactions),
            # ledger.regular_transaction_ledgers(regular_transactions),
        )

        for element in ledgers:
            self.stdout.write(str(element))
            self.stdout.write("\n")
            self.stdout.write("\n")
