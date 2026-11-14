"""Create or delete per-layer feature workspaces for a feature branch.

Approach after Peer Gronnerup's "Automating Feature Workspace maintenance in
Microsoft Fabric", rebuilt for this demo on fab CLI 1.9.0.

Usage:
    python automation/scripts/fabric_feature_maintenance.py create --branch feature/margin-kpi
    python automation/scripts/fabric_feature_maintenance.py delete --branch feature/margin-kpi

create: workspace per layer -> marker description -> ACLs -> Spark limits ->
        Git connect to the layer folder on the feature branch -> sync from Git.
delete: removes a workspace only if its name matches the feature pattern AND its
        description carries the managed marker. Anything else is left alone.
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from modules import fabric_cli_functions as fab  # noqa: E402

RECIPE = Path(__file__).resolve().parents[1] / "resources" / "environments" / "feature.json"


def load_recipe():
    return json.loads(RECIPE.read_text(encoding="utf-8"))


def feature_name(branch, recipe):
    prefix = recipe["naming"]["feature_from_branch"].split("{feature}")[0]  # "feature/"
    if not branch.startswith(prefix):
        raise SystemExit(f"Branch '{branch}' does not start with '{prefix}'; nothing to do.")
    name = branch[len(prefix):]
    # Workspace-safe: letters, digits, dash
    return re.sub(r"[^A-Za-z0-9-]+", "-", name).strip("-")


def workspace_name(recipe, feature, layer):
    return recipe["naming"]["pattern"].format(feature=feature, layer=layer)


def create(branch):
    recipe = load_recipe()
    feature = feature_name(branch, recipe)
    marker = recipe["naming"]["managed_marker"]
    git = recipe["git"]

    for layer, cfg in recipe["layers"].items():
        ws = workspace_name(recipe, feature, layer)
        print(f"\n=== {ws}")

        if fab.workspace_exists(ws):
            ws_id, desc = fab.workspace_id(ws)
            if marker not in (desc or ""):
                raise SystemExit(f"{ws} exists but was not created by this automation. Stopping.")
            print("  exists (managed), reusing")
        else:
            fab.create_workspace(ws, recipe["capacity_name"])
            ws_id, _ = fab.workspace_id(ws)
            print(f"  created {ws_id}")

        fab.api(f"workspaces/{ws_id}", "patch", {"description": f"{marker} | branch: {branch}"})
        print("  marker set")

        for p in recipe.get("permissions", []):
            fab.set_acl(ws, p["identity_object_id"], p["role"])
            print(f"  acl {p['role']} -> {p.get('_who', p['identity_object_id'])}")

        if cfg.get("spark_settings"):
            fab.api(f"workspaces/{ws_id}/spark/settings", "patch", cfg["spark_settings"])
            print("  spark settings applied")

        conn = fab.api(f"workspaces/{ws_id}/git/connection")["text"]
        if conn.get("gitConnectionState") == "NotConnected":
            fab.api(f"workspaces/{ws_id}/git/connect", "post", {
                "gitProviderDetails": {
                    "gitProviderType": git["provider"],
                    "ownerName": git["owner"],
                    "repositoryName": git["repository"],
                    "branchName": branch,
                    "directoryName": cfg["git_directory"],
                },
                "myGitCredentials": {"source": "ConfiguredConnection", "connectionId": git["connection_id"]},
            })
            print(f"  git connected: {branch} {cfg['git_directory']}")
        else:
            print(f"  git already {conn.get('gitConnectionState')}")

        init = fab.api(f"workspaces/{ws_id}/git/initializeConnection", "post",
                       {"initializationStrategy": "PreferRemote"})["text"] or {}
        action = init.get("requiredAction", "None")
        print(f"  git init: requiredAction={action}")
        if action == "UpdateFromGit":
            resp = fab.api(f"workspaces/{ws_id}/git/updateFromGit", "post", {
                "remoteCommitHash": init["remoteCommitHash"],
                "workspaceHead": init.get("workspaceHead"),
                "conflictResolution": {"conflictResolutionType": "Workspace",
                                       "conflictResolutionPolicy": "PreferRemote"},
                "options": {"allowOverrideItems": True},
            }, show_headers=True)
            fab.wait_for_operation(resp)
            print("  synced from Git")
    print("\nFeature workspaces ready.")


def delete(branch):
    recipe = load_recipe()
    feature = feature_name(branch, recipe)
    marker = recipe["naming"]["managed_marker"]
    for layer in recipe["layers"]:
        ws = workspace_name(recipe, feature, layer)
        print(f"\n=== {ws}")
        if not fab.workspace_exists(ws):
            print("  not found, skipping")
            continue
        ws_id, desc = fab.workspace_id(ws)
        if marker not in (desc or ""):
            print("  NOT managed by this automation (marker missing). Leaving it alone.")
            continue
        fab.delete_workspace(ws)
        print(f"  deleted {ws_id}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["create", "delete"])
    parser.add_argument("--branch", required=True)
    args = parser.parse_args()
    fab.login_from_env()
    {"create": create, "delete": delete}[args.action](args.branch)


if __name__ == "__main__":
    main()
