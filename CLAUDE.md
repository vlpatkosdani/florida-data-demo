# CLAUDE.md

Demo repo for the session "Clicks or Code: No-Code and Pro-Code CI/CD in Microsoft Fabric".
Flow: Microsoft's "Optimizing for CI/CD in Microsoft Fabric" branching model + Peer Gronnerup's
feature workspace automation (rebuilt with credit, not copied).

## Rules
- Never delete a workspace this repo did not create. Feature workspaces carry the marker in
  `automation/resources/environments/feature.json` (`naming.managed_marker`); check name pattern AND marker.
- Never print secrets. SPN credentials come only from env vars / GitHub environment secrets.
- Versions are pinned in `requirements.txt`. Check every `fab` flag with `fab <cmd> --help` against the pinned version.
- Fabric authors SM_Sales (semantic model), RPT_Sales (report) and dp_daily (data pipeline) in the UI and
  commits them via Git integration. Claude writes everything else.
- Show tenant-changing commands (create/delete workspace, ACL, git connect) before running them.

## Layout
- `solution/<layer>/` = one Git-integration folder per layer (store, engineering, serve), each with
  `config.yml` + `parameter.yml` for fabric-cicd.
- `automation/` = feature workspace recipe and scripts. `.github/workflows/` = CI/CD.

## Facts verified against pinned versions (fab 1.9.0, fabric-cicd 1.4.0)
- `fab deploy --config <file> --target_env <ENV>` exists.
- fabric-cicd resolves `repository_directory` and `parameter` relative to the config file.
- Cross-workspace dynamic values: `$workspace.<ws name>.$items.<Type>.<name>.$id|$sqlendpoint|$sqlendpointid`.
  The lakehouse is in Florida-Store-*, so Engineering/Serve parameters must use this form.
- VariableLibrary: fabric-cicd activates the value set whose name equals the environment, so value sets are named `PPE` and `PROD`.
- Notebook `.py` source: write `%run <notebook>` as a plain line. `# MAGIC %run ...` gets mangled on import
  (line doubled without newline) and the Spark session dies with System_Cancelled_Session_Statements_Failed.
- `fab import` of a `.py` notebook needs `--format .py`.
- OneLake name-based paths work: `abfss://Florida-Store-PPE@onelake.dfs.fabric.microsoft.com/Store_LH.Lakehouse/...`.
- PPE unpublish is on: anything in an Engineering/Serve PPE workspace that isn't in the repo gets deleted on deploy.

## Environment (no secrets here; the SPN secret lives only in GitHub environment secrets / local env vars)
- Tenant: a5ff2eab-e6e7-498b-887b-05a86e1c7a97. Capacity: Trial-20261110T093500Z-vhNIN2bjwEuglRS2Upik6Q (FTL64, West Europe).
- Deployment identity: app reg `ar-powerbi-fabric-cli-demo`, client ID 4096ba33-cc46-4821-8d5e-1083c78ac750,
  SP object ID 54c86e5d-afa1-4bca-979b-69334407b7fd. Admin on all Florida-* workspaces.
- GitHub source control connection: `florida-demo` 3bbb2c6a-44b9-41df-ab66-b11fe7231a7d.

| Workspace | ID | Role |
|---|---|---|
| Florida Data & AI - Demo | 5e42287f-8c52-4a64-b51f-117e0a6dfdd9 | DEV for clicks demos (D1/D2); Git: main, /solution/serve |
| Florida-Store-PPE | b64d3ac2-7a25-4b7a-80ee-7dabc987cac9 | fabric-cicd target |
| Florida-Store-PROD | 64cf5501-eb3d-4ead-bc83-4b223d81b91a | fabric-cicd target |
| Florida-Engineering-PPE | 3af681c9-0c95-4d8c-b35f-decad1771f86 | fabric-cicd target |
| Florida-Engineering-PROD | 022a840e-659e-4ea7-a281-862d1db20bd9 | fabric-cicd target |
| Florida-Serve-PPE | 4ea93155-284e-40a3-bdcd-4094d5b4ef3d | fabric-cicd target |
| Florida-Serve-PROD | 69f556a5-bbb8-4d56-810e-47da45dccfb1 | fabric-cicd target |

These seven workspaces were created or approved for this repo. Any other workspace in the tenant is off limits.

## Demo data
Source for nb_ingest_sales: release assets of https://github.com/vlpatkosdani/semantic-model-refresh-test/releases (any release is fine).

## Stage status
1. Scaffold: done. 2. Auth check: done. 3. Workspaces: done.
4. Store_LH, vl_settings, notebooks deployed to PPE and run (tables: sales_raw, dim_*, fact_sales). PROD not deployed yet.
   Waiting on Daniel: SM_Sales + RPT_Sales authored in Fabric, dp_daily pipeline.
5. Workflows: next. 6. reset_demo.py.
