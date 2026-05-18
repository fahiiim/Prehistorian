import subprocess
from typing import List, Optional, Callable
from .models import CommitData

NOISE_EXTENSIONS = {".svg", ".png", ".jpg", ".jpeg", ".gif", ".ico"}
NOISE_FILES = {"package-lock.json", "yarn.lock", "poetry.lock", "pipfile.lock"}


def normalize_path(filepath: str) -> str:
    normalized = filepath.replace("\\", "/")
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def is_noise_file(filepath: str) -> bool:
    normalized = normalize_path(filepath)
    lower_path = normalized.lower()
    if any(lower_path.endswith(ext) for ext in NOISE_EXTENSIONS):
        return True
    filename = lower_path.split("/")[-1]
    if filename in NOISE_FILES:
        return True
    return False


def get_latest_commit_hash() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""


def get_commit_count() -> int:
    try:
        result = subprocess.run(
            ["git", "rev-list", "--all", "--count"],
            capture_output=True,
            text=True,
            check=True,
        )
        return int(result.stdout.strip() or 0)
    except (subprocess.CalledProcessError, ValueError):
        return 0


def parse_git_history(
    max_files_per_commit: int = 15,
    progress_callback: Optional[Callable[[int], None]] = None,
) -> List[CommitData]:
    try:
        result = subprocess.run(
            ["git", "log", "--all", "--name-only", "--pretty=format:COMMIT_START:%H"],
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError:
        return []

    lines = result.stdout.splitlines()
    commits: List[CommitData] = []
    current_hash = ""
    current_files: List[str] = []
    current_raw_count = 0
    commits_seen = 0

    for line in lines:
        line = line.strip()
        if not line:
            continue

        if line.startswith("COMMIT_START:"):
            if current_hash:
                if 0 < current_raw_count <= max_files_per_commit and current_files:
                    unique_files = sorted(set(current_files))
                    if unique_files:
                        commits.append(CommitData(hash=current_hash, files=unique_files))
            current_hash = line.replace("COMMIT_START:", "")
            current_files = []
            current_raw_count = 0
            commits_seen += 1
            if progress_callback:
                progress_callback(commits_seen)
        else:
            current_raw_count += 1
            normalized = normalize_path(line)
            if not is_noise_file(normalized):
                current_files.append(normalized)

    if current_hash and 0 < current_raw_count <= max_files_per_commit and current_files:
        unique_files = sorted(set(current_files))
        if unique_files:
            commits.append(CommitData(hash=current_hash, files=unique_files))

    return commits


def get_staged_files() -> List[str]:
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only"],
            capture_output=True,
            text=True,
            check=True,
        )
        staged_files: List[str] = []
        for line in result.stdout.splitlines():
            path = line.strip()
            if not path:
                continue
            normalized = normalize_path(path)
            if not is_noise_file(normalized):
                staged_files.append(normalized)
        return staged_files
    except subprocess.CalledProcessError:
        return []
