import calendar
from datetime import date

import numpy as np
import pandas as pd
import plotly.express as px
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
    return figure.to_html(config={"staticPlot": True}, full_html=False)


def build_balance_chart(df: pd.DataFrame, x: str, y: str) -> str:
    figure = px.line(df, x=x, y=y, template="none")
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

        all_year_balance = get_real_account_balance(
            accounts, start_date, end_date
        ).reset_index()
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

        today_balance_df = all_year_balance[all_year_balance.date == today].set_index(
            "account_id"
        )
        today_balance = today_balance_df.to_dict()

        today_previous_month_balance_df = all_year_balance[
            all_year_balance.date == previous_month_today
        ].set_index("account_id")
        a = today_balance_df[["balance", "real_balance"]]
        b = today_previous_month_balance_df[["balance", "real_balance"]]
        today_previous_month_balance_df = pd.concat(
            [
                today_previous_month_balance_df,
                (((b - a) / b) * 100)
                .replace([np.inf, -np.inf], 0)
                .applymap(int)
                .add_suffix("_change"),
            ],
            axis=1,
        )
        today_previous_month_balance = today_previous_month_balance_df.to_dict()

        # per_account_this_month_remaining_expenses = (
        #     all_transactions_this_month[all_transactions_this_month.date > today]
        #     .groupby("account")[["amount"]]
        #     .sum()
        # ).to_dict()
        # per_account_end_of_year_balance = (
        #     all_year_balance.groupby("account")[["amount"]].last().to_dict()
        # )

        context["tmp"] = today_previous_month_balance

        #####################################################

        context["accounts"] = [
            {
                "model": account,
                "next_month_expenses": account.currency.format_currency(
                    per_account_next_month_expenses.get(account.id, 0)
                ),
                "this_month_expenses": account.currency.format_currency(
                    per_account_this_month_expenses.get(account.id, 0)
                ),
                "balance_raw": today_balance["balance"].get(account.id, 0),
                "balance": account.currency.format_currency(
                    today_balance["balance"].get(account.id, 0)
                ),
                "real_balance_raw": today_balance["real_balance"].get(account.id, 0),
                "real_balance": account.currency.format_currency(
                    today_balance["real_balance"].get(account.id, 0)
                ),
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
            expenses_per_category.reset_index(), x="category", y="amount"
        )
        context["figure_tags"] = build_category_chart(
            expenses_per_tag.reset_index(), x="tags", y="amount"
        )

        context["figure_balance"] = build_balance_chart(
            all_year_balance.groupby("date")[["real_balance"]].sum().reset_index(),
            "date",
            "real_balance",
        )

        return context
