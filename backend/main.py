# main.py — AutoDash BI Comercial (backend)
from __future__ import annotations

import io, re, uuid, json, os
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from fastapi import FastAPI, UploadFile, File, HTTPException, Query, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

# IA (OpenRouter) e perfis/estatísticas
from ai_client import chat_json
from ai_prompts import DETECT_SYSTEM, DETECT_USER_TEMPLATE, SUGGEST_SYSTEM, SUGGEST_USER_TEMPLATE
from services_profile import profile_dataframe

# =========================
# Config & Persistência
# =========================

app = FastAPI(title="AutoDash BI Comercial - Backend IA + Persistência")

FRONT_ORIGINS = [
    "http://localhost:5173", "http://127.0.0.1:5173",
    "http://localhost:8080", "http://127.0.0.1:8080"
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=FRONT_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Diretórios
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
UPLOAD_DIR = DATA_DIR / "uploads"
NORM_DIR = DATA_DIR / "normalized"
DASH_DIR = DATA_DIR / "dashboards"
LOGS_DIR = DATA_DIR / "logs"

for d in (DATA_DIR, UPLOAD_DIR, NORM_DIR, DASH_DIR, LOGS_DIR):
    d.mkdir(parents=True, exist_ok=True)

def _ts() -> str:
    return datetime.utcnow().strftime("%Y%m%dT%H%M%S")

def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

def _read_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)

