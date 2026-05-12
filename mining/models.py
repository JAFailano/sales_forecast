from django.db import models


class DimProduct(models.Model):
    product_name = models.CharField(max_length=255)
    category = models.CharField(max_length=100)
    brand = models.CharField(max_length=100)

    def __str__(self):
        return self.product_name
    
    class Meta:
        verbose_name = "Product"
        verbose_name_plural = "Products"


class DimCustomer(models.Model):
    customer_name = models.CharField(max_length=255)
    customer_type = models.CharField(max_length=50)
    gender = models.CharField(max_length=10)

    def __str__(self):
        return self.customer_name

    class Meta:
        verbose_name = "Customer"
        verbose_name_plural = "Customers"

class DimTime(models.Model):
    full_date = models.DateField()
    day = models.IntegerField()
    month = models.IntegerField()
    month_name = models.CharField(max_length=20)
    quarter = models.IntegerField()
    year = models.IntegerField()

    def __str__(self):
        return str(self.full_date)
    
    class Meta:
        verbose_name = "Time"
        verbose_name_plural = "Times"

class DimStore(models.Model):
    store_name = models.CharField(max_length=255)
    location = models.CharField(max_length=255)
    city = models.CharField(max_length=100)

    def __str__(self):
        return self.store_name
    
    class Meta:
        verbose_name = "Store"
        verbose_name_plural = "Stores"


class FactSales(models.Model):
    product = models.ForeignKey(
        DimProduct,
        on_delete=models.CASCADE
    )

    customer = models.ForeignKey(
        DimCustomer,
        on_delete=models.CASCADE
    )

    time = models.ForeignKey(
        DimTime,
        on_delete=models.CASCADE
    )

    store = models.ForeignKey(
        DimStore,
        on_delete=models.CASCADE
    )

    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    total_sales = models.DecimalField(max_digits=12, decimal_places=2)

    def __str__(self):
        return f"Sale #{self.id}"