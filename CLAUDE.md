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
  The lakehouse is in Sales-Store-*, so Engineering/Serve parameters must use this form.
- VariableLibrary: fabric-cicd activates the value set whose name equals the environment, so value sets are named `PPE` and `PROD`.

## Stage status
1. Scaffold: done (WIP). 2. Auth check. 3. Workspaces. 4. Notebooks + variable library. 5. Workflows. 6. reset_demo.py.
