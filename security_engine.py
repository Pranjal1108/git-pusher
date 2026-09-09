"""Small, dependency-free checks that prevent common credential leaks."""

import re
import subprocess
from pathlib import Path


# These patterns intentionally look for credential *formats*, not words such as
# "token" in documentation. Matches are reported by file and type only; values
# are never printed to the terminal or written to a log.
SECRET_PATTERNS = (
    ("GitHub token", re.compile(rb"\b(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})\b")),
    ("AWS access key", re.compile(rb"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("Google API key", re.compile(rb"\bAIza[0-9A-Za-z_-]{35}\b")),
    ("private key", re.compile(rb"-----BEGIN(?: [A-Z0-9]+)? PRIVATE KEY-----")),
    (
        "likely credential assignment",
        re.compile(
            rb"(?im)[\"']?(?:api[_-]?key|access[_-]?token|auth[_-]?token|"
            rb"client[_-]?secret|password|secret|token)[\"']?\s*[:=]\s*"
            rb"[\"']?[A-Za-z0-9_./+=-]{24,}"
        ),
    ),
)

MAX_SCAN_BYTES = 2 * 1024 * 1024


def _git_paths(path, args):
    result = subprocess.run(
        ["git", *args], cwd=path, capture_output=True, check=False
    )
    if result.returncode != 0:
        return []
    return [item.decode("utf-8", errors="surrogateescape") for item in result.stdout.split(b"\0") if item]


def changed_files(path):
    """List files that could enter the next commit, respecting .gitignore."""
    candidates = set()
    for args in (
        ["diff", "--name-only", "-z"],
        ["diff", "--cached", "--name-only", "-z"],
        ["ls-files", "--others", "--exclude-standard", "-z"],
    ):
        candidates.update(_git_paths(path, args))
    return sorted(candidates)


def find_secrets(path):
    """Return (relative path, credential kind) pairs without exposing values."""
    findings = []
    root = Path(path)
    for relative_path in changed_files(path):
        file_path = root / relative_path
        if not file_path.is_file():
            continue
        try:
            with file_path.open("rb") as source:
                content = source.read(MAX_SCAN_BYTES + 1)
        except OSError:
            continue

        # Binary assets cannot normally contain configuration credentials and
        # scanning them tends to create false positives.
        if b"\0" in content:
            continue

        for label, pattern in SECRET_PATTERNS:
            if pattern.search(content):
                findings.append((relative_path, label))
                break
    return findings
