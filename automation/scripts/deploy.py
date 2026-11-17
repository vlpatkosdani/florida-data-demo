"""Deploy solution layers with fabric-cicd.

Usage:
    python automation/scripts/deploy.py --environment PPE
    python automation/scripts/deploy.py --environment PROD --layers engineering serve

Auth: if SPN_CLIENT_SECRET is set (GitHub Actions), uses the service principal from
SPN_TENANT_ID / SPN_CLIENT_ID / SPN_CLIENT_SECRET. Otherwise uses the local `az login`.

After the serve layer, every semantic model with a Web data source gets Anonymous
credentials and a refresh (fabric-cicd deploys definitions, not credentials).
Skip with --no-refresh.
"""

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import yaml

from azure.identity import AzureCliCredential, ClientSecretCredential
from fabric_cicd import change_log_level, deploy_with_config

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYERS = ["store", "engineering", "serve"]  # deployment order: storage first, reports last

# Items this script skips on top of config.yml's publish.exclude_regex.
# `fab deploy` reads only config.yml, so it still deploys them (scope demo: nb_fab_only).
PYTHON_ONLY_EXCLUDE = r"^nb_fab_only$"


def exclude_override(config, environment):
    """config_override that adds PYTHON_ONLY_EXCLUDE to the config's own exclude_regex."""
    cfg = yaml.safe_load(config.read_text(encoding="utf-8")) or {}
    existing = (cfg.get("publish") or {}).get("exclude_regex")
    if isinstance(existing, dict):  # per-environment form
        existing = existing.get(environment)
    pattern = f"(?:{existing})|(?:{PYTHON_ONLY_EXCLUDE})" if existing else PYTHON_ONLY_EXCLUDE
    return {"publish": {"exclude_regex": pattern}}


def get_credential():
    secret = os.environ.get("SPN_CLIENT_SECRET")
    if secret:
        print("Auth: service principal")
        return ClientSecretCredential(
            tenant_id=os.environ["SPN_TENANT_ID"],
            client_id=os.environ["SPN_CLIENT_ID"],
            client_secret=secret,
        )
    print("Auth: Azure CLI")
    return AzureCliCredential()


def _call(token, method, url, body=None):
    req = urllib.request.Request(url, method=method,
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as r:
            raw = r.read()
            return r.status, (json.loads(raw) if raw else {})
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(errors="replace")[:300]


def configure_semantic_models(config, environment, credential):
    """Set Anonymous credentials on Web sources and start a refresh for each semantic model."""
    ws_name = yaml.safe_load(config.read_text(encoding="utf-8"))["core"]["workspace"][environment]
    fabric = credential.get_token("https://api.fabric.microsoft.com/.default").token
    pbi = credential.get_token("https://analysis.windows.net/powerbi/api/.default").token
    _, data = _call(fabric, "GET", "https://api.fabric.microsoft.com/v1/workspaces")
    ws_id = next(w["id"] for w in data["value"] if w["displayName"] == ws_name)
    _, items = _call(fabric, "GET", f"https://api.fabric.microsoft.com/v1/workspaces/{ws_id}/items?type=SemanticModel")
    base = f"https://api.powerbi.com/v1.0/myorg/groups/{ws_id}/datasets"
    for model in items.get("value", []):
        name, mid = model["displayName"], model["id"]
        _, sources = _call(pbi, "GET", f"{base}/{mid}/datasources")
        for src in sources.get("value", []) if isinstance(sources, dict) else []:
            if src.get("datasourceType") != "Web":
                continue
            st, err = _call(pbi, "PATCH",
                            f"https://api.powerbi.com/v1.0/myorg/gateways/{src['gatewayId']}/datasources/{src['datasourceId']}",
                            {"credentialDetails": {"credentialType": "Anonymous",
                                                   "credentials": json.dumps({"credentialData": ""}),
                                                   "encryptedConnection": "Encrypted",
                                                   "encryptionAlgorithm": "None", "privacyLevel": "Public"}})
            print(f"  {name}: Web credentials -> Anonymous ({st})" + (f" {err}" if st >= 400 else ""))
        st, err = _call(pbi, "POST", f"{base}/{mid}/refreshes", {"notifyOption": "NoNotification"})
        print(f"  {name}: refresh requested ({st})" + (f" {err}" if st >= 400 else ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True, choices=["PPE", "PROD", "DEV", "TEST", "DEMO"])
    parser.add_argument("--layers", nargs="+", choices=LAYERS, default=LAYERS)
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--no-refresh", action="store_true", help="skip credentials + refresh after serve")
    args = parser.parse_args()

    if args.debug:
        change_log_level("DEBUG")

    credential = get_credential()
    for layer in [l for l in LAYERS if l in args.layers]:
        config = REPO_ROOT / "solution" / layer / "config.yml"
        if f"    {args.environment}:" not in config.read_text(encoding="utf-8"):
            print(f"\n=== {layer}: no {args.environment} workspace in config, skipping")
            continue
        print(f"\n=== {layer} -> {args.environment}")
        deploy_with_config(
            config_file_path=str(config),
            environment=args.environment,
            token_credential=credential,
            config_override=exclude_override(config, args.environment),
        )
        if layer == "serve" and not args.no_refresh:
            print(f"\n=== serve -> {args.environment}: credentials + refresh")
            configure_semantic_models(config, args.environment, credential)
    return 0


if __name__ == "__main__":
    sys.exit(main())
