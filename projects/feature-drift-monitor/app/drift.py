from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.spatial.distance import jensenshannon

@dataclass
class FeatureResult:
    feature: str
    kind: str
    metric: float
    threshold: float
    drifted: bool

def psi(reference, current, bins=10):
    ref = pd.to_numeric(reference, errors="coerce").dropna().to_numpy()
    cur = pd.to_numeric(current, errors="coerce").dropna().to_numpy()
    if len(ref) == 0 or len(cur) == 0: return float("nan")
    edges = np.unique(np.quantile(ref, np.linspace(0, 1, bins + 1)))
    if len(edges) < 3: return 0.0
    edges[0], edges[-1] = -np.inf, np.inf
    r = np.histogram(ref, bins=edges)[0] / len(ref)
    c = np.histogram(cur, bins=edges)[0] / len(cur)
    eps = 1e-6
    r, c = np.clip(r, eps, None), np.clip(c, eps, None)
    return float(np.sum((c-r) * np.log(c/r)))

def js_divergence(reference, current):
    categories = sorted(set(reference.dropna().astype(str)) | set(current.dropna().astype(str)))
    if not categories: return float("nan")
    r = reference.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()
    c = current.astype(str).value_counts(normalize=True).reindex(categories, fill_value=0).to_numpy()
    return float(jensenshannon(r, c, base=2.0) ** 2)

def analyze(reference, current, numeric_threshold=.20, categorical_threshold=.10, bins=10):
    results=[]
    for col in [c for c in reference.columns if c in current.columns]:
        numeric = pd.api.types.is_numeric_dtype(reference[col]) and pd.api.types.is_numeric_dtype(current[col])
        metric = psi(reference[col], current[col], bins) if numeric else js_divergence(reference[col], current[col])
        threshold = numeric_threshold if numeric else categorical_threshold
        results.append(FeatureResult(col, "numeric" if numeric else "categorical", metric, threshold, bool(metric >= threshold)))
    return results
