import os
import sys
import requests
import getpass
from pathlib import Path
from colorama import Fore, Style, init, just_fix_windows_console

os.environ.setdefault("PYTHONUTF8", "1")
just_fix_windows_console()
init(autoreset=True)

ENV_PATH = Path(__file__).parent / ".env"
GITHUB_API = "https://api.github.com"


# Env Reader
def _read_env():
    data = {}
    if ENV_PATH.exists():
        for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                data[k.strip()] = v.strip()
    return data


# Env Writer
def _write_env(data):
    lines = [f"{k}={v}" for k, v in data.items()]
    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


# Already Setup
def is_configured():
    data = _read_env()
    return bool(data.get("GITHUB_USERNAME")) and bool(data.get("GITHUB_TOKEN"))


# Verify Token with GitHub API
def verify_token(token):
    if not token:
        return False, "", "Token cannot be empty."
    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "GIT-PUSHer"
    }
    try:
        r = requests.get(f"{GITHUB_API}/user", headers=headers, timeout=10)
        if r.status_code == 200:
            user_data = r.json()
            return True, user_data.get("login", ""), "Token valid!"
        elif r.status_code == 401:
            return False, "", "Invalid GitHub Token (401 Unauthorized)."
        else:
            return False, "", f"GitHub API error (Status {r.status_code})."
    except requests.RequestException as e:
        return False, "", f"Could not verify the token because GitHub could not be reached ({e})."


# Setup Wizard
def run_setup():
    width = 56
    print()
    print(Fore.CYAN + "+" + "=" * width + "+")
    print(Fore.CYAN + "|" + Fore.YELLOW + "  SETUP GITHUB CREDENTIALS".center(width) + Fore.CYAN + "|")
    print(Fore.CYAN + "|" + Fore.WHITE + "  Credentials are saved locally in .env".center(width) + Fore.CYAN + "|")
    print(Fore.CYAN + "+" + "=" * width + "+")
    print()

    existing = _read_env()
    valid = False
    token = ""
    username = ""

    while not valid:
        print(Fore.CYAN + "  GitHub Personal Access Token")
        print(Fore.WHITE + "  Create one at: https://github.com/settings/tokens")
        print(Fore.WHITE + "  Required scope: 'repo'")
        print(Fore.WHITE + "  (Tip: Paste using Ctrl+V or Right-Click in terminal)")
        
        token = getpass.getpass(Fore.YELLOW + "  Token > " + Style.RESET_ALL).strip()
        if not token:
            print(Fore.RED + "  [!] Token cannot be empty. Please try again.\n")
            continue

        print(Fore.CYAN + "  [...] Verifying token with GitHub API...")
        is_ok, detected_user, msg = verify_token(token)

        if is_ok:
            print(Fore.GREEN + f"  [OK] {msg}")
            if detected_user:
                print(Fore.GREEN + f"  [OK] Detected Username: {Fore.WHITE}{detected_user}")
                username = detected_user
            valid = True
        else:
            print(Fore.RED + f"  [FAIL] {msg}")
            retry = input(Fore.YELLOW + "  Try entering token again? (Y/n): " + Style.RESET_ALL).strip().lower()
            if retry == 'n':
                print(Fore.RED + "  Setup cancelled.")
                sys.exit(1)
            print()

    if not username:
        print()
        print(Fore.CYAN + "  GitHub Username")
        print(Fore.WHITE + "  Enter your GitHub account username:")
        while not username:
            username = input(Fore.YELLOW + "  Username > " + Style.RESET_ALL).strip()
            if not username:
                print(Fore.RED + "  [!] Username cannot be empty.\n")

    existing["GITHUB_USERNAME"] = username
    existing["GITHUB_TOKEN"]    = token
    if "TESSERACT_PATH" not in existing or not existing["TESSERACT_PATH"]:
        existing["TESSERACT_PATH"] = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

    _write_env(existing)

    print()
    print(Fore.GREEN + f"  [SUCCESS] Credentials saved! Signed in as {username}")
    print(Fore.WHITE + "  Continuing with GIT PUSHer...\n")


# Load Credentials
def load():
    if not is_configured():
        run_setup()

    data = _read_env()
    return data.get("GITHUB_USERNAME", ""), data.get("GITHUB_TOKEN", ""), data.get("TESSERACT_PATH", "")


# Reset Credentials
def reset():
    data = _read_env()
    data["GITHUB_USERNAME"] = ""
    data["GITHUB_TOKEN"]    = ""
    _write_env(data)
    print(Fore.YELLOW + "  [!] Credentials cleared. Starting setup wizard...\n")
    run_setup()
