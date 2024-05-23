import calendar
from datetime import date, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from django.views.generic import TemplateView
from pandas.tseries.offsets import DateOffset
from plotly.graph_objects import Figure

from ..accounting.balance import get_real_account_balance
from ..accounting.expence import (
    get_expenses_per_category,
    get_expenses_per_category_per_month,
    get_expenses_per_tag,
    get_expenses_per_tag_per_month,
)
from ..models import MoneyAccountModel, BaseTransactionModel

DEFAULT_LAYOUT = {
    "plot_bgcolor": "rgba(0, 0, 0, 0)",
    "paper_bgcolor": "rgba(0, 0, 0, 0)",
    "margin": dict(l=20, r=20, t=20, b=20),
    "xaxis_title": None,
    "yaxis_title": None,
}


def default_figure_layout(figure: Figure):
    figure.update_layout(
        {
            "plot_bgcolor": "rgba(0, 0, 0, 0)",
            "paper_bgcolor": "rgba(0, 0, 0, 0)",
            "margin": dict(l=20, r=20, t=20, b=20),
            "xaxis_title": None,
            "yaxis_title": None,
        }
    )
    figure.update_yaxes(automargin=True)


def build_category_chart(df: pd.DataFrame, x: str, y: str) -> str:
    figure = px.bar(df, x=x, y=y, template="none")
    default_figure_layout(figure)
    # return figure.to_html(config={"staticPlot": True}, full_html=False)
    return figure.to_html(config={}, full_html=False)


def build_balance_chart(df: pd.DataFrame, x: str, y: str, **kwargs) -> str:
    figure = px.area(df, x=x, y=y, template="none", **kwargs)
    default_figure_layout(figure)
    figure.update_layout({"width": 1000})
    return figure.to_html(full_html=False)


def build_balance_waterfall_chart(df: pd.DataFrame, x: str, y: str, base: float) -> str:
    x_data = df[x].values
    y_data = df[y].values

    figure = go.Figure(
        go.Waterfall(
            x=x_data,
            y=y_data,
            base=base,
            # measure=["relative" for _ in range(len(x_data))],
        )
    )

    default_figure_layout(figure)
    figure.update_layout({"width": 1000})
    return figure.to_html(full_html=False)


