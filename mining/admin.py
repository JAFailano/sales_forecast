from django.contrib import admin
from .models import (
    DimProduct,
    DimCustomer,
    DimTime,
    DimStore,
    FactSales
)


@admin.register(DimProduct)
class DimProductAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product_name',
        'category',
        'brand'
    )

    search_fields = (
        'product_name',
        'category',
        'brand'
    )


@admin.register(DimCustomer)
class DimCustomerAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'customer_name',
        'customer_type',
        'gender'
    )

    search_fields = (
        'customer_name',
        'customer_type'
    )

    list_filter = (
        'customer_type',
        'gender'
    )


@admin.register(DimTime)
class DimTimeAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'full_date',
        'month_name',
        'year',
        'quarter'
    )

    list_filter = (
        'year',
        'quarter',
        'month_name'
    )


@admin.register(DimStore)
class DimStoreAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'store_name',
        'location',
        'city'
    )

    search_fields = (
        'store_name',
        'city'
    )


@admin.register(FactSales)
class FactSalesAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'product',
        'customer',
        'store',
        'time',
        'quantity',
        'unit_price',
        'total_sales'
    )

    list_filter = (
        'store',
        'time'
    )

    search_fields = (
        'product__product_name',
        'customer__customer_name'
    )