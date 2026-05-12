import pandas as pd
import numpy as np
import json
from django.db.models import Sum, Count
from .models import FactSales
from django.db.models import Sum
from sklearn.linear_model import LinearRegression
from sklearn.cluster import KMeans
from django.shortcuts import render, redirect
from django.contrib import messages
from .models import (
    DimProduct,
    DimCustomer,
    DimTime,
    DimStore,
    FactSales
)


def upload_sales_excel(request):

    if request.method == 'POST' and request.FILES.get('excel_file'):

        excel_file = request.FILES['excel_file']

        try:
            # =========================
            # EXTRACT
            # =========================
            df = pd.read_excel(excel_file)
   

            # =========================
            # TRANSFORM / CLEANING
            # =========================

            # Remove duplicate rows
            df.drop_duplicates(inplace=True)

            # Remove completely empty rows
            df.dropna(how='all', inplace=True)

            # Fill missing values
            df['Customer_Name'] = df['Customer_Name'].fillna('Unknown Customer')
            df['Customer_Type'] = df['Customer_Type'].fillna('Regular')
            df['Gender'] = df['Gender'].fillna('Unknown')
            # Ensure Brand column exists
            if 'Brand' not in df.columns:
                df['Brand'] = 'Generic'

            df['Brand'] = df['Brand'].fillna('Generic')

            # Define text columns correctly
            text_columns = [
                'Product_Name',
                'Category',
                'Brand',
                'Customer_Name',
                'Customer_Type',
                'Gender',
                'Store_Name',
                'City'
            ]

            for col in text_columns:
                df[col] = df[col].astype(str).str.strip()

            # Standardize text capitalization
            df['Product_Name'] = df['Product_Name'].str.title()
            df['Category'] = df['Category'].str.title()
            df['Customer_Name'] = df['Customer_Name'].str.title()
            df['Store_Name'] = df['Store_Name'].str.title()
            df['City'] = df['City'].str.title()

            # Convert numeric fields
            df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')
            df['Unit_Price'] = pd.to_numeric(df['Unit_Price'], errors='coerce')
            df['Total_Sales'] = pd.to_numeric(df['Total_Sales'], errors='coerce')

            # Replace invalid numeric values
            df['Quantity'] = df['Quantity'].fillna(1)
            df['Unit_Price'] = df['Unit_Price'].fillna(0)
            df['Total_Sales'] = df['Total_Sales'].fillna(0)

            # Remove negative values
            df = df[df['Quantity'] >= 0]
            df = df[df['Unit_Price'] >= 0]
            df = df[df['Total_Sales'] >= 0]

            # Convert date column
            df['Sale_Date'] = pd.to_datetime(df['Sale_Date'], errors='coerce')

            # Remove invalid dates
            df = df[df['Sale_Date'].notnull()]

            # =========================
            # LOAD INTO DATA WAREHOUSE
            # =========================

            for _, row in df.iterrows():

                # Product Dimension
                product, _ = DimProduct.objects.get_or_create(
                    product_name=row['Product_Name'],
                    defaults={
                        'category': row['Category'],
                        'brand': row['Brand']
                    }
                )

                # Customer Dimension
                customer, _ = DimCustomer.objects.get_or_create(
                    customer_name=row['Customer_Name'],
                    defaults={
                        'customer_type': row['Customer_Type'],
                        'gender': row['Gender']
                    }
                )

                # Time Dimension
                sale_date = row['Sale_Date']

                month = sale_date.month

                if month <= 3:
                    quarter = 1
                elif month <= 6:
                    quarter = 2
                elif month <= 9:
                    quarter = 3
                else:
                    quarter = 4

                time_obj, _ = DimTime.objects.get_or_create(
                    full_date=sale_date.date(),
                    defaults={
                        'day': sale_date.day,
                        'month': sale_date.month,
                        'month_name': sale_date.strftime('%B'),
                        'quarter': quarter,
                        'year': sale_date.year
                    }
                )

                # Store Dimension
                store, _ = DimStore.objects.get_or_create(
                    store_name=row['Store_Name'],
                    defaults={
                        'location': row['City'],
                        'city': row['City']
                    }
                )

                # Fact Table
                FactSales.objects.create(
                    product=product,
                    customer=customer,
                    time=time_obj,
                    store=store,
                    quantity=int(row['Quantity']),
                    unit_price=float(row['Unit_Price']),
                    total_sales=float(row['Total_Sales'])
                )

            messages.success(request, 'Excel file uploaded successfully!')
            return redirect('upload_sales_excel')

        except Exception as e:
            messages.error(request, f'Error: {str(e)}')

    return render(request, 'upload_excel.html')

