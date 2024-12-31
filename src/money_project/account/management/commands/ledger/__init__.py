from typing import Iterable, Optional

from account.management.commands.ledger.base import (
    AmountSpecific,
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
    ManualAccountStateModel,
    MoneyAccountModel,
    RegularTransactionModel,
)


def in_category(text: str, category: Optional[CategoryModel]) -> bool:
    if category is None:
        return False

    c = category
    name = c.name.lower()
    if text in name:
        return True

    while c.parent is not None:
        c = c.parent
        if text in c.name.lower():
            return True

    return False


def parse_account_name(account: MoneyAccountModel) -> str:
    if ledger_name := account.get_ledger():
        return ledger_name

    name = account.name.strip().replace(" ", "_")
    return f"Assets:Checking:{name}"


def parse_expense_name(
    name: str, category: Optional[CategoryModel], tags: list[str]
) -> str:
    category_name = (category.name if category is not None else "").lower()
    return "Expenses:Unknown{}".format(
        f":{category_name.replace(" ", "_")}" if category_name else ""
    )


def parse_income_name(
    name: str, category: Optional[CategoryModel], tags: list[str]
) -> str:
    return "Income:Unknown"


def parse_source(transaction: BaseTransactionModel) -> Iterable[Posting]:
    tags = [t.name for t in transaction.tag.all()]
    currency = transaction.currency.name

    if transaction.counterparty_account is not None:
        yield Posting(
            account=parse_account_name(transaction.counterparty_account),
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )
    elif name := transaction.get_ledger():
        yield Posting(
            account=name,
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )
    elif transaction.amount < 0:
        yield Posting(
            account=parse_expense_name(transaction.name, transaction.category, tags),
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )
    else:
        yield Posting(
            account=parse_income_name(transaction.name, transaction.category, tags),
            amount=AmountTransfer(amount=-transaction.amount, currency=currency),
            tags=[],
        )


def parse_posting(transaction: BaseTransactionModel) -> Iterable[Posting]:
    sources = list(parse_source(transaction))

    # # TODO add to parse interest
    # for source in sources:
    #     if "CS_credit" in source.account:
    #         yield Posting(
    #             account="Expenses:Interest:CS_credit",
    #             amount=AmountTransfer(
    #                 amount=Decimal(1000), currency=transaction.currency.name
    #             ),
    #             tags=[],
    #         )
    #         source.amount.amount -= 1000

    yield from sources

    yield Posting(
        account=parse_account_name(transaction.target_account),
        amount=None,
        tags=[],
    )


def extra_transaction_ledger(
    transaction: ExtraTransactionModel,
) -> Iterable[BaseLedger]:
    tags = [
        t
        for t in (
            [t.name for t in transaction.tag.all()]
            + [
                (
                    "category",
                    transaction.category.name if transaction.category else None,
                ),
            ]
        )
        if t is not None
    ]
    postings = list(parse_posting(transaction))

    yield TransactionLedger(
        id=str(transaction.id),
        name=transaction.name.strip(),
        description=transaction.description.strip(),
        tags=tags,
        postings=postings,
        date=transaction.date,
    )


def regular_transaction_ledger(
    transaction: RegularTransactionModel,
) -> Iterable[BaseLedger]:
    tags = [
        t
        for t in (
            [t.name for t in transaction.tag.all()]
            + [
                (
                    "category",
                    transaction.category.name if transaction.category else None,
                ),
                ("name", transaction.name),
            ]
        )
        if t is not None
    ]
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
        name=transaction.name.strip(),
        description=transaction.description.strip(),
        tags=tags,
        postings=postings,
        date=billing_start,
        period=period,
        billing_end=billing_end,
    )


def manual_account_state_ledger(state: ManualAccountStateModel) -> Iterable[BaseLedger]:
    postings = [
        Posting(
            account=parse_account_name(state.account),
            amount=AmountSpecific(state.amount, currency=state.account.currency.name),
            tags=[],
        ),
        Posting(account="Equity:Adjustments", amount=None, tags=[]),
    ]

    name = f"Manual adjustment for account {state.account.name} on {state.date}"

    yield TransactionLedger(
        id=f"manual_{state.id}",
        name=name,
        description="",
        tags=[("name", name)],
        postings=postings,
        date=state.date,
    )


def extra_transaction_ledgers(
    transactions: Iterable[ExtraTransactionModel],
) -> Iterable[TransactionLedger]:
    for transaction in transactions:
        yield from extra_transaction_ledger(transaction)


def regular_transaction_ledgers(
    transactions: Iterable[RegularTransactionModel],
) -> Iterable[RegularTransactionLedger]:
    for transaction in transactions:
        yield from regular_transaction_ledger(transaction)


def manual_account_state_ledgers(
    states: Iterable[ManualAccountStateModel],
) -> Iterable[TransactionLedger]:
    for state in states:
        yield from manual_account_state_ledger(state)
