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
    name = account.name.strip().replace(" ", "_")
    if "portu" in name.lower():
        return "Assets:Investments:Portu"

    return f"Assets:Checking:{name}"


def parse_any_name(
    name: str, category: Optional[CategoryModel], tags: list[str]
) -> Optional[str]:
    name = name.strip().lower()
    tags_names = [t.lower() for t in tags]

    if in_category("invest", category) and "investown" in name:
        return "Assets:Investments:Investown"

    if in_category("invest", category) and "portu" in name:
        return "Assets:Investments:Portu"

    if in_category("invest", category):
        return "Assets:Investments:Unknown"

    if in_category("debts", category) and "uver" in name:
        return "Liabilities:Debt:CS_credit"

    if in_category("debts", category) and "hypoteka" in name:
        return "Liabilities:Debt:Mortgage"

    if in_category("debts", category):
        return "Liabilities:Debt:Unknown"

    if in_category("insurance", category):
        return "Expenses:Insurance"
    if in_category("car", category):
        return "Expenses:Utilities:Car"

    return None


def parse_expense_name(
    name: str, category: Optional[CategoryModel], tags: list[str]
) -> str:
    any_parse = parse_any_name(name, category, tags)
    if any_parse is not None:
        return any_parse

    category_name = (category.name if category is not None else "").lower()
    tags_names = [t.lower() for t in tags]

    if "tax" in name.lower() or "osvc" in name.lower() or in_category("osvc", category):
        return "Expenses:Tax:Income"

    return "Expenses:Unknown{}".format(
        f":{category_name.replace(" ", "_")}" if category_name else ""
    )


def parse_income_name(
    name: str, category: Optional[CategoryModel], tags: list[str]
) -> str:
    any_parse = parse_any_name(name, category, tags)
    if any_parse is not None:
        return any_parse

    tags_names = [t.lower() for t in tags]

    if in_category("error", category):
        return "Equity:Adjustments"

    if "income" in name.lower():
        return "Income:Salary:Quantlane"

    if "tax" in name.lower() or "osvc" in name.lower() or in_category("osvc", category):
        return "Income:Tax:Income"

    return "Income:Unknown"


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
