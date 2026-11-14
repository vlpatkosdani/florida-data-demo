"""Thin wrappers around the fab CLI (ms-fabric-cli 1.9.0).

Every call goes through `fab` so the same commands work on a laptop and in
GitHub Actions. Flags were checked with `fab <command> --help` on 1.9.0.
"""

import json
import os
import shutil
import subprocess
import tempfile
import time

FAB = shutil.which("fab") or "fab"


class FabError(RuntimeError):
    pass


def run(args, check=True):
    """Run a fab command with JSON output and return the parsed `result`."""
    cmd = [FAB, *args, "--output_format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8")
    out = proc.stdout.strip()
    try:
        payload = json.loads(out) if out else {}
    except json.JSONDecodeError:
        payload = {"raw": out}
    if check and (proc.returncode != 0 or payload.get("status") == "Failure"):
        raise FabError(f"fab {' '.join(args[:3])} failed: {out or proc.stderr.strip()}")
    return payload.get("result", payload)


def login_from_env():
    """Log in as the service principal when SPN_* env vars are present (CI)."""
    secret = os.environ.get("SPN_CLIENT_SECRET")
    if not secret:
        print("fab: using existing login")
        return
    # GitHub runners have no OS keyring; let fab fall back to file encryption.
    subprocess.run([FAB, "config", "set", "encryption_fallback_enabled", "true"], check=True,
                   capture_output=True)
    proc = subprocess.run(
        [FAB, "auth", "login", "-u", os.environ["SPN_CLIENT_ID"], "-p", secret,
         "--tenant", os.environ["SPN_TENANT_ID"]],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        raise FabError("fab auth login failed (output hidden to protect secrets)")
    print("fab: logged in as service principal")


# ---------- workspaces ----------

def workspace_exists(name):
    data = run(["exists", f"{name}.Workspace"])
    return "true" in json.dumps(data).lower()


def create_workspace(name, capacity_name):
    run(["mkdir", f"{name}.Workspace", "-P", f"capacityName={capacity_name}"])


def delete_workspace(name):
    run(["rm", f"{name}.Workspace", "-f"])


def set_acl(name, object_id, role):
    run(["acl", "set", f"{name}.Workspace", "-I", object_id, "-R", role, "-f"])


# ---------- REST via fab api ----------

def api(endpoint, method="get", body=None, show_headers=False):
    """Call the Fabric REST API through `fab api`; returns {status_code, headers?, text}."""
    args = ["api", endpoint, "-X", method]
    tmp = None
    if body is not None:
        tmp = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
        json.dump(body, tmp)
        tmp.close()
        args += ["-i", tmp.name]
    if show_headers:
        args.append("--show_headers")
    try:
        result = run(args)
    finally:
        if tmp:
            os.unlink(tmp.name)
    data = result.get("data", [result])[0]
    code = data.get("status_code", 0)
    if code >= 400:
        raise FabError(f"{method.upper()} {endpoint} -> {code}: {data.get('text')}")
    return data


def wait_for_operation(response, timeout=600):
    """Poll a long-running operation started by a 202 response."""
    if response.get("status_code") != 202:
        return response
    headers = {k.lower(): v for k, v in (response.get("headers") or {}).items()}
    op_id = headers.get("x-ms-operation-id")
    if not op_id:
        raise FabError(f"202 without x-ms-operation-id: {headers}")
    deadline = time.time() + timeout
    while time.time() < deadline:
        time.sleep(int(headers.get("retry-after", 5)))
        state = api(f"operations/{op_id}")["text"]
        status = state.get("status")
        print(f"    operation {op_id}: {status}")
        if status == "Succeeded":
            return state
        if status in ("Failed", "Cancelled"):
            raise FabError(f"operation {op_id} {status}: {state.get('error')}")
    raise FabError(f"operation {op_id} timed out")


def workspace_id(name):
    matches = [w for w in api("workspaces")["text"]["value"] if w["displayName"] == name]
    if not matches:
        raise FabError(f"workspace {name} not found")
    return matches[0]["id"], matches[0].get("description", "")
