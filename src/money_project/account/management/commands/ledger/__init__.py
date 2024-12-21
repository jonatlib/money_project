from typing import Iterable

from account.management.commands.ledger.base import (
    BaseLedger,
    Posting,
    RegularTransactionLedger,
    TransactionLedger,
)
from account.models import (
    BaseTransactionModel,
    ExtraTransactionModel,
    RegularTransactionModel,
)


def parse_posting(transaction: BaseTransactionModel) -> list[Posting]:
    category = transaction.category
    tags = [t.name for t in transaction.tag.all()]

    pass


def extra_transaction_ledger(
    transaction: ExtraTransactionModel,
) -> Iterable[BaseLedger]:
    tags = [t.name for t in transaction.tag.all()]
    postings = parse_posting(transaction)

    yield TransactionLedger(
        id=str(transaction.id),
        name=transaction.name,
        description=transaction.description,
        tags=tags,
        postings=postings,
        date=transaction.date,
    )


def regular_transaction_ledger(
    transaction: RegularTransactionModel,
) -> Iterable[BaseLedger]:
    tags = [t.name for t in transaction.tag.all()]
    postings = parse_posting(transaction)

    period = {
        "Yearly": "yearly",
        "Quarterly": "quarterly",
        "Half-Yearly": "every 2 months",
        "Monthly": "monthly",
        "Weekly": "weekly",
        "Daily": "daily",
        # TODO support workdays by yielding multiple entities
        "Work-Day": "daily",
    }[str(transaction.period)]
    billing_start = transaction.billing_start
    billing_end = transaction.billing_end

    yield RegularTransactionLedger(
        id=str(transaction.id),
        name=transaction.name,
        description=transaction.description,
        tags=tags,
        postings=postings,
        date=billing_start,
        period=period,
        billing_end=billing_end,
    )


def extra_transaction_ledgers(
    transactions: Iterable[ExtraTransactionModel],
) -> Iterable[BaseLedger]:
    for transaction in transactions:
        yield from extra_transaction_ledger(transaction)


def regular_transaction_ledgers(
    transactions: Iterable[RegularTransactionModel],
) -> Iterable[BaseLedger]:
    for transaction in transactions:
        yield from regular_transaction_ledger(transaction)
