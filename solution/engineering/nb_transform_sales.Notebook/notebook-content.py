# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # nb_transform_sales
# Builds `fact_sales` from `sales_raw`: one row per order line, amounts in USD.

# CELL ********************

%run Util_Connection_Library

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

from pyspark.sql import functions as F

sales = read_table("sales_raw")

fact_sales = (
    sales
    .withColumn("OrderDateKey", F.to_date("OrderDate"))
    .withColumn("SalesAmount", F.round(F.col("Quantity") * F.col("NetPrice") * F.col("ExchangeRate"), 2))
    .withColumn("CostAmount", F.round(F.col("Quantity") * F.col("UnitCost") * F.col("ExchangeRate"), 2))
    .withColumn("MarginAmount", F.col("SalesAmount") - F.col("CostAmount"))
    # DEMO: add Margin % here (feature/margin-kpi)
    .select(
        "OrderKey", "LineNumber", "OrderDateKey", "CustomerKey", "StoreKey", "ProductKey",
        "Quantity", "SalesAmount", "CostAmount", "MarginAmount",
    )
)

write_table(fact_sales, "fact_sales")
display(fact_sales.limit(10))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
