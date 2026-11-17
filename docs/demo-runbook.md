# Demo runbook: D2, D3, D4

Rehearsed end to end on 17 Nov 2026 with ms-fabric-cli 1.9.0 and fabric-cicd 1.4.0.

## Before the session (5 minutes)

```powershell
cd C:\Users\local_user\Desktop\florida-data-demo
.\.venv\Scripts\Activate.ps1
az login
fab auth logout
fab auth login --azure-cli
fab auth status        # must say: Logged In: True, your account
fab exists "Florida-Engineering-Demo.Workspace"   # must be False; if True: fab rm ... -f
```

If fab ever says `AuthenticationFailed ... Something went wrong while trying to acquire a token`
and `fab auth logout` + login does not fix it, delete `~\.config\fab\auth.json` and log in again.

## D2: Deployment pipeline (clicks, about 90 seconds)

Pipeline **Florida Engineering - Clicks**: DEV = Florida-Engineering-DEV, TEST = Florida-Engineering-TEST.

One-time setup, in the Fabric UI (rules can't be created through the API):
1. Open the pipeline, select the **TEST** stage, then **nb_transform_sales** → **Deployment rules**.
2. **Default lakehouse rule** → Add rule → From: the current lakehouse (Store_LH in Florida-Store-PPE)
   → To: **Other**, then enter:
   - Lakehouse ID: `d8bbe04d-ba36-4e93-ba31-16bae9b49c59`
   - Lakehouse name: `Store_LH`
   - Workspace ID: `4ae140d4-724f-4009-b148-0072e0237c78` (Florida-Store-TEST)

   Save. The rule applies from the next deploy, so do one DEV → TEST deploy after creating it.

TEST's vl_settings already has the **TEST** value set active (set once per stage; a deploy keeps it).

On stage:
1. In Florida-Engineering-DEV, open nb_transform_sales and make a visible change
   (e.g. add Margin % at the `# DEMO` marker). Save.
2. Pipeline → DEV → **Compare** with TEST: nb_transform_sales shows as *Different*. Open the change review.
3. **Deploy** to TEST, add a note.
4. Open nb_transform_sales in TEST: the default lakehouse is Store_LH in **Florida-Store-TEST** (the rule),
   while DEV still points at Florida-Store-PPE.
5. Show **Deployment history**.

Talking points: rule coverage varies by item type; rules are UI-only; one pipeline per workspace set;
history is the only audit trail. Variable library value sets are the shared bridge with fabric-cicd.

Reset after rehearsal: in DEV, undo the change and deploy again (or redeploy DEV from the repo with
`python automation\scripts\deploy.py --environment DEV --layers engineering`).

## D3 + D4: fab CLI and fabric-cicd (code)

```powershell
# 1. Browse, create a workspace on a capacity (fab mkdir requires a capacity)
fab ls
fab mkdir "Florida-Engineering-Demo.Workspace" -P capacityName=Trial-20261110T093500Z-vhNIN2bjwEuglRS2Upik6Q
fab get "Florida-Engineering-Demo.Workspace" -q capacityId

# 2. Show the configuration
code solution\engineering\config.yml solution\engineering\parameter.yml

# 3. Deploy with Python
python automation\scripts\deploy.py --environment DEMO --layers engineering
```

Show the replaced ID: in the repo, `nb_transform_sales` points at Store_LH in **Florida-Store-PPE**
(`4d9757c7-…`). In Florida-Engineering-Demo, open nb_transform_sales → Lakehouse pane: it now points at
Store_LH in **Florida-Store-TEST** (`d8bbe04d-…`). Same file, different environment, no manual edits.
Also open vl_settings: active value set is **DEMO**.

```powershell
# 4. Same deployment without Python
fab deploy --config solution/engineering/config.yml --target_env DEMO -f

# 5. Clean up
fab rm "Florida-Engineering-Demo.Workspace" -f
```

Expected runtimes: steps 3 and 4 about 15 seconds each.
