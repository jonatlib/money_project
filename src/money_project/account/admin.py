from django.contrib import admin

from models import (
    BaseExpenseModel,
    CategoryModel,
    CurrencyModel,
    ExtraExpenseModel,
    RegularExpenseModel,
    TagModel,
    ManualAccountStateModel,
    MoneyAccountModel,
)


# Register your models here.


@admin.register(BaseExpenseModel)
class BaseExpenseModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CategoryModel)
class CategoryModelAdmin(admin.ModelAdmin):
    pass


@admin.register(CurrencyModel)
class CurrencyModelAdmin(admin.ModelAdmin):
    pass


@admin.register(ExtraExpenseModel)
class ExtraExpenseModelAdmin(admin.ModelAdmin):
    pass


@admin.register(RegularExpenseModel)
class RegularExpenseModelAdmin(admin.ModelAdmin):
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
