import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def write_mock_csv(output_path: str | Path, table_name: str = "alfabetizacao") -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    rows = [
        {
            "NU_ANO": 2025,
            "CO_UF": 11,
            "SG_UF": "RO",
            "ID_ALUNO": 10000001,
            "TP_SERIE": 2,
            "ID_ESCOLA": 11000001,
            "TP_DEPENDENCIA": 2,
            "CO_MUNICIPIO": 1100023,
            "NO_MUNICIPIO": "Ariquemes",
            "IN_PRESENCA": 1,
            "VL_PROFICIENCIA": 650.123,
            "IN_ALFABETIZADO": 1,
            "table_name": table_name,
        }
    ]

    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    return path


def append_mock_message(output_path: str | Path, payload: Dict[str, Any]) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False))
        handle.write("\n")

    return path


def read_mock_messages(output_path: str | Path) -> List[Dict[str, Any]]:
    path = Path(output_path)
    if not path.exists():
        return []

    with path.open("r", encoding="utf-8") as handle:
        return [json.loads(line) for line in handle if line.strip()]
