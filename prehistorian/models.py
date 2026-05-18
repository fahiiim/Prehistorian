from dataclasses import dataclass
from typing import List, Dict

@dataclass
class CommitData:
    hash: str
    files: List[str]

@dataclass
class CoChangeRule:
    file_a: str
    file_b: str
    confidence: float # From 0.0 to 100.0

@dataclass
class PrehistorianModel:
    latest_commit_hash: str
    co_change_probabilities: Dict[str, List[CoChangeRule]]
