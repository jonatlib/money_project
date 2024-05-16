from datetime import date

import pandas as pd

from ..models import BaseTransactionModel, MoneyAccountModel


def get_expenses_per_category(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionModel.objects.build_dataframe_all(
        accounts, start_date, end_date
    )
    try:
        df = df[df.amount < 0]
    except AttributeError:
        return df

    df.category.fillna("-", inplace=True)
    return df.groupby(["account", "category"])[["amount"]].sum()


def get_expenses_per_category_per_month(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionModel.objects.build_dataframe_all(
        accounts, start_date, end_date
    )
    try:
        df = df[df.amount < 0]
    except AttributeError:
        return df

    df.category.fillna("-", inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    return df.groupby(["account", "category", pd.Grouper(freq="ME", key="date")])[
        ["amount"]
    ].sum()
