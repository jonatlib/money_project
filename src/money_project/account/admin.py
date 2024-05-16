from django.contrib import admin
from mptt.admin import DraggableMPTTAdmin, TreeRelatedFieldListFilter

from account.models import (
    RegularTransactionModel,
    ExtraTransactionModel,
    CategoryModel,
    CurrencyModel,
    TagModel,
    ManualAccountStateModel,
    MoneyAccountModel,
)


# Register your models here.


@admin.register(CategoryModel)
class CategoryModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [field.name for field in CategoryModel._meta.fields]


@admin.register(CurrencyModel)
class CurrencyModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [field.name for field in CurrencyModel._meta.fields]


@admin.register(ExtraTransactionModel)
class ExtraTransactionModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [
        field.name for field in ExtraTransactionModel._meta.fields
    ]
    list_filter = [
        "category",
        ("tag", TreeRelatedFieldListFilter),
        "target_account",
        "date",
    ]


@admin.register(RegularTransactionModel)
class RegularTransactionModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [
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
class TagModelAdmin(DraggableMPTTAdmin):
    list_display = [
        "tree_actions",
        "indented_title",
        "id",
        "name",
        "used_for_grouping",
        "parent",
    ]
    list_display_links = ("indented_title",)


@admin.register(ManualAccountStateModel)
class ManualAccountStateModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [
        field.name for field in ManualAccountStateModel._meta.fields
    ]


@admin.register(MoneyAccountModel)
class MoneyAccountModelAdmin(admin.ModelAdmin):
    list_display = ["__str__"] + [
        field.name for field in MoneyAccountModel._meta.fields
    ]
