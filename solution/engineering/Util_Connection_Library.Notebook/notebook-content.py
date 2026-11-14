# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # Util_Connection_Library
# Shared helpers. Load with `%run Util_Connection_Library` from any notebook in this workspace.
#
# Every environment value comes from the **vl_settings** variable library, so the same notebook
# code runs in a feature workspace (default value set, reads PPE), in PPE and in PROD.
# fabric-cicd switches the active value set to match the target environment.

# CELL ********************

import notebookutils

ONELAKE = "onelake.dfs.fabric.microsoft.com"


def get_settings():
    """Return the vl_settings variable library of the current workspace."""
    return notebookutils.variableLibrary.getLibrary("vl_settings")


def store_root(settings=None):
    """abfss root of the Store lakehouse, e.g. abfss://<ws>@onelake.../Store_LH.Lakehouse"""
    s = settings or get_settings()
    return f"abfss://{s.store_workspace}@{ONELAKE}/{s.store_lakehouse}.Lakehouse"


def table_path(name, settings=None):
    return f"{store_root(settings)}/Tables/{name}"


def files_path(relative, settings=None):
    return f"{store_root(settings)}/Files/{relative.lstrip('/')}"


def write_table(df, name, mode="overwrite"):
    """Write a Delta table into Store_LH (lakehouse without schemas)."""
    (df.write.format("delta")
       .mode(mode)
       .option("overwriteSchema", "true")
       .save(table_path(name)))
    print(f"wrote {name} -> {table_path(name)}")


def read_table(name):
    return spark.read.format("delta").load(table_path(name))

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