def _save_parquet(df: pd.DataFrame, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(path, index=False)

def _load_parquet(path: Path) -> pd.DataFrame:
    return pd.read_parquet(path)

def _load_semantic_meta(normalized_dataset_id: str) -> Dict[str, Any]:
    """
    Lê o meta de semântica salvo no normalize. Retorna {"columns": []} se não existir.
    """
    meta_path = NORM_DIR / f"{normalized_dataset_id}.meta.json"
    if meta_path.exists():
        return _read_json(meta_path)
    return {"columns": []}


# Armazenamento em memória (MVP) — com fallback no disco
DATASETS: Dict[str, pd.DataFrame] = {}
NORMALIZED: Dict[str, pd.DataFrame] = {}
DASHBOARDS: Dict[str, Dict[str, Any]] = {}

# Defaults para sugestão de gráficos (podem vir do .env ou usar fallback)
# >>> Padrão "groupby" evita criação de meses vazios
DEFAULT_AGG_MODE = (os.getenv("DEFAULT_AGG_MODE", "groupby") or "groupby").strip().lower()  # "resample" | "groupby"
DEFAULT_DROP_ALL_ZERO = os.getenv("DEFAULT_DROP_ALL_ZERO", "true").strip().lower() in ("1","true","yes","on")


# =========================
# Modelos Pydantic (contratos)
# =========================

class Column(BaseModel):
    name: str
    dtype: str                     # number|string|date|percent|currency|category|unknown
    semantic: Optional[str] = None # revenue|target|orders|seller|product|region|channel|date|discount|margin
    format: Optional[str] = None   # BRL|percent|yyyy-MM-dd|dd/MM/yyyy etc.

class DatasetPreview(BaseModel):
    dataset_id: str
    columns: List[Column]
    sample_rows: List[Dict[str, Any]]

class QualityIssue(BaseModel):
    col: str
    issue: str
    details: Optional[str] = None

class NormalizeResult(BaseModel):
    normalized_dataset_id: str
    rows: int
    columns: List[Column]
    quality: List[QualityIssue]

class KPI(BaseModel):
    name: str
    value: float
    unit: Optional[str] = None
    change: Optional[float] = None
    changeLabel: Optional[str] = None
    trend: Optional[str] = None

class KPIPlan(BaseModel):
    name: str
    value_expr: str
    fmt: Optional[str] = None
    explain: Optional[str] = None

class ChartSeries(BaseModel):
    key: str
    label: str
    dashed: Optional[bool] = None

class ChartPlan(BaseModel):
    type: str
    title: str
    xKey: Optional[str] = None
    yKey: Optional[str] = None
    series: Optional[List[ChartSeries]] = None
    categoryKey: Optional[str] = None
    valueKey: Optional[str] = None
    topN: Optional[int] = 5

class ChartSpec(BaseModel):
    type: str
    title: str
    data: List[Dict[str, Any]]
    xKey: Optional[str] = None
    yKey: Optional[str] = None
    series: Optional[List[ChartSeries]] = None
    categoryKey: Optional[str] = None
    valueKey: Optional[str] = None

class Insight(BaseModel):
    type: str
    title: str
    message: str

class DashboardDoc(BaseModel):
    dataset_id: str
    kpis: List[KPI]
    charts: List[ChartSpec]
    insights: List[Insight]
    filters: Optional[Dict[str, Any]] = None
    version: Optional[str] = None

# =========================
# Utils determinísticos
# =========================

_U_SPACE_CHARS = [
    "\u00A0",  # NBSP
    "\u202F",  # NNBSP
    "\u2007",  # figure space
    "\u2009",  # thin space
]
_money_symbols = ("R$", "US$", "€", "£")

def _to_number_ptbr(x: Any) -> Optional[float]:
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return None
    s = str(x).strip()
    if s == "" or s == "—":
        return None
    # remove símbolos monetários e QUALQUER espaço unicode
    for sym in _money_symbols:
        if s.startswith(sym):
            s = s[len(sym):]
    for sp in _U_SPACE_CHARS:
        s = s.replace(sp, "")
    s = s.replace(" ", "")

    # percentuais
    if s.endswith("%"):
        s = s[:-1]
        s = s.replace(".", "").replace(",", ".")
        try:
            return float(s) / 100.0
        except Exception:
            return None

    # decimal pt-BR
    try:
        if "," in s and "." in s:
            s = s.replace(".", "").replace(",", ".")
        elif "," in s:
            s = s.replace(",", ".")
        return float(s)
    except Exception:
        return None

def _snake(s: str) -> str:
    return re.sub(r"[^a-zA-Z0-9]+", "_", s).strip("_").lower()

def _parse_date_smart(series: pd.Series) -> pd.Series:
    """Parser de data estável: tenta formatos mais comuns antes do to_datetime flexível."""
    s = series.astype(str).str.strip()
    # heurística barata: checa padrão do primeiro valor não-nulo
    vals = s[s.ne("")].dropna().unique()
    if len(vals):
        v = vals[0]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", v):
            return pd.to_datetime(s, format="%Y-%m-%d", errors="coerce")
        if re.fullmatch(r"\d{2}/\d{2}/\d{4}", v):
            return pd.to_datetime(s, format="%d/%m/%Y", errors="coerce")
    # fallback tolerante (dayfirst=True ajuda no pt-BR)
    return pd.to_datetime(s, dayfirst=True, errors="coerce")

def _find_date_col(df: pd.DataFrame) -> Optional[str]:
    """
    Escolhe de forma estável a coluna de data.
    1) Se existir 'data' com dtype datetime, usa ela.
    2) Senão, tenta nomes comuns 'date', 'dt', 'dia', 'competencia' (datetime).
    3) NUNCA usa 'mes' ou 'ano' como coluna de data.
    4) Se nada acima, primeira coluna datetime.
    """
    if "data" in df.columns and pd.api.types.is_datetime64_any_dtype(df["data"]):
        return "data"
    for cand in ["date", "dt", "dia", "competencia", "month"]:
        if cand in df.columns and pd.api.types.is_datetime64_any_dtype(df[cand]):
            return cand
    for c in df.columns:
        if c not in ("mes", "ano") and pd.api.types.is_datetime64_any_dtype(df[c]):
            return c
    return None

def monthly_aggregate(
    df: pd.DataFrame,
    date_col: str,
    cols: List[str],
    mode: str = "groupby",          # "resample" | "groupby"
    drop_all_zero: bool = True       # remove meses em que todas as 'cols' somam 0
) -> pd.DataFrame:
    """
    Agrega valores por mês para 'cols', retornando:
      - coluna 'month' (YYYY-MM)
      - uma linha por mês (apenas existentes em 'groupby'; grade contínua em 'resample')
    """
    if not cols:
        return pd.DataFrame(columns=["month"])

    ts = df[[date_col] + cols].dropna(subset=[date_col]).copy()
    if ts.empty:
        return pd.DataFrame(columns=["month"] + cols)

    if not pd.api.types.is_datetime64_any_dtype(ts[date_col]):
        raise ValueError(f"Coluna '{date_col}' não é datetime")

    if mode == "groupby":
        ts["_month"] = ts[date_col].values.astype("datetime64[M]")
        agg = ts.groupby("_month")[cols].sum(numeric_only=True).reset_index()
        agg["month"] = pd.to_datetime(agg["_month"]).dt.strftime("%Y-%m")
        agg = agg.drop(columns=["_month"])
    else:
        agg = ts.set_index(date_col).resample("MS").sum(numeric_only=True).reset_index()
        agg["month"] = agg[date_col].dt.strftime("%Y-%m")
        agg = agg.drop(columns=[date_col])

    if drop_all_zero and not agg.empty:
        mask_nonzero = (agg[cols].fillna(0).abs().sum(axis=1) > 0)
        agg = agg[mask_nonzero].reset_index(drop=True)

    return agg[["month"] + cols]

# =========================
# Health
# =========================

@app.get("/api/health")
def health():
    return {"ok": True, "ts": datetime.utcnow().isoformat()}

# =========================
# Upload (persiste arquivo e preview)
# =========================

@app.post("/api/files/upload", response_model=DatasetPreview)
async def upload_file(file: UploadFile = File(...)):
    content = await file.read()
    ext = (file.filename or "").lower()

    # ler em DF
    df = None
    try:
        if ext.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(content))
            except Exception:
                df = pd.read_csv(io.BytesIO(content), sep=";")
        elif ext.endswith(".xlsx") or ext.endswith(".xls"):
            df = pd.read_excel(io.BytesIO(content))
        else:
            try:
                df = pd.read_csv(io.BytesIO(content))
            except Exception:
                df = pd.read_excel(io.BytesIO(content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Falha ao ler arquivo: {e}")

    if df is None or df.empty:
        raise HTTPException(status_code=400, detail="Arquivo vazio ou ilegível.")

    dataset_id = f"ds_{uuid.uuid4().hex[:6]}"
    DATASETS[dataset_id] = df

    # salvar arquivo original
    real_ext = ".xlsx" if "xlsx" in ext or "xls" in ext else ".csv"
    upload_path = UPLOAD_DIR / f"{dataset_id}{real_ext}"
    upload_path.write_bytes(content)

    # preview neutro
    columns = [Column(name=str(c), dtype="unknown").dict() for c in df.columns]
    sample = df.head(5).fillna("").astype(str).to_dict(orient="records")
    preview = {"dataset_id": dataset_id, "columns": columns, "sample_rows": sample}

    # log do upload
    log_dir = LOGS_DIR / dataset_id
    _write_json(log_dir / f"upload-preview-{_ts()}.json", preview)

    return DatasetPreview(**preview)

# =========================
# Detecção (IA) — persiste request/response
# =========================

class AiDetectBody(BaseModel):
    dataset_id: str
    model: Optional[str] = None

@app.post("/api/schema/detect_ai")
async def detect_ai(body: AiDetectBody):
    df = DATASETS.get(body.dataset_id)
    if df is None:
        # tenta recarregar do disco
        cand_csv = UPLOAD_DIR / f"{body.dataset_id}.csv"
        cand_xlsx = UPLOAD_DIR / f"{body.dataset_id}.xlsx"
        if cand_csv.exists():
            df = pd.read_csv(cand_csv)
        elif cand_xlsx.exists():
            df = pd.read_excel(cand_xlsx)
        else:
            raise HTTPException(status_code=404, detail="dataset_id não encontrado")
        DATASETS[body.dataset_id] = df

    sample = df.head(5).fillna("").astype(str).to_dict(orient="records")
    backend_inferred = [{"name": str(c), "dtype": "unknown"} for c in df.columns]

    user = DETECT_USER_TEMPLATE.format(
        filename=f"{body.dataset_id}.csv",
        sample_rows=json.dumps(sample, ensure_ascii=False)[:5000],
        backend_inferred=json.dumps(backend_inferred, ensure_ascii=False),
    )
    messages = [
        {"role": "system", "content": DETECT_SYSTEM},
        {"role": "user", "content": user}
    ]

    # log da requisição
    log_dir = LOGS_DIR / body.dataset_id
    _write_json(log_dir / f"detect_ai-request-{_ts()}.json", {"model": body.model, "messages": messages})

    out = await chat_json(messages, model=body.model)

    # exige JSON válido
    if "_raw" in out:
        _write_json(log_dir / f"detect_ai-error-{_ts()}.json", {"raw": out["_raw"]})
        raise HTTPException(status_code=502, detail=f"Modelo não retornou JSON válido")

    if "columns" not in out or not isinstance(out["columns"], list):
        _write_json(log_dir / f"detect_ai-error-{_ts()}.json", {"out": out})
        raise HTTPException(status_code=502, detail="Resposta sem 'columns' válida pela IA")

    _write_json(log_dir / f"detect_ai-response-{_ts()}.json", out)

    cols: List[Dict[str, Any]] = []
    for col in out["columns"]:
        name = str(col.get("name") or "")
        dtype = str(col.get("dtype") or "string")
        semantic = col.get("semantic")
        fmt = col.get("format")
        cols.append({"name": name, "dtype": dtype, "semantic": semantic, "format": fmt})

    return {"columns": cols}

@app.get("/api/schema/detect")
def detect_schema_disabled():
    raise HTTPException(status_code=410, detail="Use /api/schema/detect_ai")

# =========================
# Normalização (determinística) — persiste parquet, meta e log
# =========================

class NormalizeBody(BaseModel):
    dataset_id: str
    columns: Optional[List[Column]] = None
    currency: Optional[str] = "BRL"
    date_formats: Optional[List[str]] = ["dd/MM/yyyy", "yyyy-MM-dd"]
    coerce_numbers_ptbr: Optional[bool] = True

@app.post("/api/normalize", response_model=NormalizeResult)
def normalize(body: NormalizeBody):
    df = DATASETS.get(body.dataset_id)
    if df is None:
        cand_csv = UPLOAD_DIR / f"{body.dataset_id}.csv"
        cand_xlsx = UPLOAD_DIR / f"{body.dataset_id}.xlsx"
        if cand_csv.exists():
            df = pd.read_csv(cand_csv)
        elif cand_xlsx.exists():
            df = pd.read_excel(cand_xlsx)
        else:
            raise HTTPException(status_code=404, detail="dataset_id não encontrado")
        DATASETS[body.dataset_id] = df

    norm = df.copy()
    quality: List[QualityIssue] = []

    # Mapa de dtype vindo do detect_ai (para conversão determinística)
    dtype_map: Dict[str, str] = {}
    if body.columns:
        for col in body.columns:
            dtype_map[col.name] = col.dtype

    # Conversões
    for c in norm.columns:
        dt = dtype_map.get(str(c), "unknown")
        if dt == "date":
            try:
                norm[c] = _parse_date_smart(norm[c])
            except Exception:
                quality.append(QualityIssue(col=str(c), issue="date_parse_error", details="Falha ao converter data"))
        elif dt in ("currency", "percent", "number"):
            norm[c] = norm[c].apply(_to_number_ptbr)
        else:
            norm[c] = norm[c]

    # Qualidade (missing)
    for c in norm.columns:
        miss = int(norm[c].isna().sum())
        if miss:
            quality.append(QualityIssue(col=str(c), issue="missing", details=f"{miss} células ausentes"))

    # ID e persistência
    normalized_dataset_id = f"nds_{uuid.uuid4().hex[:6]}"
    NORMALIZED[normalized_dataset_id] = norm

    # Salvar parquet do normalizado
    _save_parquet(norm, NORM_DIR / f"{normalized_dataset_id}.parquet")

    # Persistir metadados de semântica vindos do detect_ai (limpando "null" string)
    sem_meta: List[Dict[str, Any]] = []
    if body.columns:
        for col in body.columns:
            sem_val = col.semantic
            if isinstance(sem_val, str) and sem_val.strip().lower() == "null":
                sem_val = None
            fmt_val = col.format
            if isinstance(fmt_val, str) and fmt_val.strip().lower() == "null":
                fmt_val = None
            sem_meta.append({
                "name": col.name,
                "dtype": col.dtype,
                "semantic": sem_val,
                "format": fmt_val,
            })

    meta_path = NORM_DIR / f"{normalized_dataset_id}.meta.json"
    _write_json(meta_path, {
        "dataset_id": body.dataset_id,
        "normalized_dataset_id": normalized_dataset_id,
        "columns": sem_meta
    })

    # Monta colunas de saída (para o front)
    cols: List[Column] = []
    for c in norm.columns:
        if str(c) in dtype_map:
            dt = dtype_map[str(c)]
        else:
            if pd.api.types.is_datetime64_any_dtype(norm[c]):
                dt = "date"
            elif norm[c].dtype.kind in "if":
                dt = "number"
            else:
                dt = "string"
        cols.append(Column(name=_snake(str(c)), dtype=dt))

    result = NormalizeResult(
        normalized_dataset_id=normalized_dataset_id,
        rows=int(len(norm)),
        columns=cols,
        quality=quality
    )

    # Log
    log_dir = LOGS_DIR / body.dataset_id
    _write_json(log_dir / f"normalize-{normalized_dataset_id}-{_ts()}.json", json.loads(result.model_dump_json()))

    return result


# =========================
# Executor seguro de KPIs
# =========================

FUNC_ONE = {"sum", "avg", "min", "max", "count", "growth_mom"}
FUNC_TWO = {"attainment"}  # attainment(revenue,target) -> sum(revenue)/sum(target)

def _eval_kpi_expr(expr: str, df: pd.DataFrame) -> float:
    expr = (expr or "").strip()
    m = re.fullmatch(r"([a-zA-Z_]+)\s*\(([^()]+)\)", expr)
    if not m:
        raise ValueError(f"Expressão KPI inválida: {expr}")
    func = m.group(1).lower()
    args = [a.strip() for a in m.group(2).split(",")]

    if func in FUNC_ONE and len(args) == 1:
        col = args[0]
        if col not in df.columns:
            raise ValueError(f"Coluna '{col}' não encontrada")
        s = pd.to_numeric(df[col], errors="coerce")
        if func == "sum":   return float(s.fillna(0).sum())
        if func == "avg":   return float(s.dropna().mean()) if not s.dropna().empty else 0.0
        if func == "min":   return float(s.dropna().min()) if not s.dropna().empty else 0.0
        if func == "max":   return float(s.dropna().max()) if not s.dropna().empty else 0.0
        if func == "count": return float(s.notna().sum())
        if func == "growth_mom":
            date_col = _find_date_col(df)
            if not date_col:
                return 0.0
            agg = monthly_aggregate(df, date_col, [col], mode="groupby", drop_all_zero=True)
            if len(agg) < 2:
                return 0.0
            last, prev = float(agg.iloc[-1][col] or 0.0), float(agg.iloc[-2][col] or 0.0)
            if prev == 0:
                return 0.0
            return (last - prev) / abs(prev)

    if func in FUNC_TWO and len(args) == 2:
        a, b = args
        if a not in df.columns or b not in df.columns:
            raise ValueError(f"Coluna não encontrada em {expr}")
        sa = float(pd.to_numeric(df[a], errors="coerce").fillna(0).sum())
        sb = float(pd.to_numeric(df[b], errors="coerce").fillna(0).sum())
        return (sa / sb) if sb != 0 else 0.0

    raise ValueError(f"Função não permitida ou aridade inválida: {expr}")

def _fmt_value(v: float, fmt: Optional[str]) -> Tuple[float, Optional[str]]:
    unit = None
    if fmt:
        f = fmt.lower()
        if f.startswith("currency"):
            parts = f.split(":")
            cur = parts[1] if len(parts) > 1 else "BRL"
            unit = f"currency:{cur}"
        elif f in ("percent", "%"):
            unit = "percent"
        elif f == "number":
            unit = None
    return float(v), unit

# =========================
# Sugestão (IA) — usa semantic_hints, persiste plano e dashboard
# =========================

class AiSuggestBody(BaseModel):
    normalized_dataset_id: str
    model: Optional[str] = None
    agg_mode: Optional[str] = None        # "resample" | "groupby" | None (usa default)
    drop_all_zero: Optional[bool] = None  # None -> usa default

@app.post("/api/dash/suggest_ai", response_model=DashboardDoc)
async def suggest_ai(body: AiSuggestBody):
    nds = NORMALIZED.get(body.normalized_dataset_id)
    if nds is None:
        path = NORM_DIR / f"{body.normalized_dataset_id}.parquet"
        if not path.exists():
            raise HTTPException(status_code=404, detail="normalized_dataset_id não encontrado")
        nds = _load_parquet(path)
        NORMALIZED[body.normalized_dataset_id] = nds

    # Descobrir dataset_id original (para logs)
    dataset_id = None
    for d in LOGS_DIR.iterdir():
        if (d / f"normalize-{body.normalized_dataset_id}.json").exists():
            dataset_id = d.name
            break
        for _ in d.glob(f"normalize-{body.normalized_dataset_id}-*.json"):
            dataset_id = d.name
            break
        if dataset_id:
            break
    if dataset_id is None:
        dataset_id = "unknown"

    # Carregar dicas semânticas geradas no normalize
    meta = _load_semantic_meta(body.normalized_dataset_id)  # {"columns": [...]}

    # Perfil resumido (numérico e estrutural)
    prof = profile_dataframe(nds)

    # Prompt do usuário com semantic_hints
    user = SUGGEST_USER_TEMPLATE.format(
        columns=json.dumps(prof["columns"], ensure_ascii=False),
        stats=json.dumps(prof["stats"], ensure_ascii=False)[:8000],
        time_coverage=json.dumps(prof["time_coverage"], ensure_ascii=False),
        semantic_hints=json.dumps(meta.get("columns", []), ensure_ascii=False)
    )
    messages = [
        {"role": "system", "content": SUGGEST_SYSTEM},
        {"role": "user", "content": user}
    ]

    # Log request
    log_dir = LOGS_DIR / dataset_id
    _write_json(log_dir / f"suggest_ai-request-{body.normalized_dataset_id}-{_ts()}.json",
                {"model": body.model, "messages": messages,
                 "agg_mode": body.agg_mode, "drop_all_zero": body.drop_all_zero})

    # Chamada IA (plano)
    out = await chat_json(messages, model=body.model, max_tokens=3000)

    if "_raw" in out:
        _write_json(log_dir / f"suggest_ai-error-{body.normalized_dataset_id}-{_ts()}.json", {"raw": out["_raw"]})
        raise HTTPException(status_code=502, detail="Modelo não retornou JSON válido")

    # ---- KPIs (avaliados no DF) ----
    kpis: List[KPI] = []
    for k in out.get("kpis", [])[:6]:
        plan = KPIPlan(**k)
        try:
            val = _eval_kpi_expr(plan.value_expr, nds)
        except Exception as e:
            _write_json(log_dir / f"suggest_ai-kpi_error-{body.normalized_dataset_id}-{_ts()}.json",
                        {"kpi": k, "error": str(e)})
            raise HTTPException(status_code=400, detail=f"Falha ao calcular KPI '{plan.name}': {e}")
        value, unit = _fmt_value(val, plan.fmt)
        kpis.append(KPI(name=plan.name, value=float(value), unit=unit))

    # ---- Charts (séries geradas do DF; plano vem da IA) ----
    agg_mode = (body.agg_mode or DEFAULT_AGG_MODE or "groupby").strip().lower()
    if agg_mode not in ("resample", "groupby"):
        agg_mode = "groupby"
    drop_all_zero = DEFAULT_DROP_ALL_ZERO if body.drop_all_zero is None else bool(body.drop_all_zero)

    charts: List[ChartSpec] = []
    date_col = _find_date_col(nds)

    # DEBUG de agregação (prova dos meses e somatórios)
    if date_col:
        debug_cols: List[str] = []
        for ch in out.get("charts", []):
            for s in (ch.get("series") or []):
                if s.get("key") in nds.columns and s["key"] not in debug_cols:
                    debug_cols.append(s["key"])
            if ch.get("yKey") and ch["yKey"] in nds.columns and ch["yKey"] not in debug_cols:
                debug_cols.append(ch["yKey"])
            if ch.get("valueKey") and ch["valueKey"] in nds.columns and ch["valueKey"] not in debug_cols:
                debug_cols.append(ch["valueKey"])
        agg_dbg = monthly_aggregate(
            nds, date_col,
            debug_cols or [c for c in nds.columns if c != date_col and nds[c].dtype.kind in "if"],
            mode=agg_mode, drop_all_zero=False
        )
        _write_json(log_dir / f"agg-debug-{body.normalized_dataset_id}-{_ts()}.json", {
            "date_col": date_col,
            "agg_mode": agg_mode,
            "drop_all_zero": drop_all_zero,
            "months": agg_dbg["month"].tolist() if not agg_dbg.empty else [],
            "head": agg_dbg.head(24).to_dict(orient="records")
        })

    for ch in out.get("charts", [])[:4]:
        plan = ChartPlan(**ch)
        ctype = plan.type.lower()
        data: List[Dict[str, Any]] = []

        # LINE / AREA
        if ctype in ("line", "area"):
            x = plan.xKey or date_col
            if not x or x not in nds.columns or not pd.api.types.is_datetime64_any_dtype(nds[x]):
                raise HTTPException(status_code=400, detail=f"Gráfico '{plan.title}' requer coluna de data válida")
            if not plan.series:
                continue
            cols = [s.key for s in plan.series if s.key in nds.columns]
            if not cols:
                continue
            agg = monthly_aggregate(nds, date_col=x, cols=cols, mode=agg_mode, drop_all_zero=drop_all_zero)
            for _, r in agg.iterrows():
                row = {"month": r["month"]}
                for key in cols:
                    row[key] = float(r.get(key, 0.0))
                data.append(row)
            charts.append(ChartSpec(
                type=ctype, title=plan.title, data=data, xKey="month",
                series=[ChartSeries(key=s.key, label=s.label, dashed=s.dashed) for s in plan.series if s.key in cols]
            ))
            continue

        # BAR / STACKED BAR (Top N)
        if ctype in ("bar", "stacked_bar"):
            if not (plan.xKey and plan.yKey):
                continue
            x, y = plan.xKey, plan.yKey
            if x not in nds.columns or y not in nds.columns:
                raise HTTPException(status_code=400, detail=f"Gráfico '{plan.title}': colunas não encontradas")
            topN = plan.topN or 5
            agg = nds.groupby(x)[y].sum().sort_values(ascending=False).head(topN).reset_index()
            data = [{str(x): str(r[x]), str(y): float(r[y])} for _, r in agg.iterrows()]
            charts.append(ChartSpec(type="bar", title=plan.title, data=data, xKey=str(x), yKey=str(y)))
            continue

        # PIE / DONUT (composição)
        if ctype in ("pie", "donut"):
            if not (plan.categoryKey and plan.valueKey):
                continue
            a, b = plan.categoryKey, plan.valueKey
            if a not in nds.columns or b not in nds.columns:
                raise HTTPException(status_code=400, detail=f"Gráfico '{plan.title}': colunas não encontradas")
            agg = nds.groupby(a)[b].sum().reset_index()
            agg.columns = ["name", "value"]
            data = [{"name": str(r["name"]), "value": float(r["value"])} for _, r in agg.iterrows()]
            charts.append(ChartSpec(type=("donut" if ctype == "donut" else "pie"),
                                    title=plan.title, data=data, categoryKey="name", valueKey="value"))
            continue

        raise HTTPException(status_code=400, detail=f"Tipo de gráfico/parâmetros inválidos em '{plan.title}'")

    # ---- Insights (texto da IA) ----
    insights: List[Insight] = []
    for ins in out.get("insights", [])[:4]:
        insights.append(Insight(
            type=str(ins.get("type", "info")),
            title=str(ins.get("title", "Insight")),
            message=str(ins.get("message", "")),
        ))

    doc = DashboardDoc(
        dataset_id=body.normalized_dataset_id,
        kpis=kpis,
        charts=charts,
        insights=insights,
        filters={"time_grain": "month"} if date_col else None,
        version=datetime.utcnow().strftime("%Y.%m.%d"),
    )

    # Persistir dashboard final
    DASHBOARDS[body.normalized_dataset_id] = json.loads(doc.model_dump_json())
    _write_json(DASH_DIR / f"{body.normalized_dataset_id}.json", DASHBOARDS[body.normalized_dataset_id])

    # Logs do plano e do dashboard
    _write_json(log_dir / f"suggest_ai-plan-{body.normalized_dataset_id}-{_ts()}.json", out)
    _write_json(log_dir / f"suggest_ai-dashboard-{body.normalized_dataset_id}-{_ts()}.json", DASHBOARDS[body.normalized_dataset_id])

    return doc


# desabilita rota antiga sem IA
class SuggestBody(BaseModel):
    normalized_dataset_id: str

@app.post("/api/dash/suggest")
def suggest_disabled(body: SuggestBody):
    raise HTTPException(status_code=410, detail="Use /api/dash/suggest_ai")


# =========================
# Latest — lê do disco se necessário
# =========================

@app.get("/api/dash/latest/{normalized_dataset_id}", response_model=DashboardDoc)
def latest(normalized_dataset_id: str):
    doc = DASHBOARDS.get(normalized_dataset_id)
    if not doc:
        disk = DASH_DIR / f"{normalized_dataset_id}.json"
        if not disk.exists():
            raise HTTPException(status_code=404, detail="dashboard não encontrado")
        doc = _read_json(disk)
        DASHBOARDS[normalized_dataset_id] = doc
    return doc


# =========================
# Pipeline único (upload -> detect -> normalize -> suggest)
# =========================

class PipelineOptions(BaseModel):
    model: Optional[str] = None
    agg_mode: Optional[str] = None         # "resample" | "groupby"
    drop_all_zero: Optional[bool] = None   # None -> usa DEFAULT_DROP_ALL_ZERO

class PipelineResult(BaseModel):
    dataset_id: str
    normalized_dataset_id: str
    dashboard: DashboardDoc
    stages: List[Dict[str, Any]]  # [{name, start, end, meta}]

def _stage(name: str) -> Dict[str, Any]:
    return {"name": name, "start": datetime.utcnow().isoformat() + "Z", "end": None, "meta": {}}

def _finish(stage: Dict[str, Any], meta: Dict[str, Any] = None):
    stage["end"] = datetime.utcnow().isoformat() + "Z"
    if meta:
        stage["meta"] = meta

@app.post("/api/pipeline/auto", response_model=PipelineResult)
async def pipeline_auto(
    file: UploadFile = File(...),
    model: Optional[str] = Form(default=None),
    agg_mode: Optional[str] = Form(default=None),
    drop_all_zero: Optional[bool] = Form(default=None),
):
    stages: List[Dict[str, Any]] = []

    # 1) Upload
    st_up = _stage("upload")
    stages.append(st_up)
    contents = await file.read()
    dataset_id = f"ds_{uuid.uuid4().hex[:6]}"
    log_dir = LOGS_DIR / dataset_id
    log_dir.mkdir(parents=True, exist_ok=True)
    upload_path = UPLOAD_DIR / f"{dataset_id}.csv"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with open(upload_path, "wb") as f:
        f.write(contents)
    try:
        df = pd.read_csv(upload_path)
    except Exception:
        df = pd.read_csv(upload_path, sep=";")
    DATASETS[dataset_id] = df

    preview = {
        "dataset_id": dataset_id,
        "filename": file.filename,
        "rows": int(len(df)),
        "columns": list(map(str, df.columns)),
        "sample_rows": df.head(5).fillna("").astype(str).to_dict(orient="records"),
    }
    _write_json(log_dir / f"upload-preview-{_ts()}.json", preview)
    _finish(st_up, {"dataset_id": dataset_id, "rows": int(len(df)), "filename": file.filename})

    # 2) Detect (IA)
    st_det = _stage("detect_ai")
    stages.append(st_det)
    sample_rows = df.head(5).astype(str).to_dict(orient="records")
    backend_inferred = [{"name": str(c), "dtype": "unknown"} for c in df.columns]
    user = DETECT_USER_TEMPLATE.format(
        filename=file.filename,
        sample_rows=json.dumps(sample_rows, ensure_ascii=False),
        backend_inferred=json.dumps(backend_inferred, ensure_ascii=False)
    )
    messages = [{"role": "system", "content": DETECT_SYSTEM},
                {"role": "user", "content": user}]
    _write_json(log_dir / f"detect_ai-request-{_ts()}.json", {"model": model, "messages": messages})
    det = await chat_json(messages, model=model, max_tokens=2000)
    _write_json(log_dir / f"detect_ai-response-{_ts()}.json", det)
    if "_raw" in det or "columns" not in det:
        raise HTTPException(status_code=502, detail="detect_ai não retornou JSON válido")
    _finish(st_det, {"columns": det["columns"]})

    # 3) Normalize
    st_norm = _stage("normalize")
    stages.append(st_norm)
    norm = df.copy()
    dtype_map = {c["name"]: c["dtype"] for c in det["columns"]}
    for c in norm.columns:
        dt = dtype_map.get(str(c), "unknown")
        if dt == "date":
            norm[c] = _parse_date_smart(norm[c])
        elif dt in ("currency","percent","number"):
            norm[c] = norm[c].apply(_to_number_ptbr)
    normalized_dataset_id = f"nds_{uuid.uuid4().hex[:6]}"
    NORMALIZED[normalized_dataset_id] = norm
    _save_parquet(norm, NORM_DIR / f"{normalized_dataset_id}.parquet")

    # meta semântico
    sem_meta = []
    for col in det["columns"]:
        sem_val = col.get("semantic")
        if isinstance(sem_val, str) and sem_val.strip().lower() == "null":
            sem_val = None
        fmt_val = col.get("format")
        if isinstance(fmt_val, str) and fmt_val.strip().lower() == "null":
            fmt_val = None
        sem_meta.append({"name": col["name"], "dtype": col["dtype"], "semantic": sem_val, "format": fmt_val})
    _write_json(NORM_DIR / f"{normalized_dataset_id}.meta.json", {
        "dataset_id": dataset_id, "normalized_dataset_id": normalized_dataset_id, "columns": sem_meta
    })
    _write_json(log_dir / f"normalize-{normalized_dataset_id}-{_ts()}.json", {
        "normalized_dataset_id": normalized_dataset_id,
        "rows": int(len(norm)),
        "dtype_map": dtype_map,
    })
    _finish(st_norm, {"normalized_dataset_id": normalized_dataset_id, "rows": int(len(norm))})

    # 4) Suggest (IA) + cálculo determinístico
    st_sug = _stage("suggest_ai")
    stages.append(st_sug)
    meta = {"columns": sem_meta}
    prof = profile_dataframe(norm)
    user_sug = SUGGEST_USER_TEMPLATE.format(
        columns=json.dumps(prof["columns"], ensure_ascii=False),
        stats=json.dumps(prof["stats"], ensure_ascii=False)[:8000],
        time_coverage=json.dumps(prof["time_coverage"], ensure_ascii=False),
        semantic_hints=json.dumps(meta["columns"], ensure_ascii=False)
    )
    sug_msgs = [{"role":"system","content": SUGGEST_SYSTEM},
                {"role":"user","content": user_sug}]
    _write_json(log_dir / f"suggest_ai-request-{normalized_dataset_id}-{_ts()}.json", {"model": model, "messages": sug_msgs})
    plan = await chat_json(sug_msgs, model=model, max_tokens=3000)
    _write_json(log_dir / f"suggest_ai-plan-{normalized_dataset_id}-{_ts()}.json", plan)
    if "_raw" in plan:
        raise HTTPException(status_code=502, detail="suggest_ai não retornou JSON válido")

    # KPIs
    kpis: List[KPI] = []
    for k in plan.get("kpis", [])[:6]:
        plan_k = KPIPlan(**k)
        val = _eval_kpi_expr(plan_k.value_expr, norm)
        value, unit = _fmt_value(val, plan_k.fmt)
        kpis.append(KPI(name=plan_k.name, value=float(value), unit=unit))

    # defaults (respeita .env/payload)
    agg_mode_eff = (agg_mode or DEFAULT_AGG_MODE or "groupby").strip().lower() if agg_mode else (DEFAULT_AGG_MODE or "groupby")
    if agg_mode_eff not in ("resample","groupby"):
        agg_mode_eff = "groupby"
    drop_eff = DEFAULT_DROP_ALL_ZERO if drop_all_zero is None else bool(drop_all_zero)

    # DEBUG de agregação (prova dos meses)
    date_col = _find_date_col(norm)
    if date_col:
        debug_cols: List[str] = []
        for ch in plan.get("charts", []):
            for s in (ch.get("series") or []):
                if s.get("key") in norm.columns and s["key"] not in debug_cols:
                    debug_cols.append(s["key"])
            if ch.get("yKey") and ch["yKey"] in norm.columns and ch["yKey"] not in debug_cols:
                debug_cols.append(ch["yKey"])
            if ch.get("valueKey") and ch["valueKey"] in norm.columns and ch["valueKey"] not in debug_cols:
                debug_cols.append(ch["valueKey"])
        agg_dbg = monthly_aggregate(norm, date_col, debug_cols or [c for c in norm.columns if c != date_col and norm[c].dtype.kind in "if"], mode=agg_mode_eff, drop_all_zero=False)
        _write_json(log_dir / f"agg-debug-{normalized_dataset_id}-{_ts()}.json", {
            "date_col": date_col,
            "agg_mode": agg_mode_eff,
            "drop_all_zero": drop_eff,
            "months": agg_dbg["month"].tolist() if not agg_dbg.empty else [],
            "head": agg_dbg.head(24).to_dict(orient="records")
        })

    charts: List[ChartSpec] = []
    for ch in plan.get("charts", [])[:4]:
        plan_ch = ChartPlan(**ch)
        ctype = plan_ch.type.lower()
        data: List[Dict[str, Any]] = []

        if ctype in ("line","area"):
            x = plan_ch.xKey or date_col
            if not x or x not in norm.columns or not pd.api.types.is_datetime64_any_dtype(norm[x]):
                raise HTTPException(status_code=400, detail=f"Gráfico '{plan_ch.title}' requer coluna de data válida")
            if not plan_ch.series:
                continue
            cols = [s.key for s in plan_ch.series if s.key in norm.columns]
            if not cols:
                continue
            agg = monthly_aggregate(norm, x, cols, mode=agg_mode_eff, drop_all_zero=drop_eff)
            for _, r in agg.iterrows():
                row = {"month": r["month"]}
                for key in cols:
                    row[key] = float(r.get(key, 0.0))
                data.append(row)
            charts.append(ChartSpec(
                type=ctype, title=plan_ch.title, data=data, xKey="month",
                series=[ChartSeries(key=s.key, label=s.label, dashed=s.dashed) for s in plan_ch.series if s.key in cols]
            ))

        elif ctype in ("bar","stacked_bar") and plan_ch.xKey and plan_ch.yKey:
            x, y = plan_ch.xKey, plan_ch.yKey
            if x not in norm.columns or y not in norm.columns:
                raise HTTPException(status_code=400, detail=f"Gráfico '{plan_ch.title}': colunas não encontradas")
            topN = plan_ch.topN or 5
            agg = norm.groupby(x)[y].sum().sort_values(ascending=False).head(topN).reset_index()
            data = [{str(x): str(r[x]), str(y): float(r[y])} for _, r in agg.iterrows()]
            charts.append(ChartSpec(type="bar", title=plan_ch.title, data=data, xKey=str(x), yKey=str(y)))

        elif ctype in ("pie","donut") and plan_ch.categoryKey and plan_ch.valueKey:
            a, b = plan_ch.categoryKey, plan_ch.valueKey
            if a not in norm.columns or b not in norm.columns:
                raise HTTPException(status_code=400, detail=f"Gráfico '{plan_ch.title}': colunas não encontradas")
            agg = norm.groupby(a)[b].sum().reset_index()
            agg.columns = ["name", "value"]
            data = [{"name": str(r["name"]), "value": float(r["value"])} for _, r in agg.iterrows()]
            charts.append(ChartSpec(type=("donut" if ctype == "donut" else "pie"),
                                    title=plan_ch.title, data=data, categoryKey="name", valueKey="value"))
        else:
            raise HTTPException(status_code=400, detail=f"Gráfico inválido em '{plan_ch.title}'")

    insights: List[Insight] = []
    for ins in plan.get("insights", [])[:4]:
        insights.append(Insight(type=str(ins.get("type","info")),
                                title=str(ins.get("title","Insight")),
                                message=str(ins.get("message",""))))

    doc = DashboardDoc(
        dataset_id=normalized_dataset_id, kpis=kpis, charts=charts, insights=insights,
        filters={"time_grain":"month"} if date_col else None,
        version=datetime.utcnow().strftime("%Y.%m.%d")
    )

    DASHBOARDS[normalized_dataset_id] = json.loads(doc.model_dump_json())
    _write_json(DASH_DIR / f"{normalized_dataset_id}.json", DASHBOARDS[normalized_dataset_id])

    _finish(st_sug, {"kpis": len(kpis), "charts": len(charts), "insights": len(insights)})

    return PipelineResult(
        dataset_id=dataset_id,
        normalized_dataset_id=normalized_dataset_id,
        dashboard=doc,
        stages=stages
    )
