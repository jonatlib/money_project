from django.contrib import admin

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
    pass


@admin.register(CurrencyModel)
class CurrencyModelAdmin(admin.ModelAdmin):
    pass


@admin.register(ExtraTransactionModel)
class ExtraTransactionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(RegularTransactionModel)
class RegularTransactionModelAdmin(admin.ModelAdmin):
    pass


@admin.register(TagModel)
class TagModelAdmin(admin.ModelAdmin):
    pass


@admin.register(ManualAccountStateModel)
class ManualAccountStateModelAdmin(admin.ModelAdmin):
    pass


@admin.register(MoneyAccountModel)
class MoneyAccountModelAdmin(admin.ModelAdmin):
    pass
