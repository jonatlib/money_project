import abc
import calendar
import dataclasses
import datetime
import textwrap
from collections.abc import Iterable
from copy import deepcopy
from decimal import Decimal
from typing import Optional


def format_tag(tag: str | tuple[str, str]) -> str:
    if isinstance(tag, tuple):
        return f"  ; {tag[0]}: {tag[1]}"
    else:
        return f"  ; :{tag}:"


@dataclasses.dataclass
class Amount(abc.ABC):
    @abc.abstractmethod
    def __str__(self) -> str:
        pass


@dataclasses.dataclass
class AmountTransfer(Amount):
    amount: Decimal
    currency: str

    def __str__(self) -> str:
        return f"{self.amount} {self.currency}"


@dataclasses.dataclass
class AmountSpecific(Amount):
    amount: Decimal
    currency: str

    def __str__(self) -> str:
        return f"={self.amount} {self.currency}"


@dataclasses.dataclass
class Posting:
    account: str
    amount: Optional[Amount]
    tags: list[str | tuple[str, str]]

    def __str__(self) -> str:
        tags = "\n".join([format_tag(t) for t in self.tags])

        return textwrap.dedent(
            f"""
            {tags}
            {self.account}   {self.amount or ""}
            """.strip()
        ).strip()


@dataclasses.dataclass
class BaseLedger(abc.ABC):
    id: str
    name: str
    description: Optional[str]
    tags: list[str | tuple[str, str]]
    postings: list[Posting]

    @abc.abstractmethod
    def __str__(self) -> str:
        pass


@dataclasses.dataclass
class TransactionLedger(BaseLedger):
    date: datetime.date

    def copy(self) -> "TransactionLedger":
        return TransactionLedger(
            id=deepcopy(self.id),
            name=deepcopy(self.name),
            description=deepcopy(self.description),
            tags=deepcopy(self.tags),
            postings=deepcopy(self.postings),
            date=deepcopy(self.date),
        )

    def get_heading(self) -> str:
        date_str = self.date.strftime("%Y-%m-%d")
        return f'{date_str} * ({self.id}) "{self.name}"'

    def __str__(self) -> str:
        tags = "\n".join([format_tag(t) for t in self.tags])

        result = []
        result.append(self.get_heading())

        if tags:
            result.append(tags)

        for posting in self.postings:
            result.append(textwrap.indent(str(posting), "  "))

        return "\n".join(result)


@dataclasses.dataclass
class RegularTransactionLedger(TransactionLedger):
    period: str
    billing_end: Optional[datetime.date]

    def get_heading(self) -> str:
        # ~ Monthly Rent Payment (2024-01 to 2024-12)
        if self.billing_end is not None:
            return f"~ {self.period} {self.date} to {self.billing_end}"
        else:
            return f"~ {self.period} {self.date}"

    def generate_transactions(
        self, month: datetime.date
    ) -> Iterable[TransactionLedger]:
        if self.period == "monthly":
            entity = self.copy()
            date = entity.date.replace(month=month.month, year=month.year)
            if self.billing_end is not None and date > self.billing_end:
                return
            entity.date = date
            yield entity
        elif self.period == "daily":
            number_of_days = calendar.monthrange(month.year, month.month)[1]
            for day in range(1, number_of_days):
                date = datetime.date(month.year, month.month, day)
                if self.billing_end is not None and date > self.billing_end:
                    return
                entity = self.copy()
                entity.date = date
                yield entity
        elif self.period == "weekly":
            start = self.date.replace(month=month.month, year=month.year)
            for shift in range(0, 4):
                date = start + datetime.timedelta(days=shift * 7)
                if self.billing_end is not None and date > self.billing_end:
                    return
                if date.month == month.month:
                    entity = self.copy()
                    entity.date = date
                    yield entity
        elif self.period == "yearly":
            if self.date.month == month.month and self.date.year == month.year:
                entity = self.copy()
                date = entity.date.replace(year=month.year)
                if self.billing_end is not None and date > self.billing_end:
                    return
                entity.date = date
                yield entity
        else:
            raise ValueError(f"Unknown period: {self.period}")
