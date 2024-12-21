from typing import Iterable, Optional

from account.management.commands.ledger.base import (
    AmountTransfer,
    BaseLedger,
    Posting,
    RegularTransactionLedger,
    TransactionLedger,
)
from account.models import (
    BaseTransactionModel,
    CategoryModel,
    ExtraTransactionModel,
    MoneyAccountModel,
    RegularTransactionModel,
)


def parse_account_name(account: MoneyAccountModel) -> str:
    return f"Assets:Checking:{account.name}"


def parse_expense_name(category: Optional[CategoryModel], tags: list[str]) -> str:
    category_name = category.name if category is not None else ""
    return "Expenses{}".format(f":{category_name}" if category_name else "")


def parse_income_name(
    name: str, category: Optional[CategoryModel], tags: list[str]
) -> str:
    return "Income:Salary:Quantlane"


def parse_posting(transaction: BaseTransactionModel) -> Iterable[Posting]:
    tags = [t.name for t in transaction.tag.all()]
    currency = transaction.currency.name

    if transaction.counterparty_account is not None:
        yield Posting(
            account=parse_account_name(transaction.counterparty_account),
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )
    elif transaction.amount < 0:
        yield Posting(
            account=parse_expense_name(transaction.category, tags),
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )
    else:
        yield Posting(
            account=parse_income_name(transaction.name, transaction.category, tags),
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )

    yield Posting(
        account=parse_account_name(transaction.target_account),
        amount=None,
        tags=[],
    )


def extra_transaction_ledger(
    transaction: ExtraTransactionModel,
) -> Iterable[BaseLedger]:
    tags = [t.name for t in transaction.tag.all()]
    postings = list(parse_posting(transaction))

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
    postings = list(parse_posting(transaction))

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
