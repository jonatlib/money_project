from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter
from simple_history.admin import SimpleHistoryAdmin

from account.models import (
    CategoryModel,
    CurrencyModel,
    ExtraTransactionModel,
    LedgerName,
    ManualAccountStateModel,
    MoneyAccountModel,
    RegularTransactionModel,
    TagModel,
)


# Register your models here.


@admin.register(LedgerName)
class LedgerNameModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [field.name for field in LedgerName._meta.fields]


@admin.register(CategoryModel)
class CategoryModelAdmin(DraggableMPTTAdmin, SimpleHistoryAdmin):
    list_display = [
        "tree_actions",
        "indented_title",
        "id",
        "name",
        "color",
        "parent",
        "ledger_name",
    ]
    list_display_links = ("indented_title",)


@admin.register(CurrencyModel)
class CurrencyModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [field.name for field in CurrencyModel._meta.fields]


@admin.register(ExtraTransactionModel)
class ExtraTransactionModelAdmin(SimpleHistoryAdmin):
    list_display = ["__str__", "get_ledger"] + [
        field.name for field in ExtraTransactionModel._meta.fields
    ]
    list_filter = [
        "category",
        ("tag", TreeRelatedFieldListFilter),
        "target_account",
        "date",
    ]
    list_editable = [
        "date",
        "amount",
        "category",
        "ledger_name",
    ]
    save_as = True


@admin.register(RegularTransactionModel)
class RegularTransactionModelAdmin(SimpleHistoryAdmin):
    list_display = ["__str__", "get_ledger"] + [
        field.name for field in RegularTransactionModel._meta.fields
    ]
    list_filter = [
        "category",
        ("tag", TreeRelatedFieldListFilter),
        "target_account",
        "billing_start",
        "billing_end",
        "period",
    ]


@admin.register(TagModel)
class TagModelAdmin(DraggableMPTTAdmin, SimpleHistoryAdmin):
    list_display = [
        "tree_actions",
        "indented_title",
        "id",
        "name",
        "color",
        "used_for_grouping",
        "parent",
        "ledger_name",
    ]
    list_display_links = ("indented_title",)


@admin.register(ManualAccountStateModel)
class ManualAccountStateModelAdmin(SimpleHistoryAdmin):
    list_display = ["__str__"] + [
        field.name for field in ManualAccountStateModel._meta.fields
    ]


@admin.register(MoneyAccountModel)
class MoneyAccountModelAdmin(SimpleHistoryAdmin):
    list_display = ["__str__"] + [
        field.name for field in MoneyAccountModel._meta.fields
    ]
