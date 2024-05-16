from _datetime import date

import pandas as pd

from ..models import BaseTransactionModel, MoneyAccountModel


def get_ideal_account_balance(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionModel.objects.build_dataframe_all(
        accounts, start_date, end_date
    )

    result = (
        df.groupby(["date", "account"])
        .agg(
            amount=("amount", "sum"),
        )
        .reset_index()
    )
    result.sort_values(by=["account", "date"], ascending=True, inplace=True)
    result["f_amount"] = result.amount.astype("float64")
    result["balance"] = result.groupby("account").f_amount.cumsum()

    return result[["account", "date", "amount", "balance"]]
