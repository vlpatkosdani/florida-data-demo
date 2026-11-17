# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {}
# META }

# MARKDOWN ********************

# # zz_scratch
# Scope demo. config.yml has publish.exclude_regex: "^zz_", which both tools read,
# so neither `fab deploy` nor `deploy.py` publishes this notebook.
# Git integration ignores config.yml, so it still appears in Git-synced feature workspaces.

# CELL ********************

print("zz_scratch: excluded by config.yml for every deployment tool")

# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
