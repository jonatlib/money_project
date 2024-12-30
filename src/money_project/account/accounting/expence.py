from datetime import date

import pandas as pd

from ..models import MoneyAccountModel
from ..models.transaction import BaseTransactionManager


# FIXME implement ignored transactinos?


def get_expenses_per_category(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionManager.build_dataframe_all(accounts, start_date, end_date)
    try:
        df = df[df.amount < 0]
    except AttributeError:
        return df

    df.category.fillna("-", inplace=True)
    return df.groupby(["account", "category"])[["amount"]].sum()


def get_expenses_per_category_per_month(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionManager.build_dataframe_all(accounts, start_date, end_date)
    try:
        df = df[df.amount < 0]
    except AttributeError:
        return df

    df.category.fillna("-", inplace=True)
    df["date"] = pd.to_datetime(df["date"])
    return df.groupby(["account", "category", pd.Grouper(freq="ME", key="date")])[
        ["amount"]
    ].sum()


def get_expenses_per_tag(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionManager.build_dataframe_all(accounts, start_date, end_date)
    try:
        df = df[df.amount < 0]
    except AttributeError:
        return df

    df = df.explode(["tags", "tag_ids"], ignore_index=True)
    return df.groupby(["account", "tags", "tag_ids"])[["amount"]].sum()


def get_expenses_per_tag_per_month(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionManager.build_dataframe_all(accounts, start_date, end_date)
    try:
        df = df[df.amount < 0]
    except AttributeError:
        return df

    df = df.explode(["tags", "tag_ids"], ignore_index=True)
    df["date"] = pd.to_datetime(df["date"])
    return df.groupby(
        ["account", "tags", "tag_ids", pd.Grouper(freq="ME", key="date")]
    )[["amount"]].sum()
