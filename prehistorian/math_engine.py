import joblib
import pandas as pd
from scipy.sparse import lil_matrix
from mlxtend.frequent_patterns import fpgrowth, association_rules
from typing import List, Dict, Optional
from pathlib import Path

from .models import CommitData, CoChangeRule, PrehistorianModel

MODEL_DIR = Path(".prehistorian")
MODEL_PATH = MODEL_DIR / "model.joblib"

def _create_matrix(commits: List[CommitData]) -> pd.DataFrame:
    unique_items = set()
    for commit in commits:
        unique_items.update(commit.files)
        
    items_list = sorted(list(unique_items))
    item_to_index = {item: idx for idx, item in enumerate(items_list)}
    
    sparse_mat = lil_matrix((len(commits), len(items_list)), dtype=bool)
    
    for row_idx, commit in enumerate(commits):
        for item in commit.files:
            sparse_mat[row_idx, item_to_index[item]] = True
            
    # Convert to pandas SparseDataFrame which is natively supported by mlxtend when we use 
    # use_colnames=True and min_support correctly
    df = pd.DataFrame.sparse.from_spmatrix(sparse_mat.tocsr(), columns=items_list)
    return df

def train_model(commits: List[CommitData], latest_hash: str) -> PrehistorianModel:
    if not commits:
        return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities={})
        
    df = _create_matrix(commits)
    
    try:
        # mlxtend >= 0.17.0 supports sparse dataframes directly
        frequent_itemsets = fpgrowth(df, min_support=0.01, use_colnames=True)
    except Exception:
        # Fallback if there's any issue with sparse matrix and mlxtend parsing
        # (usually it requires SparseDtype in pandas which we satisfy)
        frequent_itemsets = fpgrowth(df.sparse.to_dense(), min_support=0.01, use_colnames=True)

    if frequent_itemsets.empty:
        return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities={})
        
    rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=0.1, num_itemsets=len(frequent_itemsets))
    
    if rules.empty:
         return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities={})
         
    co_change_probs: Dict[str, List[CoChangeRule]] = {}
    
    for _, row in rules.iterrows():
        antecedents = list(row['antecedents'])
        consequents = list(row['consequents'])
        
        if len(antecedents) == 1 and len(consequents) == 1:
            file_a = antecedents[0]
            file_b = consequents[0]
            confidence = float(row['confidence']) * 100
            
            if file_a not in co_change_probs:
                co_change_probs[file_a] = []
            co_change_probs[file_a].append(CoChangeRule(file_a=file_a, file_b=file_b, confidence=confidence))
            
    for file_a in co_change_probs:
        co_change_probs[file_a].sort(key=lambda r: r.confidence, reverse=True)
        
    return PrehistorianModel(latest_commit_hash=latest_hash, co_change_probabilities=co_change_probs)

def save_model(model: PrehistorianModel):
    MODEL_DIR.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)

def load_model() -> Optional[PrehistorianModel]:
    if not MODEL_PATH.exists():
        return None
    return joblib.load(MODEL_PATH)
