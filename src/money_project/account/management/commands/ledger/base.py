import abc
import dataclasses
import datetime
from decimal import Decimal
from typing import Optional


@dataclasses.dataclass
class Posting:
    account: str
    amount: Decimal
    currency: str
    tags: list[str]

    def __str__(self) -> str:
        return "todo"


@dataclasses.dataclass
class BaseLedger(abc.ABC):
    id: str
    name: str
    description: Optional[str]
    tags: list[str]
    postings: list[Posting]

    @abc.abstractmethod
    def __str__(self):
        pass


@dataclasses.dataclass
class TransactionLedger(BaseLedger):
    date: datetime.date

    def __str__(self) -> str:
        return "todo"


@dataclasses.dataclass
class RegularTransactionLedger(TransactionLedger):
    period: str
    billing_end: Optional[datetime.date]

    def __str__(self) -> str:
        return "todo"
