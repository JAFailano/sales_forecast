from django.urls import path
from .views import customer_clustering
from .views import (
    upload_sales_excel,
    sales_forecasting,
    customer_clustering   # 👈 ADD THIS
)

urlpatterns = [
    path('', upload_sales_excel, name='upload_sales_excel'),
    path('forecast/', sales_forecasting, name='sales_forecasting'),
    path('clustering/', customer_clustering, name='clustering'),  # 👈 FIXED
]