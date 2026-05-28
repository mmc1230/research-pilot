from pathlib import Path
from typing import Any

import pandas as pd

from app.tools.tool_registry import register_tool


METRIC_KEYWORDS = [
    "r2",
    "rmse",
    "mae",
    "mse",
    "mean",
    "std",
    "q95",
    "failure_prob",
    "accuracy",
    "loss",
]
LOWER_IS_BETTER = ["rmse", "mae", "mse", "loss", "std", "q95", "failure_prob"]
HIGHER_IS_BETTER = ["r2", "accuracy", "score", "auc", "f1"]


def _read_csv(csv_path: str) -> pd.DataFrame:
    path = Path(csv_path)
    if not path.exists() or not path.is_file():
        raise FileNotFoundError(f"CSV not found: {csv_path}")
    try:
        return pd.read_csv(path)
    except Exception as exc:
        raise ValueError(f"Failed to read CSV {csv_path}: {exc}") from exc


def detect_metric_columns(df: pd.DataFrame) -> list[str]:
    metrics = []
    for col in df.columns:
        lower = col.lower()
        if any(keyword in lower for keyword in METRIC_KEYWORDS) and pd.api.types.is_numeric_dtype(df[col]):
            metrics.append(col)
    return metrics


def _direction(metric: str) -> str:
    lower = metric.lower()
    if any(key in lower for key in LOWER_IS_BETTER):
        return "lower"
    if any(key in lower for key in HIGHER_IS_BETTER):
        return "higher"
    return "unknown"


@register_tool(
    name="load_csv",
    description="Load a CSV and return schema, row count, data types, and missing values.",
    args_schema={"csv_path": "string"},
)
def load_csv(csv_path: str) -> dict[str, Any]:
    df = _read_csv(csv_path)
    return {
        "csv_path": csv_path,
        "rows": int(len(df)),
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
        "missing_values": {col: int(df[col].isna().sum()) for col in df.columns},
        "metric_columns": detect_metric_columns(df),
        "preview": df.head(5).to_dict(orient="records"),
    }


@register_tool(
    name="analyze_metrics_csv",
    description="Analyze experiment metrics, best rows, grouped summaries, and possible anomalies.",
    args_schema={"csv_path": "string"},
)
def analyze_metrics_csv(csv_path: str) -> dict[str, Any]:
    df = _read_csv(csv_path)
    metrics = detect_metric_columns(df)
    categorical_cols = [
        col for col in df.columns if not pd.api.types.is_numeric_dtype(df[col]) and df[col].nunique(dropna=True) <= 50
    ]
    model_col = next((c for c in df.columns if c.lower() in {"model", "method", "algorithm", "name"}), None)

    best_by_metric = {}
    for metric in metrics:
        direction = _direction(metric)
        series = pd.to_numeric(df[metric], errors="coerce")
        if series.dropna().empty:
            continue
        idx = series.idxmin() if direction == "lower" else series.idxmax()
        best_by_metric[metric] = {
            "direction": direction,
            "best_index": int(idx),
            "best_value": float(series.loc[idx]),
            "row": df.loc[idx].to_dict(),
        }

    grouped_summary = {}
    group_col = model_col or (categorical_cols[0] if categorical_cols else None)
    if group_col and metrics:
        grouped = df.groupby(group_col)[metrics].mean(numeric_only=True).round(6)
        grouped_summary = grouped.reset_index().to_dict(orient="records")

    anomalies = []
    for metric in metrics:
        values = pd.to_numeric(df[metric], errors="coerce").dropna()
        if len(values) < 4:
            continue
        q1, q3 = values.quantile(0.25), values.quantile(0.75)
        iqr = q3 - q1
        lower, upper = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outlier_rows = df[(pd.to_numeric(df[metric], errors="coerce") < lower) | (pd.to_numeric(df[metric], errors="coerce") > upper)]
        for idx, row in outlier_rows.head(10).iterrows():
            anomalies.append({"metric": metric, "index": int(idx), "value": row[metric], "row": row.to_dict()})

    return {
        "csv_path": csv_path,
        "rows": int(len(df)),
        "metric_columns": metrics,
        "group_column": group_col,
        "best_by_metric": best_by_metric,
        "grouped_summary": grouped_summary,
        "anomalies": anomalies,
        "schema": load_csv(csv_path),
    }
