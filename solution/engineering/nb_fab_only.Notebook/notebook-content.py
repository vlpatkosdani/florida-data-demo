# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # nb_fab_only
# Scope demo. `fab deploy` publishes this notebook because config.yml allows it.
# `deploy.py` skips it: it adds its own exclude rule (PYTHON_ONLY_EXCLUDE) on top of config.yml.
# So it never reaches PPE or PROD (GitHub Actions use deploy.py).

# CELL ********************

print("nb_fab_only: deployed by fab deploy, skipped by deploy.py")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
