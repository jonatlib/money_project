import argparse
from datetime import datetime

from django.core.management.base import BaseCommand, CommandParser

from ...accounting.account import get_ideal_account_balance, get_real_account_balance
from ...models import MoneyAccountModel


class Command(BaseCommand):
    help = "Exports money account data to CSV"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("accounts", nargs="+", type=int)
        parser.add_argument("--ideal", action=argparse.BooleanOptionalAction)
        parser.add_argument("--start-date", type=str)
        parser.add_argument("--end-date", type=str)

    def handle(self, *args, **options):
        accounts = options["accounts"]
        ideal = options["ideal"]
        start_date = datetime.strptime(options["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(options["end_date"], "%Y-%m-%d").date()

        if ideal:
            result = get_ideal_account_balance(
                MoneyAccountModel.objects.filter(id__in=accounts), start_date, end_date
            )
        else:
            result = get_real_account_balance(
                MoneyAccountModel.objects.filter(id__in=accounts), start_date, end_date
            )

        self.stdout.write(
            result.to_csv(index=True, header=True, date_format="%Y-%m-%d")
        )
