# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # nb_ingest_sales
# Downloads one release of the Contoso demo data and lands it in Store_LH:
# raw parquet in `Files/raw/<release>/`, then Delta tables `sales_raw` and `dim_*`.

# CELL ********************

%run Util_Connection_Library

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

import os
import urllib.request

settings = get_settings()
release = settings.source_release
base_url = settings.source_base_url

# file name -> target table
FILES = {
    "sales": "sales_raw",
    "product": "dim_product",
    "store": "dim_store",
    "date": "dim_date",
    "customer": "dim_customer",
}

local_dir = f"/tmp/{release}"
os.makedirs(local_dir, exist_ok=True)

for name in FILES:
    url = f"{base_url}/{release}/{name}.parquet"
    local = f"{local_dir}/{name}.parquet"
    urllib.request.urlretrieve(url, local)
    target = files_path(f"raw/{release}/{name}.parquet")
    notebookutils.fs.cp(f"file:{local}", target)
    print(f"{url} -> {target}")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }

# CELL ********************

for name, table in FILES.items():
    df = spark.read.parquet(files_path(f"raw/{release}/{name}.parquet"))
    write_table(df, table)

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
