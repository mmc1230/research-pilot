from pathlib import Path

from app.tools.csv_tools import analyze_metrics_csv, load_csv


def test_csv_schema_and_metrics(tmp_path: Path):
    csv_path = tmp_path / "results.csv"
    csv_path.write_text(
        "model,target,R2,RMSE,MAE\n"
        "a,NO,0.91,0.12,0.08\n"
        "b,NO,0.88,0.10,0.07\n"
        "a,C2H4,0.81,0.22,0.15\n",
        encoding="utf-8",
    )
    schema = load_csv(str(csv_path))
    assert schema["rows"] == 3
    assert "RMSE" in schema["metric_columns"]

    analysis = analyze_metrics_csv(str(csv_path))
    assert analysis["best_by_metric"]["RMSE"]["best_value"] == 0.10
    assert analysis["best_by_metric"]["R2"]["best_value"] == 0.91
