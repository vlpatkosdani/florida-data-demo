# Demo runbook: D2, D3, D4

Rehearsed end to end on 17 Nov 2026 with ms-fabric-cli 1.9.0 and fabric-cicd 1.4.0.

## Before the session (5 minutes)

All commands are for **cmd** and use full paths, so they work from any folder.
Use the project venv's fab (1.9.0). The global `fab` on this laptop is 0.1.10 and shares the same
login files, which causes random "Failed to get access token" errors.

```bat
set REPO=C:\Users\local_user\Desktop\florida-data-demo
set FAB="%REPO%\.venv\Scripts\fab.exe"
set PY="%REPO%\.venv\Scripts\python.exe"

%FAB% --version
:: must say 1.9.0
%FAB% auth status
:: must say Logged In: True (your account or the app registration)
%FAB% exists "_Florida-Engineering-Demo.Workspace"
:: must say False; if True: %FAB% rm "_Florida-Engineering-Demo.Workspace" -f
```

If fab says `Failed to get access token` and logout + login doesn't fix it: run `%FAB% auth logout`,
delete `%USERPROFILE%\.config\fab\auth.json` and `cache.bin`, then log in again.

## D2: Deployment pipeline (clicks, about 90 seconds)

Pipeline **Florida Engineering - Clicks**: DEV = _Florida-Engineering-DEV, TEST = _Florida-Engineering-TEST.

