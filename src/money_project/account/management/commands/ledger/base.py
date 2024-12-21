import abc
import dataclasses
import datetime
import textwrap
from decimal import Decimal
from typing import Optional


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
class Posting:
    account: str
    amount: Optional[Amount]
    tags: list[str]

    def __str__(self) -> str:
        tags = "\n".join([f"; :{t}:" for t in self.tags])

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
    tags: list[str]
    postings: list[Posting]

    @abc.abstractmethod
    def __str__(self) -> str:
        pass


@dataclasses.dataclass
class TransactionLedger(BaseLedger):
    date: datetime.date

    def __str__(self) -> str:
        date_str = self.date.strftime("%Y-%m-%d")
        tags = "\n".join([f"  ; :{t}:" for t in self.tags])

        result = []
        result.append(f'{date_str} * ({self.id}) "{self.name}"')

        if tags:
            result.append(tags)

        for posting in self.postings:
            result.append(textwrap.indent(str(posting), "  "))

        return "\n".join(result)


@dataclasses.dataclass
class RegularTransactionLedger(TransactionLedger):
    period: str
    billing_end: Optional[datetime.date]

    def __str__(self) -> str:
        return "todo"
