from datetime import datetime

from django.core.management.base import BaseCommand, CommandParser

from ...models import BaseTransactionModel, MoneyAccountModel


class Command(BaseCommand):
    help = "Exports money account data to CSV"

    def add_arguments(self, parser: CommandParser):
        parser.add_argument("accounts", nargs="+", type=int)
        parser.add_argument("--start-date", type=str)
        parser.add_argument("--end-date", type=str)

    def handle(self, *args, **options):
        accounts = options["accounts"]
        start_date = datetime.strptime(options["start_date"], "%Y-%m-%d").date()
        end_date = datetime.strptime(options["end_date"], "%Y-%m-%d").date()

        result = BaseTransactionModel.objects.build_dataframe_all(
            MoneyAccountModel.objects.filter(id__in=accounts),
            start_date,
            end_date,
        )

        self.stdout.write(
            result.to_csv(index=False, header=True, date_format="%Y-%m-%d")
        )
