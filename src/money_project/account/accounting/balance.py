from datetime import date

import pandas as pd

from ..models import BaseTransactionModel, MoneyAccountModel, ManualAccountStateModel


def get_ideal_account_balance(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    df = BaseTransactionModel.objects.build_dataframe_all(
        accounts, start_date, end_date
    )

    try:
        result = (
            df.groupby(["date", "account_id"])
            .agg(
                amount=("amount", "sum"),
            )
            .reset_index()
        )
    except KeyError:
        return df

    # Reindex and add missing dates in range
    back_fill_df = pd.date_range(start_date, end_date, freq="D")
    result = (
        result.set_index(["account_id", "date"])
        .reindex(
            pd.MultiIndex.from_product(
                [[a.id for a in accounts], back_fill_df], names=["account_id", "date"]
            ),
        )
        .reset_index()
    )
    result.amount.fillna(0, inplace=True)
    result.date = result.date.apply(lambda x: x.date())

    # Compute balance
    result.sort_values(by=["account_id", "date"], ascending=True, inplace=True)
    result["f_amount"] = result.amount.astype("float64")
    result["balance"] = result.groupby("account_id").f_amount.cumsum()

    result = result[["account_id", "date", "amount", "balance"]].set_index(
        ["account_id", "date"]
    )
    return result


def get_real_account_balance(
    accounts: list[MoneyAccountModel], start_date: date, end_date: date
) -> pd.DataFrame:
    ideal_df = get_ideal_account_balance(accounts, start_date, end_date)
    if ideal_df.empty:
        return ideal_df

    # TODO do we need to filter by start date?
    manual_states = [
        {
            "date": state.date,
            "balance_snapshot": state.amount,
            "account_id": state.account.id,
        }
        for state in ManualAccountStateModel.objects.filter(
            account__in=accounts, date__lte=end_date
        )
    ]
    if not manual_states:
        ideal_df["real_balance"] = ideal_df["balance"]
        ideal_df["balance_snapshot"] = pd.NA
        return ideal_df

    manual_states_df = pd.DataFrame(manual_states).set_index(["account_id", "date"])

    df = pd.concat([ideal_df, manual_states_df], axis=1, join="outer")
    df.balance = df.groupby(["account_id"]).balance.fillna(method="ffill")
    df.amount.fillna(0, inplace=True)
    df["balance_snapshot_ffill"] = df["balance_snapshot"].astype("float64")
    df.balance_snapshot_ffill = (
        df.groupby(["account_id"])
        .balance_snapshot_ffill.fillna(method="ffill")
        .fillna(0)
    )

    df["real_balance"] = (
        df.balance
        - (
            df.where(~df.balance_snapshot.isna())
            .groupby(["account_id"])
            .balance.ffill()
            .fillna(0)
        )
        + df.balance_snapshot_ffill
    )

    # TODO maybe cut the dataframe according to start and end
    # TODO as this can be bigger because of the manual balance updates
    return df[["amount", "balance", "real_balance", "balance_snapshot"]]
