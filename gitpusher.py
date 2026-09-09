import os
import sys
import time
import argparse
import requests
from pathlib import Path
from datetime import datetime

os.environ.setdefault("PYTHONUTF8", "1")

from colorama import Fore, Style, init, just_fix_windows_console
just_fix_windows_console()
init(autoreset=True)

import git_engine as git
import vision_engine as vision
import setup_credentials as creds

DEFAULT_BRANCH = "main"
MAX_RETRIES    = 4
GITHUB_API     = "https://api.github.com"

GITHUB_USERNAME = ""
GITHUB_TOKEN    = ""


# Banner Print
def print_banner():
    lines = [
        "",
        Fore.CYAN + "+======================================================+",
        Fore.CYAN + "|  " + Fore.WHITE + " _____ ___ _____   ____  _   _ ____  _   _ _____ " + Fore.CYAN + "  |",
        Fore.CYAN + "|  " + Fore.WHITE + "/ ____|_ _|_   _| |  _ | | | / ___|| | | | ____| " + Fore.CYAN + "  |",
        Fore.CYAN + "|  " + Fore.WHITE + "| |  _ | |  | |   | |_) | | | \\___|| |_| |  _| | " + Fore.CYAN + "  |",
        Fore.CYAN + "|  " + Fore.WHITE + "| |_| || |  | |   |  __/| |_| |___) |  _  | |___| " + Fore.CYAN + "  |",
        Fore.CYAN + "|  " + Fore.WHITE + " \\____|___| |_|   |_|    \\___/|____/ |_| |_|_____| " + Fore.CYAN + " |",
        Fore.CYAN + "|       " + Fore.YELLOW + "Automated Git Pusher  v2.0" + Fore.CYAN + "                       |",
        Fore.CYAN + "+======================================================+",
        "",
    ]
    print("\n".join(lines))


# Config Load
def load_config():
    global GITHUB_USERNAME, GITHUB_TOKEN
    username, token, tess_path = creds.load()
    GITHUB_USERNAME = username
    GITHUB_TOKEN    = token
    if tess_path:
        os.environ["TESSERACT_PATH"] = tess_path
    print(Fore.GREEN + f"  [OK] Signed in as: {Fore.WHITE}{GITHUB_USERNAME}")


# API Headers
def _headers():
    return {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }


# Repo Exists Check
def repo_exists(repo_name):
    url = f"{GITHUB_API}/repos/{GITHUB_USERNAME}/{repo_name}"
    r = requests.get(url, headers=_headers())
    if r.status_code == 401:
        print(Fore.RED + "\n  [!] Saved GitHub token was rejected by GitHub (401 Unauthorized).")
        creds.reset()
        load_config()
        return repo_exists(repo_name)
    if r.status_code == 200:
        data = r.json()
        return True, data["clone_url"], data["html_url"]
    return False, "", ""


# Create Repo
def create_repo(repo_name, description="", private=False):
    print(Fore.CYAN + f"[GITHUB API] Creating repo: {repo_name}...")
    payload = {"name": repo_name, "description": description, "private": private, "auto_init": False}
    r = requests.post(f"{GITHUB_API}/user/repos", json=payload, headers=_headers())

    if r.status_code == 401:
        print(Fore.RED + "\n  [!] Saved GitHub token was rejected by GitHub (401 Unauthorized).")
        creds.reset()
        load_config()
        return create_repo(repo_name, description, private)

    if r.status_code == 201:
        data = r.json()
        print(Fore.GREEN + f"  [OK] Repo created: {data['html_url']}")
        return data["clone_url"], data["html_url"]

    if r.status_code == 422:
        errors = r.json().get("errors", [])
        if any("already exists" in str(e) for e in errors):
            print(Fore.YELLOW + f"  [!] Repo '{repo_name}' already exists. Reusing.")
            clone = f"https://github.com/{GITHUB_USERNAME}/{repo_name}.git"
            html  = f"https://github.com/{GITHUB_USERNAME}/{repo_name}"
            return clone, html

    print(Fore.RED + f"  [FAIL] API error {r.status_code}: {r.text}")
    sys.exit(1)


