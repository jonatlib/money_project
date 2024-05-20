import calendar
from datetime import date, timedelta

import pandas as pd
import plotly.express as px
from django.views.generic import TemplateView
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
        previous_month = start_of_month - timedelta(days=1)

        all_year_balance = get_real_account_balance(accounts, start_date, end_date)
        all_expenses_this_month = BaseTransactionModel.objects.build_dataframe_all(
            accounts, start_of_month, end_of_month
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
        accounts_stats = None

        expenses_until_month_end = None
        incomes_until_month_end = None

        #####################################################

        context["accounts"] = accounts

        context["figure_category"] = build_category_chart(
            expenses_per_category.reset_index(), x="category", y="amount"
        )
        context["figure_tags"] = build_category_chart(
            expenses_per_tag.reset_index(), x="tags", y="amount"
        )

        context["figure_balance"] = build_balance_chart(
            all_year_balance.reset_index(), "date", "balance"
        )

        return context
