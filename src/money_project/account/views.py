from datetime import date

from django.views.generic import TemplateView

from .accounting.expence import (
    get_expenses_per_category,
    get_expenses_per_category_per_month,
)
from .models import MoneyAccountModel


class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["expenses"] = get_expenses_per_category(
            MoneyAccountModel.objects.all(),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        ).to_html()

        context["expenses_month"] = get_expenses_per_category_per_month(
            MoneyAccountModel.objects.all(),
            start_date=date(2024, 1, 1),
            end_date=date(2024, 12, 31),
        ).to_html()

        return context
