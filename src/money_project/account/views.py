from datetime import date

import plotly.express as px
from django.views.generic import TemplateView

from .accounting.balance import get_real_account_balance
from .accounting.expence import (
    get_expenses_per_category,
    get_expenses_per_category_per_month,
    get_expenses_per_tag,
    get_expenses_per_tag_per_month,
)
from .models import MoneyAccountModel


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        accounts = MoneyAccountModel.objects.all()
        start_date = date(2024, 1, 1)
        end_date = date(2024, 12, 31)

        context["balance"] = get_real_account_balance(
            accounts, start_date, end_date
        ).to_html()
        context["expenses"] = get_expenses_per_category(
            accounts, start_date, end_date
        ).to_html()
        context["expenses_month"] = get_expenses_per_category_per_month(
            accounts, start_date, end_date
        ).to_html()
        context["expenses_tag"] = get_expenses_per_tag(
            accounts, start_date, end_date
        ).to_html()
        context["expenses_tag_per_month"] = get_expenses_per_tag_per_month(
            accounts, start_date, end_date
        ).to_html()

        figure = px.bar(
            get_expenses_per_category(accounts, start_date, end_date).reset_index()[
                ["category", "amount"]
            ],
            y="amount",
            x="category",
            template="none",
        )
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
        context["figure"] = figure.to_html(config={"staticPlot": True}, full_html=False)

        return context
