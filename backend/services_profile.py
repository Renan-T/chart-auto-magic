# backend/services_profile.py
from __future__ import annotations
import pandas as pd
from typing import Any, Dict, List, Tuple

def profile_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
    cols = []
    for c in df.columns:
        kind = "date" if pd.api.types.is_datetime64_any_dtype(df[c]) else ("number" if df[c].dtype.kind in "if" else "string")
        cols.append({"name": c, "dtype": kind})
    stats = {}
    for c in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[c]):
            stats[c] = {
                "min": str(df[c].min()) if not df[c].isna().all() else None,
                "max": str(df[c].max()) if not df[c].isna().all() else None,
                "count": int(df[c].notna().sum())
            }
        elif df[c].dtype.kind in "if":
            s = df[c].dropna()
            stats[c] = {
                "count": int(s.shape[0]),
                "sum": float(s.sum()) if not s.empty else 0.0,
                "mean": float(s.mean()) if not s.empty else 0.0
            }
        else:
            # valor mais frequente (modo) para sinalizar dimensão útil
            top = df[c].dropna().value_counts().head(3)
            stats[c] = {"top_values": [str(i) for i in top.index.tolist()], "top_counts": [int(v) for v in top.values.tolist()]}
    # cobertura temporal (se houver apenas 1 coluna de data)
    date_cols = [c for c in df.columns if pd.api.types.is_datetime64_any_dtype(df[c])]
    coverage = None
    if date_cols:
        d = date_cols[0]
        coverage = {"date_col": d, "min": str(df[d].min()), "max": str(df[d].max())}
    return {"columns": cols, "stats": stats, "time_coverage": coverage}
