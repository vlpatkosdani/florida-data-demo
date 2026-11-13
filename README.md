# Clicks or Code: Fabric CI/CD demo (WIP)

One Sales solution, three layers, promoted with clicks (Git integration, deployment pipelines)
and with code (fab CLI, fabric-cicd).

> Work in progress. Workflows, scripts, notebooks and the variable library are not here yet.

## Layout

```
solution/
  store/        Store_LH lakehouse                     -> Florida-Store-PPE / -PROD
  engineering/  notebooks, variable library, pipeline  -> Florida-Engineering-PPE / -PROD
  serve/        SM_Sales, RPT_Sales                    -> Florida-Serve-PPE / -PROD
automation/
  resources/environments/feature.json   feature workspace recipe
  scripts/                              deploy + feature maintenance (coming)
.github/workflows/                      feature-create, feature-cleanup, deploy-ppe, deploy-prod (coming)
```

## Local setup

```
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
az login
fab auth login --azure-cli
```

## Deploy one layer

```
fab deploy --config solution/engineering/config.yml --target_env PPE
```

## Credits
- Microsoft Fabric blog: "Optimizing for CI/CD in Microsoft Fabric"
- Peer Gronnerup: "Automating Feature Workspace maintenance in Microsoft Fabric"
- Daniel Patkos & Kevin Chant: "Deploy Smarter: Enterprise CI/CD in Microsoft Fabric using Fabric CLI and fabric-cicd"
