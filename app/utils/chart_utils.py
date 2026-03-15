from datetime import timedelta

def format_sales_for_chart(sales_data, start_date, n_days=28):
    """Returns labels and values for chart.js line chart."""
    sales_dict = {d: s or 0 for d, s in sales_data}
    day_labels = [(start_date + timedelta(days=i)).strftime("%d %b") for i in range(n_days)]
    sales_values = [sales_dict.get(start_date + timedelta(days=i), 0) for i in range(n_days)]
    total_sales = sum(sales_values)
    return day_labels, sales_values, total_sales