# Phase Header
def phase(title):
    print(f"\n{Fore.MAGENTA}{'-'*55}")
    print(f"{Fore.MAGENTA}  PHASE: {Fore.WHITE}{title}")
    print(f"{Fore.MAGENTA}{'-'*55}")


# Repo Name Guess
def guess_repo_name(path):
    return Path(path).resolve().name.replace(" ", "-").lower()


# Email Guess
def guess_email():
    return f"{GITHUB_USERNAME}@users.noreply.github.com"


# GitHub Repo Phase
def phase_github_repo(repo_name, description, private):
    phase("GitHub Repo")
    exists, clone_url, html_url = repo_exists(repo_name)
    if exists:
        print(Fore.YELLOW + f"  [!] Already exists: {html_url}")
        return clone_url, html_url
    return create_repo(repo_name, description, private)


# Git Setup Phase
def phase_git_setup(repo_path, remote_url, branch, replace_remote=False):
    phase("Git Setup")

    if not git.is_git_repo(repo_path):
        if not git.init_repo(repo_path):
            sys.exit(1)
    else:
        print(Fore.GREEN + "  [OK] Already a git repo.")

    git.configure_identity(repo_path, GITHUB_USERNAME, guess_email())
    git.set_branch(repo_path, branch)
    if not git.add_remote(repo_path, remote_url, replace=replace_remote):
        print(Fore.RED + "  [FAIL] Remote setup was cancelled to protect the existing destination.")
        sys.exit(1)


# Commit Phase
def phase_commit(repo_path, commit_message):
    phase("Stage & Commit")

    status = git.get_status(repo_path)
    if not status:
        print(Fore.YELLOW + "  [!] Working tree clean. Nothing to commit.")
        return "nothing"

    print(Fore.CYAN + "  Changed files:")
    for line in status.splitlines():
        print(Fore.WHITE + f"    {line}")

    if not git.stage_all(repo_path):
        sys.exit(1)

    result = git.commit(repo_path, commit_message)
    if result == "nothing":
        return "nothing"
    if not result:
        sys.exit(1)
    return "committed"


# Conflict Resolution Phase
def phase_resolve_conflicts(repo_path):
    phase("Merge Conflict Resolution")
    print(Fore.YELLOW + "  Conflict detected. Resolving (keeping our changes)...")
    vision.save_snapshot("conflict_detected")

    resolved = git.resolve_conflicts_ours(repo_path)
    if resolved:
        ok = git.continue_rebase(repo_path)
        if ok:
            print(Fore.GREEN + "  [OK] Rebase continued after resolution.")
        else:
            print(Fore.YELLOW + "  -> Rebase continue failed. Aborting safely.")
            git.abort_rebase(repo_path)
    else:
        print(Fore.YELLOW + "  -> Aborting safely; resolve the conflict before trying again.")
        git.abort_rebase(repo_path)


# Push Phase with Retries
def phase_push(repo_path, branch, remote_url):
    phase("Push to GitHub")

    for attempt in range(1, MAX_RETRIES + 1):
        print(Fore.CYAN + f"  Attempt {attempt}/{MAX_RETRIES}...")
        result = git.push(repo_path, branch=branch, token=GITHUB_TOKEN,
                          username=GITHUB_USERNAME, repo_url=remote_url)

        if result is True:
            return True

        if result == "pull_needed":
            pull_result = git.pull_rebase(repo_path, branch)
            if pull_result == "conflict":
                phase_resolve_conflicts(repo_path)
            elif not pull_result:
                print(Fore.RED + "  [FAIL] Pull failed.")
                break
            continue

        if result == "conflict":
            phase_resolve_conflicts(repo_path)
            continue

        if result is False:
            print(Fore.RED + "  [FAIL] Push failed.")
            break

    print(Fore.RED + "[PUSH] All retries exhausted.")
    return False


