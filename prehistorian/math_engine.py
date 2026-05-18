import joblib
import pandas as pd
from scipy.sparse import lil_matrix, csr_matrix
from mlxtend.frequent_patterns import fpgrowth
from typing import List, Dict, Optional, Set, FrozenSet, Tuple
from pathlib import Path

from .models import CommitData, CoChangeRule, PrehistorianModel

MODEL_DIR = Path(".prehistorian")
MODEL_PATH = MODEL_DIR / "model.joblib"
MIN_SUPPORT = 0.01


def _build_sparse_matrix(commits: List[CommitData]) -> Tuple[csr_matrix, List[str]]:
    unique_items = set()
    for commit in commits:
        unique_items.update(commit.files)

    items_list = sorted(unique_items)
    item_to_index = {item: idx for idx, item in enumerate(items_list)}

    sparse_mat = lil_matrix((len(commits), len(items_list)), dtype=int)

    for row_idx, commit in enumerate(commits):
        for item in set(commit.files):
            sparse_mat[row_idx, item_to_index[item]] = 1

    return sparse_mat.tocsr(), items_list


def _build_dataframe(matrix: csr_matrix, items_list: List[str]) -> pd.DataFrame:
    return pd.DataFrame.sparse.from_spmatrix(matrix, columns=items_list)


def _find_frequent_pairs(df: pd.DataFrame) -> Set[FrozenSet[str]]:
    if df.empty or df.shape[1] == 0:
        return set()

    try:
        frequent_itemsets = fpgrowth(
            df,
            min_support=MIN_SUPPORT,
            use_colnames=True,
            max_len=2,
        )
    except Exception:
        frequent_itemsets = fpgrowth(
            df.sparse.to_dense(),
            min_support=MIN_SUPPORT,
            use_colnames=True,
            max_len=2,
        )

    if frequent_itemsets.empty:
        return set()

    pairs: Set[FrozenSet[str]] = set()
    for itemset in frequent_itemsets["itemsets"]:
        if len(itemset) == 2:
            pairs.add(frozenset(itemset))
    return pairs


def _calculate_markov(
    matrix: csr_matrix,
    items_list: List[str],
    frequent_pairs: Set[FrozenSet[str]],
) -> Dict[str, List[CoChangeRule]]:
    if matrix.shape[1] == 0:
        return {}

    file_counts = matrix.sum(axis=0).A1
    cooc = (matrix.T @ matrix).tocoo()
    co_change_probs: Dict[str, List[CoChangeRule]] = {}

    for row_idx, col_idx, count in zip(cooc.row, cooc.col, cooc.data):
        if row_idx == col_idx:
            continue
        count_a = file_counts[row_idx]
        if count_a == 0:
            continue

        file_a = items_list[row_idx]
        file_b = items_list[col_idx]

        if frequent_pairs and frozenset((file_a, file_b)) not in frequent_pairs:
            continue

        confidence = (float(count) / float(count_a)) * 100.0
        co_change_probs.setdefault(file_a, []).append(
            CoChangeRule(file_a=file_a, file_b=file_b, confidence=confidence)
        )

    for file_a in co_change_probs:
        co_change_probs[file_a].sort(key=lambda r: r.confidence, reverse=True)

    return co_change_probs


def train_model(commits: List[CommitData], latest_hash: str) -> PrehistorianModel:
    if not commits:
        return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities={})

    matrix, items_list = _build_sparse_matrix(commits)
    if matrix.shape[1] == 0:
        return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities={})

    df = _build_dataframe(matrix, items_list)
    frequent_pairs = _find_frequent_pairs(df)
    co_change_probs = _calculate_markov(matrix, items_list, frequent_pairs)

    return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities=co_change_probs)

def save_model(model: PrehistorianModel):
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

def load_model() -> Optional[PrehistorianModel]:
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)
