from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

try:
    from query_parser import parse_query_with_vlm
except ImportError:
    from .query_parser import parse_query_with_vlm  # type: ignore


DEFAULT_KEEP_FIELDS = [
    "scan_id",
    "target_id",
    "caption",
    "obj_name",
    "program",
    "easy",
    "view_dep",
    "scene_id",
    "object_id",
    "object_name",
    "description",
]


def _stable_target_object(row: dict[str, Any], analysis: dict[str, Any]) -> str:
    object_name = str(row.get("object_name", "") or row.get("obj_name", "")).strip()
    if object_name:
        return object_name
    return str(analysis.get("target_object", "") or "").strip()


def analyze_query(raw_query: str) -> dict[str, Any]:
    raw_query = str(raw_query or "").strip()
    if not raw_query:
        return {
            "raw_query": raw_query,
            "target_object": "",
            "target_attributes": [],
            "reference_object": "",
            "reference_attributes": [],
            "relation": "",
        }

    max_attempts = 2
    last_result: dict[str, Any] | None = None
    for attempt in range(max_attempts):
        result = parse_query_with_vlm(raw_query)
        last_result = result

        target_object = str(result.get("target_object", "") or "").strip()
        if target_object:
            return result

        print(
            f"[QueryPreprocess] retry analyze because target_object is empty "
            f"attempt={attempt + 1}/{max_attempts} query={raw_query}"
        )

    if last_result is not None:
        return last_result
    raise RuntimeError("Query analysis did not produce any result")


def preprocess_dataset(
    input_path: Path,
    output_path: Path,
    *,
    query_field: str = "caption",
) -> None:
    data = json.loads(input_path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Expected top-level list dataset")

    enriched_rows: list[dict[str, Any]] = []
    for index, row in enumerate(data):
        if not isinstance(row, dict):
            raise ValueError(f"Row {index} is not an object")

        raw_query = str(row.get(query_field, "") or "").strip()
        analysis = analyze_query(raw_query)

        enriched = {key: row[key] for key in DEFAULT_KEEP_FIELDS if key in row}
        enriched["target_object"] = _stable_target_object(row, analysis)
        enriched["query_analysis"] = analysis
        enriched_rows.append(enriched)

        print(
            f"[QueryPreprocess] index={index} "
            f"scan_id={row.get('scan_id', row.get('scene_id', ''))} "
            f"target_id={row.get('target_id', row.get('object_id', ''))} "
            f"query={raw_query}"
        )

    output_path.write_text(
        json.dumps(enriched_rows, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"saved={output_path}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Precompute query analysis for ScanRefer-style datasets."
    )
    parser.add_argument("--input", default=None, help="Input dataset JSON path")
    parser.add_argument("--output", default=None, help="Output dataset JSON path")
    parser.add_argument(
        "--query-field",
        default="caption",
        help="Field name containing the natural-language query",
    )
    parser.add_argument(
        "--query",
        default=None,
        help="Optional single-query test mode; if provided, dataset mode is skipped",
    )
    args = parser.parse_args()

    if args.query is not None:
        result = analyze_query(args.query)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    if not args.input or not args.output:
        raise ValueError("Dataset mode requires --input and --output")

    preprocess_dataset(
        Path(args.input),
        Path(args.output),
        query_field=str(args.query_field),
    )


if __name__ == "__main__":
    main()