# OCR Screen Monitor
def phase_ocr_monitor(repo_path):
    phase("OCR Screen Monitor")
    if not vision.is_tesseract_available():
        print(Fore.YELLOW + "  [SKIP] OCR engine is unavailable. The Git push was not affected.")
        print(Fore.YELLOW + "         Run push.bat again to retry its automatic installation.")
        return ""
    print(Fore.CYAN + "  Scanning screen for errors via OCR...")
    time.sleep(1.5)

    errors, text = vision.detect_terminal_error()
    if errors:
        print(Fore.YELLOW + f"  [!] OCR detected: {errors}")
        vision.save_snapshot("ocr_error_detected")
        if "conflict" in errors:
            phase_resolve_conflicts(repo_path)
        elif "denied" in errors or "rejected" in errors:
            print(Fore.RED + "  [FAIL] Access denied. Check your token.")
        elif "not found" in errors:
            print(Fore.RED + "  [FAIL] Remote not found. Check the URL.")
    else:
        print(Fore.GREEN + "  [OK] No errors detected via OCR.")

    return text


# Final Status
def print_result(push_ok, html_url, remote_url):
    print(f"\n{Fore.CYAN}{'='*55}")
    if push_ok:
        print(Fore.GREEN + f"  [DONE] PUSH COMPLETE -> {html_url or remote_url}")
    else:
        print(Fore.RED + "  [FAIL] PUSH FAILED. Check logs above.")
    print(f"{Fore.CYAN}{'='*55}\n")


# Main Entry
def main():
    print_banner()

    parser = argparse.ArgumentParser(
        prog="gitpusher",
        description="Automated Git Pusher -- zero friction GitHub deployment"
    )
    parser.add_argument("path",              nargs="?", default=".",   help="Project folder path")
    parser.add_argument("-m", "--message",   default="",              help="Commit message")
    parser.add_argument("-r", "--repo",      default="",              help="Repo name (default: folder name)")
    parser.add_argument("-d", "--description", default="",            help="Repo description")
    parser.add_argument("--private",         action="store_true",     help="Create as private repo")
    parser.add_argument("--branch",          default=DEFAULT_BRANCH,  help="Branch name")
    parser.add_argument("--remote",          default="",              help="Existing remote URL (skips repo creation)")
    parser.add_argument("--replace-remote",  action="store_true",     help="Replace an existing origin remote")
    parser.add_argument("--reset",           action="store_true",     help="Re-enter GitHub credentials")

    args = parser.parse_args()

    if args.reset:
        creds.reset()
        sys.exit(0)

    load_config()

    repo_path  = str(Path(args.path).resolve())
    if not Path(repo_path).is_dir():
        parser.error(f"Project folder does not exist: {repo_path}")
    repo_name  = args.repo or guess_repo_name(repo_path)
    branch     = args.branch
    commit_msg = args.message or f"chore: auto-push [{datetime.now().strftime('%Y-%m-%d %H:%M')}]"

    print(Fore.CYAN + f"\n  Project : {repo_path}")
    print(Fore.CYAN + f"  Repo    : {repo_name}")
    print(Fore.CYAN + f"  Branch  : {branch}")
    print(Fore.CYAN + f"  Message : {commit_msg}")

    remote_url = args.remote
    html_url   = ""

    existing_remote = git.get_remote_url(repo_path) if git.is_git_repo(repo_path) else ""
    if existing_remote and not remote_url and not args.replace_remote:
        remote_url = git.redact_remote_url(existing_remote)
        print(Fore.YELLOW + f"  Using existing origin: {remote_url}")

    if not remote_url:
        clone_url, html_url = phase_github_repo(repo_name, args.description, args.private)
        remote_url = clone_url

    phase_git_setup(repo_path, remote_url, branch, args.replace_remote)
    phase_commit(repo_path, commit_msg)
    push_ok = phase_push(repo_path, branch, remote_url)
    phase_ocr_monitor(repo_path)
    print_result(push_ok, html_url, remote_url)


if __name__ == "__main__":
    main()