One-time setup, in the Fabric UI (rules can't be created through the API):
1. Open the pipeline, select the **TEST** stage, then **nb_transform_sales** → **Deployment rules**.
2. **Default lakehouse rule** → Add rule → From: the current lakehouse (Store_LH in _Florida-Store-PPE)
   → To: **Other**, then enter:
   - Lakehouse ID: `d8bbe04d-ba36-4e93-ba31-16bae9b49c59`
   - Lakehouse name: `Store_LH`
   - Workspace ID: `4ae140d4-724f-4009-b148-0072e0237c78` (_Florida-Store-TEST)

   Save. The rule applies from the next deploy, so do one DEV → TEST deploy after creating it.

TEST's vl_settings already has the **TEST** value set active (set once per stage; a deploy keeps it).

On stage:
1. In _Florida-Engineering-DEV, open nb_transform_sales and make a visible change
   (e.g. add Margin % at the `# DEMO` marker). Save.
2. Pipeline → DEV → **Compare** with TEST: nb_transform_sales shows as *Different*. Open the change review.
3. **Deploy** to TEST, add a note.
4. Open nb_transform_sales in TEST: the default lakehouse is Store_LH in **_Florida-Store-TEST** (the rule),
   while DEV still points at _Florida-Store-PPE.
5. Show **Deployment history**.

Talking points: rule coverage varies by item type; rules are UI-only; one pipeline per workspace set;
history is the only audit trail. Variable library value sets are the shared bridge with fabric-cicd.

Reset after rehearsal: in DEV, undo the change and deploy again (or redeploy DEV from the repo with
`python automation\scripts\deploy.py --environment DEV --layers engineering`).

## D3 + D4: fab CLI and fabric-cicd (code)

Run in the same cmd window as the pre-session block (it sets `REPO`, `FAB`, `PY`).

```bat
:: 1. Browse, create a workspace on a capacity (fab mkdir requires a capacity)
%FAB% ls
%FAB% mkdir "_Florida-Engineering-Demo.Workspace" -P capacityName=Trial-20261110T093500Z-vhNIN2bjwEuglRS2Upik6Q
%FAB% get "_Florida-Engineering-Demo.Workspace" -q capacityId
:: only when fab runs as the app registration: give yourself access so you can open it in Fabric
%FAB% acl set "_Florida-Engineering-Demo.Workspace" -I caff5106-0728-4c5a-b1fe-1904c514071b -R Admin -f

:: 2. Show the configuration
code "%REPO%\solution\engineering\config.yml" "%REPO%\solution\engineering\parameter.yml"

:: 3. Deploy with Python
%PY% "%REPO%\automation\scripts\deploy.py" --environment DEMO --layers engineering

:: Show the replaced ID: Git has PPE storage...
findstr /n "default_lakehouse" "%REPO%\solution\engineering\nb_transform_sales.Notebook\notebook-content.py"
:: ...the deployed notebook has TEST storage
%FAB% export "_Florida-Engineering-Demo.Workspace/nb_transform_sales.Notebook" -o "%TEMP%\demo" --format .py -f
findstr /n "default_lakehouse" "%TEMP%\demo\nb_transform_sales.Notebook\notebook-content.py"
```

Expected: Git shows lakehouse `4d9757c7-…` / workspace `b64d3ac2-…` (_Florida-Store-PPE); the deployed
notebook shows `d8bbe04d-…` / `4ae140d4-…` (_Florida-Store-TEST). Same file, different environment, no
manual edits. In Fabric: nb_transform_sales → Lakehouse pane shows the same; vl_settings active value
set is **DEMO**.

Scope beat: the folder has 6 items, the workspace now has 4. `zz_scratch` is excluded by `config.yml`
(`publish.exclude_regex: "^zz_"`); `nb_fab_only` is excluded by deploy.py's own rule (`PYTHON_ONLY_EXCLUDE`).

```bat
%FAB% ls "_Florida-Engineering-Demo.Workspace"
:: 3 notebooks + vl_settings

:: 4. Same deployment without Python
%FAB% deploy --config "%REPO%\solution\engineering\config.yml" --target_env DEMO -f
%FAB% ls "_Florida-Engineering-Demo.Workspace"
:: nb_fab_only appeared (fab reads only config.yml); zz_scratch is still missing (config excludes it for every tool)

:: 5. Clean up
%FAB% rm "_Florida-Engineering-Demo.Workspace" -f
```

Notes:
- `deploy.py` finds its configs from its own location, and `fab deploy` resolves item folders relative
  to the config file. That's why full paths work from any folder.
- `deploy.py` uses the app registration only if `SPN_CLIENT_SECRET` is set in this window, otherwise
  your `az login`. `fab deploy` uses fab's login.
- Expected runtimes: steps 3 and 4 about 15 seconds each.

## D5: Feature workspaces + fabric-cicd release (both, about 12 minutes)

Rehearsed 17 Nov 2026 with a `feature/smoke-test` branch. The service principal may not use Git
integration in this tenant (tenant setting, can't be changed), so Git connect is one command you run
yourself. Say it out loud: it's a real-world gotcha.

```powershell
# 1. Branch from ppe and push: GitHub Actions 'feature-create' starts (~1 min)
git switch ppe; git pull
git switch -c feature/avg-order-value
git push -u origin feature/avg-order-value
```

2. While it runs, narrate `automation/resources/environments/feature.json` (naming, capacity, layers,
   Spark limits, ACLs). The run summary shows the next command.
3. Fabric: `*feature-avg-order-value-Engineering` and `-Serve` appear at the top of the list.

```powershell
# 4. Connect both workspaces to their Git folders on the feature branch and sync (~20 s, your login)
python automation\scripts\fabric_feature_maintenance.py connect --branch feature/avg-order-value
```

5. In `*feature-avg-order-value-Serve`, open SM_Sales and add
   `Avg Order Value = DIVIDE ( [Sales Amount], [# Orders] )`. Source control → Compare → Commit.
   (Optional, Engineering: add Margin % in nb_transform_sales at the `# DEMO` marker.)
6. VS Code: `git pull`, show the same TMDL diff, open the PR into `ppe`.
7. Squash merge: `deploy-ppe` publishes with fabric-cicd and refreshes SM_Sales (Anonymous credentials
   set by deploy.py); `feature-cleanup` deletes the feature workspaces. Show both runs side by side.
8. Open RPT_Sales in `_Florida-Serve-PPE` with the new measure.
9. Promote to main: PR `ppe` → `main`, merge; `deploy-prod` waits for approval in the `prod`
   environment; approve live; PROD updates and refreshes with `data-10m-v1`.

Backup: pre-create the feature branch and run step 4 before the session.