def build_balance_waterfall_chart_diff(
    df: pd.DataFrame, x: str, y: str, base: float
) -> str:
    x_data = df[x].values
    y_data = (df[y].shift(-1) - df[y]).values

    figure = go.Figure(
        go.Waterfall(
            x=x_data,
            y=y_data,
            base=base,
            # measure=["relative" for _ in range(len(x_data))],
        )
    )

    default_figure_layout(figure)
    figure.update_layout({"width": 1000})
    return figure.to_html(full_html=False)


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounts = MoneyAccountModel.objects.all()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)
        period_days = (end_date - start_date).days + 1

        today = date.today()
        start_of_month = date.today().replace(day=1)
        end_of_month = date.today().replace(
            day=calendar.monthrange(today.year, today.month)[1]
        )
        previous_month_today = (start_of_month - DateOffset(months=1)).date()
        end_of_year = date.today().replace(
            day=calendar.monthrange(today.year, 12)[1], month=12
        )

        all_year_balance_with_ignored = get_real_account_balance(
            accounts, start_date, end_date
        ).reset_index()
        all_year_balance_with_ignored["account"] = (
            all_year_balance_with_ignored.account_id.apply(
                lambda v: MoneyAccountModel.objects.get(id=v).name
            )
        )
        # FIXME when this won't return any account it will crash the view
        all_year_balance = get_real_account_balance(
            accounts.filter(include_in_statistics=True), start_date, end_date
        ).reset_index()
        all_year_balance["account"] = all_year_balance.account_id.apply(
            lambda v: MoneyAccountModel.objects.get(id=v).name
        )

        all_transactions_this_month = BaseTransactionModel.objects.build_dataframe_all(
            accounts, start_of_month, end_of_month
        )
        all_transactions_next_month = BaseTransactionModel.objects.build_dataframe_all(
            accounts,
            (start_of_month + DateOffset(months=1)).date(),
            (end_of_month + DateOffset(months=1)).date(),
        )

        expenses_per_category = get_expenses_per_category(
            accounts, start_date, end_date
        )
        expenses_per_tag = get_expenses_per_tag(accounts, start_date, end_date)

        expenses_per_category_per_month = get_expenses_per_category_per_month(
            accounts, start_date, end_date
        )
        expenses_per_tag_per_month = get_expenses_per_tag_per_month(
            accounts, start_date, end_date
        )

        #####################################################

        # Real balance, model balance
        # % change to end of previous month
        # state: month: begin, end
        #       end of year
        # month stats:
        #       all expenses
        #       remaining expenses
        #       next month expenses

        # Expanses
        per_account_next_month_expenses = (
            all_transactions_next_month[all_transactions_next_month.amount < 0]
            .reset_index()
            .groupby("account_id")[["amount"]]
            .sum()
            .to_dict()["amount"]
        )
        per_account_this_month_expenses = (
            all_transactions_this_month[all_transactions_this_month.amount < 0]
            .reset_index()
            .groupby("account_id")[["amount"]]
            .sum()
            .to_dict()["amount"]
        )
        per_account_this_month_remaining_expenses = (
            all_transactions_this_month[
                (all_transactions_this_month.amount < 0)
                & (all_transactions_this_month.date > today)
            ]
            .reset_index()
            .groupby("account_id")[["amount"]]
            .sum()
            .to_dict()["amount"]
        )

        # Upcoming events
        upcoming_events = pd.concat(
            [
                all_transactions_this_month.set_index(["account_id", "date"]),
                all_transactions_next_month.set_index(["account_id", "date"]),
            ]
        ).reset_index()
        upcoming_events = upcoming_events[
            (upcoming_events.date > today)
            & (upcoming_events.date <= (today + timedelta(days=10)))
        ]
        upcoming_events["days"] = upcoming_events.date.apply(lambda v: (v - today).days)
        # FIXME not working when no data on account
        upcoming_events["formatted_amount"] = upcoming_events[
            ["account_id", "amount"]
        ].apply(
            lambda v: MoneyAccountModel.objects.get(
                id=v.account_id
            ).currency.format_currency(v.amount),
            axis=1,
        )

        # Balances
        today_balance_df = all_year_balance[all_year_balance.date == today].set_index(
            "account_id"
        )
        today_balance = today_balance_df.to_dict()

        today_previous_month_balance_df = all_year_balance[
            all_year_balance.date == previous_month_today
        ].set_index("account_id")
        a = today_previous_month_balance_df[["balance", "real_balance"]]
        b = today_balance_df[["balance", "real_balance"]]
        today_previous_month_balance_df = pd.concat(
            [
                today_previous_month_balance_df,
                (((a - b) / a) * 100)
                .replace([np.inf, -np.inf, np.nan], 0)
                .applymap(int)
                .add_suffix("_change"),
            ],
            axis=1,
        )
        today_previous_month_balance = today_previous_month_balance_df.to_dict()

        # Balances in time
        start_of_month_balance = (
            all_year_balance[all_year_balance.date == start_of_month]
            .set_index("account_id")
            .to_dict()
        )
        end_of_month_balance = (
            all_year_balance[all_year_balance.date == end_of_month]
            .set_index("account_id")
            .to_dict()
        )
        end_of_year_balance = (
            all_year_balance[all_year_balance.date == end_of_year]
            .set_index("account_id")
            .to_dict()
        )

        # per_account_this_month_remaining_expenses = (
        #     all_transactions_this_month[all_transactions_this_month.date > today]
        #     .groupby("account")[["amount"]]
        #     .sum()
        # ).to_dict()
        # per_account_end_of_year_balance = (
        #     all_year_balance.groupby("account")[["amount"]].last().to_dict()
        # )

        # context["tmp"] = today_previous_month_balance

        #####################################################

        context["accounts"] = [
            {
                #
                # Django model
                "model": account,
                #
                # Expanses
                "next_month_expenses": account.currency.format_currency(
                    per_account_next_month_expenses.get(account.id, 0)
                ),
                "this_month_expenses": account.currency.format_currency(
                    per_account_this_month_expenses.get(account.id, 0)
                ),
                "this_month_remaining_expenses": account.currency.format_currency(
                    per_account_this_month_remaining_expenses.get(account.id, 0)
                ),
                #
                # Balances
                "balance_raw": today_balance["balance"].get(account.id, 0),
                "balance": account.currency.format_currency(
                    today_balance["balance"].get(account.id, 0)
                ),
                "real_balance_raw": today_balance["real_balance"].get(account.id, 0),
                "real_balance": account.currency.format_currency(
                    today_balance["real_balance"].get(account.id, 0)
                ),
                #
                # Balances in time
                "real_balance_start_of_month": account.currency.format_currency(
                    start_of_month_balance["real_balance"].get(account.id, 0)
                ),
                "real_balance_end_of_month": account.currency.format_currency(
                    end_of_month_balance["real_balance"].get(account.id, 0)
                ),
                "real_balance_end_of_year": account.currency.format_currency(
                    end_of_year_balance["real_balance"].get(account.id, 0)
                ),
                #
                # Last month today balances
                "balance_today_last_month_raw": today_previous_month_balance[
                    "balance"
                ].get(account.id, 0),
                "balance_today_last_month": account.currency.format_currency(
                    today_previous_month_balance["balance"].get(account.id, 0)
                ),
                "real_balance_today_last_month_raw": today_previous_month_balance[
                    "real_balance"
                ].get(account.id, 0),
                "real_balance_today_last_month": account.currency.format_currency(
                    today_previous_month_balance["real_balance"].get(account.id, 0)
                ),
                # Last month today balance change
                "balance_today_last_month_change": today_previous_month_balance[
                    "balance_change"
                ].get(account.id, 0),
                "real_balance_today_last_month_change": today_previous_month_balance[
                    "real_balance_change"
                ].get(account.id, 0),
            }
            for account in accounts
        ]

        context["figure_category"] = build_category_chart(
            expenses_per_category.reset_index()
            .groupby("category")
            .sum()
            .reset_index()
            .sort_values(by="amount"),
            x="category",
            y="amount",
        )
        context["figure_tags"] = build_category_chart(
            expenses_per_tag.reset_index()
            .groupby("tags")
            .sum()
            .reset_index()
            .sort_values(by="amount"),
            x="tags",
            y="amount",
        )

        context["figure_daily_balance"] = build_balance_chart(
            all_year_balance.groupby("date")[["real_balance"]].sum().reset_index(),
            x="date",
            y="real_balance",
        )

        context["figure_daily_balance_accounts_not_ignored"] = build_balance_chart(
            all_year_balance[["account", "date", "real_balance"]].reset_index(),
            x="date",
            y="real_balance",
            color="account",
        )
        context["figure_daily_balance_accounts"] = build_balance_chart(
            all_year_balance_with_ignored[
                ["account", "date", "real_balance"]
            ].reset_index(),
            x="date",
            y="real_balance",
            color="account",
        )
        context["figure_daily_model_balance_accounts"] = build_balance_chart(
            all_year_balance_with_ignored[["account", "date", "balance"]].reset_index(),
            x="date",
            y="balance",
            color="account",
        )

        waterfall_balance = all_year_balance.copy()
        waterfall_balance.date = all_year_balance.date.apply(pd.Timestamp)
        waterfall_balance = (
            waterfall_balance.groupby("date")[["real_balance"]]
            .sum()
            .groupby(pd.Grouper(freq="M"))
            .agg(first=("real_balance", "first"), last=("real_balance", "last"))
            .reset_index()
        )
        waterfall_balance["diff"] = (
            waterfall_balance["last"] - waterfall_balance["last"].shift(1)
        ).fillna(waterfall_balance["last"].iloc[0] - waterfall_balance["first"].iloc[0])
        context["figure_balance"] = build_balance_waterfall_chart(
            waterfall_balance,
            "date",
            "diff",
            # FIXME when moving from previous year
            base=all_year_balance.groupby("date").real_balance.sum().iloc[0],
        )

        daily_balance_this_month = all_year_balance[
            (all_year_balance.date >= start_of_month)
            & (all_year_balance.date <= end_of_month)
        ]
        daily_balance_this_month.date = daily_balance_this_month.date.apply(
            pd.Timestamp
        )
        context["figure_daily_balance_this_month"] = build_balance_waterfall_chart_diff(
            daily_balance_this_month.groupby("date")[["real_balance"]]
            .sum()
            .reset_index(),
            "date",
            "real_balance",
            # FIXME this return balance in first day of month we should return last day of month
            base=sum(start_of_month_balance["real_balance"].values()),
        )

        context["upcoming_expenses"] = upcoming_events[
            upcoming_events.amount < 0
        ].to_dict(orient="records")
        context["upcoming_incomes"] = upcoming_events[
            upcoming_events.amount >= 0
        ].to_dict(orient="records")

        return context
