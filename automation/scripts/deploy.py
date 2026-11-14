"""Deploy solution layers with fabric-cicd.

Usage:
    python automation/scripts/deploy.py --environment PPE
    python automation/scripts/deploy.py --environment PROD --layers engineering serve

Auth: if SPN_CLIENT_SECRET is set (GitHub Actions), uses the service principal from
SPN_TENANT_ID / SPN_CLIENT_ID / SPN_CLIENT_SECRET. Otherwise uses the local `az login`.
"""

import argparse
import os
import sys
from pathlib import Path

from azure.identity import AzureCliCredential, ClientSecretCredential
from fabric_cicd import change_log_level, deploy_with_config

REPO_ROOT = Path(__file__).resolve().parents[2]
LAYERS = ["store", "engineering", "serve"]  # deployment order: storage first, reports last


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


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--environment", required=True, choices=["PPE", "PROD"])
    parser.add_argument("--layers", nargs="+", choices=LAYERS, default=LAYERS)
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    if args.debug:
        change_log_level("DEBUG")

    credential = get_credential()
    for layer in [l for l in LAYERS if l in args.layers]:
        config = REPO_ROOT / "solution" / layer / "config.yml"
        print(f"\n=== {layer} -> {args.environment}")
        deploy_with_config(
            config_file_path=str(config),
            environment=args.environment,
            token_credential=credential,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
