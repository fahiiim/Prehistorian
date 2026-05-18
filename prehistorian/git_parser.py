import subprocess
from typing import List
from .models import CommitData

NOISE_EXTENSIONS = {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.ico'}
NOISE_FILES = {'package-lock.json', 'yarn.lock', 'poetry.lock', 'Pipfile.lock'}

def is_noise_file(filepath: str) -> bool:
    if any(filepath.endswith(ext) for ext in NOISE_EXTENSIONS):
        return True
    filename = filepath.split('/')[-1]
    if filename in NOISE_FILES:
        return True
    return False

def get_latest_commit_hash() -> str:
    try:
        result = subprocess.run(
            ['git', 'rev-parse', 'HEAD'],
            capture_output=True, text=True, check=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return ""

def parse_git_history(max_files_per_commit: int = 15) -> List[CommitData]:
    try:
        result = subprocess.run(
            ['git', 'log', '--all', '--name-only', '--pretty=format:COMMIT_START:%H'],
            capture_output=True, text=True, check=True
        )
    except subprocess.CalledProcessError:
        return []

    lines = result.stdout.splitlines()
    commits = []
    current_hash = ""
    current_files = []

    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        if line.startswith('COMMIT_START:'):
            if current_hash:
                if 0 < len(current_files) <= max_files_per_commit:
                    commits.append(CommitData(hash=current_hash, files=current_files))
            current_hash = line.replace('COMMIT_START:', '')
            current_files = []
        else:
            if not is_noise_file(line):
                current_files.append(line)
                
    if current_hash and 0 < len(current_files) <= max_files_per_commit:
        commits.append(CommitData(hash=current_hash, files=current_files))
        
    return commits

def get_staged_files() -> List[str]:
    try:
        result = subprocess.run(
            ['git', 'diff', '--cached', '--name-only'],
            capture_output=True, text=True, check=True
        )
        return [f.strip() for f in result.stdout.splitlines() if f.strip() and not is_noise_file(f.strip())]
    except subprocess.CalledProcessError:
        return []
