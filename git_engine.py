import subprocess
import os
import sys
import shutil
from pathlib import Path
from colorama import Fore, Style, init

init(autoreset=True)


# Git Detection
def is_git_repo(path):
    return (Path(path) / ".git").exists()


# Run Command
def run_git(args, cwd, capture=True):
    result = subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=capture,
        text=True
    )
    return result


# Git Init
def init_repo(path):
    print(Fore.CYAN + "[GIT INIT] Initializing repository...")
    result = run_git(["init"], cwd=path)
    if result.returncode == 0:
        print(Fore.GREEN + "  ✓ Repository initialized.")
        return True
    print(Fore.RED + f"  ✗ Init failed: {result.stderr}")
    return False


# Remote Check
def has_remote(path):
    result = run_git(["remote", "-v"], cwd=path)
    return bool(result.stdout.strip())


# Add Remote
def add_remote(path, remote_url):
    run_git(["remote", "remove", "origin"], cwd=path)
    result = run_git(["remote", "add", "origin", remote_url], cwd=path)
    if result.returncode == 0:
        print(Fore.GREEN + f"  ✓ Remote added: {remote_url}")
        return True
    print(Fore.RED + f"  ✗ Remote failed: {result.stderr}")
    return False


# Stage Files
def stage_all(path):
    print(Fore.CYAN + "[GIT ADD] Staging all files...")
    result = run_git(["add", "-A"], cwd=path)
    if result.returncode == 0:
        print(Fore.GREEN + "  ✓ Files staged.")
        return True
    print(Fore.RED + f"  ✗ Stage failed: {result.stderr}")
    return False


# Commit Changes
def commit(path, message):
    print(Fore.CYAN + f"[GIT COMMIT] Committing: '{message}'")
    result = run_git(["commit", "-m", message], cwd=path)
    if result.returncode == 0:
        print(Fore.GREEN + "  ✓ Commit successful.")
        return True
    if "nothing to commit" in result.stdout or "nothing to commit" in result.stderr:
        print(Fore.YELLOW + "  ⚠ Nothing to commit.")
        return "nothing"
    print(Fore.RED + f"  ✗ Commit failed: {result.stderr}")
    return False


# User Identity
def configure_identity(path, username, email):
    run_git(["config", "user.name", username], cwd=path)
    run_git(["config", "user.email", email], cwd=path)


# Branch Name
def get_current_branch(path):
    result = run_git(["branch", "--show-current"], cwd=path)
    return result.stdout.strip() or "main"


# Set Branch
def set_branch(path, branch_name="main"):
    current = get_current_branch(path)
    if current != branch_name:
        result = run_git(["branch", "-M", branch_name], cwd=path)
        if result.returncode == 0:
            print(Fore.GREEN + f"  ✓ Branch set to '{branch_name}'")
        else:
            print(Fore.YELLOW + f"  ⚠ Could not rename branch: {result.stderr}")


# Push Code
def push(path, branch="main", token=None, username=None, repo_url=None):
    print(Fore.CYAN + f"[GIT PUSH] Pushing to origin/{branch}...")

    if token and username and repo_url:
        from urllib.parse import urlparse
        parsed = urlparse(repo_url)
        auth_url = f"https://{username}:{token}@{parsed.netloc}{parsed.path}"
        run_git(["remote", "set-url", "origin", auth_url], cwd=path)

    result = run_git(["push", "-u", "origin", branch], cwd=path)
    if result.returncode == 0:
        print(Fore.GREEN + "  ✓ Push successful!")
        return True

    stderr = result.stderr + result.stdout

    if "rejected" in stderr and "fetch first" in stderr:
        print(Fore.YELLOW + "  ⚠ Remote has changes. Pulling first...")
        return "pull_needed"

    if "merge conflict" in stderr.lower() or "CONFLICT" in stderr:
        print(Fore.RED + "  ✗ Merge conflict detected.")
        return "conflict"

    print(Fore.RED + f"  ✗ Push failed: {stderr}")
    return False


# Pull Rebase
def pull_rebase(path, branch="main"):
    print(Fore.CYAN + "[GIT PULL] Pulling with rebase...")
    result = run_git(["pull", "--rebase", "origin", branch], cwd=path)
    if result.returncode == 0:
        print(Fore.GREEN + "  ✓ Pull successful.")
        return True

    if "CONFLICT" in result.stdout or "CONFLICT" in result.stderr:
        print(Fore.RED + "  ✗ Conflicts during pull.")
        return "conflict"

    print(Fore.RED + f"  ✗ Pull failed: {result.stderr}")
    return False


# Conflict Files
def get_conflict_files(path):
    result = run_git(["diff", "--name-only", "--diff-filter=U"], cwd=path)
    return [f.strip() for f in result.stdout.strip().splitlines() if f.strip()]


# Resolve Conflicts
def resolve_conflicts_ours(path):
    print(Fore.CYAN + "[CONFLICT RESOLVE] Using 'ours' strategy...")
    conflicts = get_conflict_files(path)
    if not conflicts:
        print(Fore.YELLOW + "  ⚠ No conflict files found via git diff.")
        return False

    for f in conflicts:
        full_path = Path(path) / f
        print(Fore.YELLOW + f"  Resolving: {f}")
        if full_path.exists():
            content = full_path.read_text(encoding="utf-8", errors="replace")
            resolved = _resolve_markers(content)
            full_path.write_text(resolved, encoding="utf-8")
            run_git(["add", str(f)], cwd=path)
            print(Fore.GREEN + f"    ✓ Resolved: {f}")

    return True


# Marker Resolution
def _resolve_markers(content):
    lines = content.splitlines(keepends=True)
    resolved = []
    in_ours = False
    in_theirs = False

    for line in lines:
        if line.startswith("<<<<<<<"):
            in_ours = True
            in_theirs = False
        elif line.startswith("=======") and in_ours:
            in_ours = False
            in_theirs = True
        elif line.startswith(">>>>>>>") and in_theirs:
            in_theirs = False
        elif in_ours:
            resolved.append(line)
        elif in_theirs:
            pass
        else:
            resolved.append(line)

    return "".join(resolved)


# Rebase Continue
def continue_rebase(path):
    env = os.environ.copy()
    env["GIT_EDITOR"] = "true"
    result = subprocess.run(
        ["git", "rebase", "--continue"],
        cwd=path,
        capture_output=True,
        text=True,
        env=env
    )
    return result.returncode == 0


# Abort Rebase
def abort_rebase(path):
    run_git(["rebase", "--abort"], cwd=path)
    print(Fore.YELLOW + "  ⚠ Rebase aborted. Force pushing...")
    result = run_git(["push", "-u", "--force-with-lease", "origin", get_current_branch(path)], cwd=path)
    return result.returncode == 0


# Check Status
def get_status(path):
    result = run_git(["status", "--short"], cwd=path)
    return result.stdout.strip()


# Log Recent
def get_log(path, n=3):
    result = run_git(["log", f"-{n}", "--oneline"], cwd=path)
    return result.stdout.strip()