from .models import DimCustomer
def customer_clustering(request):
    sales = FactSales.objects.select_related('customer')

    customer_data = {}
    customers = DimCustomer.objects.all()
    customer_names = [c.customer_name for c in customers]

    customers_data = (
    FactSales.objects
    .values('customer__customer_name')
    .annotate(
        total_spent=Sum('total_sales'),
        transactions=Count('id')
    )
)
    for sale in sales:
        cust = sale.customer.id

        if cust not in customer_data:
            customer_data[cust] = {
                'total_spent': 0,
                'transactions': 0
            }

        customer_data[cust]['total_spent'] += float(sale.total_sales)
        customer_data[cust]['transactions'] += 1

    data = [
        [float(row['total_spent']), int(row['transactions'])]
        for row in customers_data
    ]
    customer_ids = []
    
    for cust_id, values in customer_data.items():
        data.append([values['total_spent'], values['transactions']])
        customer_ids.append(cust_id)

    # KMeans
    kmeans = KMeans(n_clusters=3, random_state=42)
    clusters = kmeans.fit_predict(data)

    centers = kmeans.cluster_centers_
    sorted_clusters = sorted(range(len(centers)), key=lambda i: centers[i][0])

    cluster_labels = {
        sorted_clusters[0]: 'Low Value',
        sorted_clusters[1]: 'Medium Value',
        sorted_clusters[2]: 'High Value',
    }

    # 🔥 NEW: Prepare chart datasets
    chart_clusters = {
        'Low Value': [],
        'Medium Value': [],
        'High Value': []
    }

    results = []
    customer_names = customer_ids
    for i, row in enumerate(customers_data):
        label = cluster_labels[clusters[i]]

        point = {
            'x': data[i][0],  # total_spent
            'y': data[i][1]   # transactions
        }

        chart_clusters[label].append(point)

        results.append({
            'customer_name': row['customer__customer_name'].replace('Customer ', '').strip(),
            'total_spent': float(row['total_spent']),   # ✅ FIX
            'transactions': int(row['transactions']),   # optional but good
            'cluster': label
        })

    context = {
        'results': results,
        'low_cluster': json.dumps(chart_clusters['Low Value']),
        'medium_cluster': json.dumps(chart_clusters['Medium Value']),
        'high_cluster': json.dumps(chart_clusters['High Value']),
    }

    return render(request, 'clustering.html', {
    'results': results,
    'chart_data': json.dumps(results)
})
def sales_forecasting(request):

    # =========================
    # GET MONTHLY SALES
    # =========================

    monthly_data = (
        FactSales.objects
        .values('time__month', 'time__month_name', 'time__year')
        .annotate(total_revenue=Sum('total_sales'))
        .order_by('time__year', 'time__month')
    )

    months = []
    revenues = []
    labels = []

    counter = 1

    for item in monthly_data:
        months.append([counter])
        revenues.append(float(item['total_revenue']))

        labels.append(
            f"{item['time__month_name']} {item['time__year']}"
        )

        counter += 1

    # =========================
    # MACHINE LEARNING
    # LINEAR REGRESSION
    # =========================

    predicted_sales = None

    if len(months) > 1:

        X = np.array(months)
        y = np.array(revenues)

        model = LinearRegression()
        model.fit(X, y)

        next_month = [[len(months) + 1]]

        predicted_sales = model.predict(next_month)[0]


    context = {
        'labels': json.dumps(labels),
        'revenues': json.dumps(revenues),
        'predicted_sales': predicted_sales,
        'monthly_sales': zip(labels, revenues),
    }

    return render(request, 'sales_forecasting.html', context)

