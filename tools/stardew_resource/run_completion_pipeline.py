from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover - optional local validation dependency
    Image = None
    ImageDraw = None


VISUAL_CATEGORIES = {
    "Animals",
    "Buildings",
    "Characters",
    "Effects",
    "LooseSprites",
    "Maps",
    "Minigames",
    "Portraits",
    "TerrainFeatures",
    "TileSheets",
}

OUTPUT_DATE = "20260624"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build FarmOld Stardew resource completion outputs.")
    parser.add_argument(
        "--farmold-root",
        default=str(Path(__file__).resolve().parents[2]),
        help="FarmOld repository root.",
    )
    parser.add_argument(
        "--output-root",
        default="",
        help="Completion output root. Defaults to _local_exports/stardew_resource_completion_20260624.",
    )
    parser.add_argument(
        "--skip-decode",
        action="store_true",
        help="Skip Node XNB decoding and reuse an existing xnb_decode_index.csv if present.",
    )
    return parser.parse_args()


def now_local() -> str:
    return datetime.now().replace(microsecond=0).isoformat()


def posix(path: str | Path) -> str:
    return str(path).replace("\\", "/")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str] | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        seen: list[str] = []
        for row in rows:
            for key in row:
                if key not in seen:
                    seen.append(key)
        fieldnames = seen
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def md5_file(path: Path) -> str:
    digest = hashlib.md5()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest().upper()


def safe_relative(path: Path, root: Path) -> str:
    try:
        return posix(path.relative_to(root))
    except ValueError:
        return posix(path)


def no_ext(content_path: str) -> str:
    lowered = content_path.lower()
    for ext in (".xnb", ".fnt", ".json"):
        if lowered.endswith(ext):
            return content_path[: -len(ext)]
    return content_path


def source_type_for(category: str, content_path: str) -> str:
    if content_path.lower().endswith(".mgfxo"):
        return "ShaderEffectBinary"
    if category == "Data":
        return "DataConfig"
    if category == "Strings":
        return "StringsText"
    if category == "Fonts":
        return "Font"
    if category == "XACT":
        return "AudioBank"
    if category == "VolcanoLayouts":
        return "DataOrLayout"
    if category == "Maps":
        return "MapTilesheetOrImage"
    if category in VISUAL_CATEGORIES:
        return "VisualSprite"
    if content_path == "ContentHashes.json":
        return "HashIndex"
    return "Unknown"


def validate_content_hashes(content_root: Path, content_hash_rows: list[dict[str, str]]) -> dict[str, Any]:
    missing: list[dict[str, str]] = []
    mismatches: list[dict[str, str]] = []
    checked = 0
    for row in content_hash_rows:
        relative = row["AssetPath"]
        expected = row["Hash"].upper()
        source = content_root / Path(relative)
        if not source.exists():
            missing.append({"AssetPath": relative, "ExpectedHash": expected})
            continue
        checked += 1
        actual = md5_file(source)
        if actual != expected:
            mismatches.append({"AssetPath": relative, "ExpectedHash": expected, "ActualHash": actual})
    return {
        "checked_hash_files": checked,
        "missing_source_files": len(missing),
        "hash_mismatches": len(mismatches),
        "missing": missing,
        "mismatches": mismatches,
    }


def validate_images(image_root: Path) -> dict[str, Any]:
    image_extensions = {".png", ".jpg", ".jpeg", ".bmp", ".gif"}
    files = [p for p in image_root.rglob("*") if p.is_file()]
    image_files = [p for p in files if p.suffix.lower() in image_extensions]
    zero_byte = [p for p in files if p.stat().st_size == 0]
    decode_failures: list[dict[str, str]] = []
    image_details: list[dict[str, Any]] = []

    if Image is not None:
        for path in image_files:
            try:
                with Image.open(path) as image:
                    image.verify()
                with Image.open(path) as image:
                    image_details.append(
                        {
                            "path": posix(path),
                            "width": image.width,
                            "height": image.height,
                            "mode": image.mode,
                        }
                    )
            except Exception as exc:
                decode_failures.append({"path": posix(path), "error": f"{type(exc).__name__}: {exc}"})

    return {
        "total_files": len(files),
        "image_files": len(image_files),
        "zero_byte_files": len(zero_byte),
        "image_decode_failures": len(decode_failures),
        "pillow_available": Image is not None,
        "zero_byte_paths": [posix(p) for p in zero_byte],
        "decode_failures": decode_failures,
        "image_details": image_details,
    }


def validate_json_tree(root: Path) -> dict[str, Any]:
    files = sorted(root.rglob("*.json"))
    failures: list[dict[str, str]] = []
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception as exc:
            failures.append({"path": posix(path), "error": f"{type(exc).__name__}: {exc}"})
    return {"json_files": len(files), "json_parse_failures": len(failures), "failures": failures}


def build_xnb_decode_input(farmold_root: Path, output_root: Path) -> list[dict[str, str]]:
    content_root = farmold_root / "Content"
    exports_root = farmold_root / "_local_exports"
    items: list[dict[str, str]] = []

    visual_csv = exports_root / "stardew_visual_resource_inventory_20260624" / "visual_resource_inventory.csv"
    for row in read_csv(visual_csv):
        if row.get("Extension", "").lower() != ".xnb":
            continue
        source_path = Path(row["SourcePath"])
        content_path = safe_relative(source_path, content_root)
        items.append(
            {
                "content_path": content_path,
                "category": row["Category"],
                "source_type": "VisualSprite",
                "source_path": str(source_path),
                "output_group": "decoded_visual",
            }
        )

    fonts_csv = exports_root / "stardew_fonts_inventory_20260624" / "fonts_file_inventory.csv"
    for row in read_csv(fonts_csv):
        if row.get("Extension", "").lower() != ".xnb":
            continue
        source_path = Path(row["SourcePath"])
        items.append(
            {
                "content_path": safe_relative(source_path, content_root),
                "category": "Fonts",
                "source_type": "Font",
                "source_path": str(source_path),
                "output_group": "decoded_fonts",
            }
        )

    volcano_csv = exports_root / "stardew_volcanolayouts_exports_20260624" / "volcanolayouts_file_inventory.csv"
    for row in read_csv(volcano_csv):
        if row.get("Extension", "").lower() != ".xnb":
            continue
        source_path = Path(row["SourcePath"])
        items.append(
            {
                "content_path": safe_relative(source_path, content_root),
                "category": "VolcanoLayouts",
                "source_type": "DataOrLayout",
                "source_path": str(source_path),
                "output_group": "decoded_volcanolayouts",
            }
        )

    write_json(output_root / "xnb_decode_input.json", {"items": items})
    return items


def run_xnb_decoder(farmold_root: Path, output_root: Path) -> dict[str, Any]:
    script = farmold_root / "tools" / "stardew_resource" / "export_xnb_assets.mjs"
    command = [
        "node",
        str(script),
        "--farmold-root",
        str(farmold_root),
        "--input",
        str(output_root / "xnb_decode_input.json"),
        "--output",
        str(output_root),
    ]
    result = subprocess.run(
        command,
        cwd=str(farmold_root),
        text=True,
        capture_output=True,
        check=False,
    )
    (output_root / "xnb_decode_stdout.log").write_text(result.stdout, encoding="utf-8")
    (output_root / "xnb_decode_stderr.log").write_text(result.stderr, encoding="utf-8")
    if result.returncode != 0:
        raise RuntimeError(f"XNB decoder failed with exit code {result.returncode}; see xnb_decode_stderr.log")
    return json.loads((output_root / "xnb_decode_summary.json").read_text(encoding="utf-8"))


def parse_font_descriptors(farmold_root: Path, output_root: Path) -> dict[str, Any]:
    content_root = farmold_root / "Content"
    rows: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for path in sorted((content_root / "Fonts").rglob("*.fnt")):
        relative = safe_relative(path, content_root)
        try:
            root = ET.parse(path).getroot()
            info = root.find("info")
            common = root.find("common")
            chars = root.find("chars")
            pages = root.find("pages")
            rows.append(
                {
                    "content_path": relative,
                    "face": info.get("face") if info is not None else "",
                    "size": info.get("size") if info is not None else "",
                    "lineHeight": common.get("lineHeight") if common is not None else "",
                    "scaleW": common.get("scaleW") if common is not None else "",
                    "scaleH": common.get("scaleH") if common is not None else "",
                    "pages": pages.get("count") if pages is not None else "",
                    "chars": chars.get("count") if chars is not None else "",
                    "bytes": path.stat().st_size,
                    "source_path": str(path),
                    "status": "parsed",
                }
            )
        except Exception as exc:
            failures.append({"content_path": relative, "error": f"{type(exc).__name__}: {exc}"})
    write_csv(output_root / "font_descriptor_index.csv", rows)
    write_csv(output_root / "font_descriptor_failures.csv", failures, ["content_path", "error"])
    return {
        "fnt_descriptors": len(rows) + len(failures),
        "fnt_descriptors_parsed": len(rows),
        "fnt_descriptor_failures": len(failures),
    }


def copy_reference_indexes(farmold_root: Path, output_root: Path) -> dict[str, str]:
    exports_root = farmold_root / "_local_exports"
    references = output_root / "reference_indexes"
    references.mkdir(parents=True, exist_ok=True)
    files = {
        "data_export_index.csv": exports_root / "stardew_data_exports_20260624" / "data_export_index.csv",
        "data_export_failures.csv": exports_root / "stardew_data_exports_20260624" / "data_export_failures.csv",
        "strings_export_index.csv": exports_root / "stardew_strings_exports_20260624" / "strings_export_index.csv",
        "strings_export_failures.csv": exports_root / "stardew_strings_exports_20260624" / "strings_export_failures.csv",
        "map_summary.csv": exports_root / "stardew_maps_20260623" / "map_summary.csv",
        "tilesheet_summary.csv": exports_root / "stardew_maps_20260623" / "tilesheet_summary.csv",
        "layer_summary.csv": exports_root / "stardew_maps_20260623" / "layer_summary.csv",
        "xact_file_inventory.csv": exports_root / "stardew_xact_audio_inventory_20260624" / "xact_file_inventory.csv",
        "xact_ascii_strings.csv": exports_root / "stardew_xact_audio_inventory_20260624" / "xact_ascii_strings.csv",
        "fonts_file_inventory.csv": exports_root / "stardew_fonts_inventory_20260624" / "fonts_file_inventory.csv",
        "content_hashes_index.csv": exports_root / "stardew_content_hashes_inventory_20260624" / "content_hashes_index.csv",
    }
    copied: dict[str, str] = {}
    for name, source in files.items():
        target = references / name
        shutil.copy2(source, target)
        copied[name] = posix(target.relative_to(output_root))
    return copied


def build_contact_sheets(output_root: Path, decode_rows: list[dict[str, str]]) -> dict[str, Any]:
    if Image is None:
        return {"created": 0, "skipped": True, "reason": "Pillow is not available"}

    by_category: dict[str, list[Path]] = defaultdict(list)
    for row in decode_rows:
        if row.get("status") != "decoded":
            continue
        if row.get("extension", "").lower() != "png":
            continue
        if not row.get("output_relative_path", "").startswith("decoded_visual/"):
            continue
        by_category[row["category"]].append(output_root / Path(row["output_relative_path"]))

    contact_root = output_root / "contact_sheets"
    contact_root.mkdir(parents=True, exist_ok=True)
    created = 0
    details: list[dict[str, Any]] = []
    for category, paths in sorted(by_category.items()):
        thumbs = []
        for path in paths:
            try:
                with Image.open(path) as image:
                    image = image.convert("RGBA")
                    image.thumbnail((64, 64))
                    tile = Image.new("RGBA", (72, 72), (255, 255, 255, 0))
                    tile.alpha_composite(image, ((72 - image.width) // 2, (72 - image.height) // 2))
                    thumbs.append(tile)
            except Exception:
                continue
        if not thumbs:
            continue
        columns = min(20, max(1, math.ceil(math.sqrt(len(thumbs)))))
        rows = math.ceil(len(thumbs) / columns)
        sheet = Image.new("RGBA", (columns * 72, rows * 72), (32, 32, 32, 255))
        for index, thumb in enumerate(thumbs):
            x = (index % columns) * 72
            y = (index // columns) * 72
            sheet.alpha_composite(thumb, (x, y))
        sheet_path = contact_root / f"{category}.png"
        sheet.save(sheet_path)
        created += 1
        details.append(
            {
                "category": category,
                "images": len(thumbs),
                "contact_sheet": posix(sheet_path.relative_to(output_root)),
            }
        )
    write_csv(output_root / "contact_sheets.csv", details)
    return {"created": created, "skipped": False, "details": details}


def map_tilesheet_validation(farmold_root: Path, output_root: Path, content_paths: set[str]) -> dict[str, Any]:
    tilesheet_csv = farmold_root / "_local_exports" / "stardew_maps_20260623" / "tilesheet_summary.csv"
    rows = read_csv(tilesheet_csv)
    unknown: list[dict[str, str]] = []
    matrix: list[dict[str, str]] = []
    content_no_ext = {no_ext(path).lower() for path in content_paths}
    for row in rows:
        image_source = row.get("imageSource", "").replace("\\", "/").strip("/")
        normalized = image_source
        if normalized and normalized.lower() not in content_no_ext:
            unknown.append({"asset": row.get("asset", ""), "imageSource": image_source})
        matrix.append(
            {
                "map_asset": row.get("asset", ""),
                "sheet_id": row.get("id", ""),
                "image_source": image_source,
                "tile_width": row.get("tileWidth", ""),
                "tile_height": row.get("tileHeight", ""),
                "tile_count": row.get("tileCount", ""),
                "status": "known" if normalized.lower() in content_no_ext else "unknown",
            }
        )
    write_csv(output_root / "map_tilesheet_matrix.csv", matrix)
    write_csv(output_root / "map_tilesheet_unknown.csv", unknown, ["asset", "imageSource"])
    return {
        "tilesheet_reference_rows": len(rows),
        "unknown_referenced_tilesheet_count": len(unknown),
    }


def build_manifest(
    farmold_root: Path,
    output_root: Path,
    content_hash_rows: list[dict[str, str]],
    decode_rows: list[dict[str, str]],
    decode_failures: list[dict[str, str]],
    font_descriptor_rows: list[dict[str, str]],
) -> list[dict[str, Any]]:
    exports_root = farmold_root / "_local_exports"
    content_root = farmold_root / "Content"
    data_index = {row["Asset"]: row for row in read_csv(exports_root / "stardew_data_exports_20260624" / "data_export_index.csv")}
    strings_index = {
        row["Asset"]: row for row in read_csv(exports_root / "stardew_strings_exports_20260624" / "strings_export_index.csv")
    }
    map_index = {row["asset"]: row for row in read_csv(exports_root / "stardew_maps_20260623" / "map_summary.csv")}
    visual_index = {
        safe_relative(Path(row["SourcePath"]), content_root): row
        for row in read_csv(exports_root / "stardew_visual_resource_inventory_20260624" / "visual_resource_inventory.csv")
    }
    xact_index = {
        "XACT/" + row["Name"]: row
        for row in read_csv(exports_root / "stardew_xact_audio_inventory_20260624" / "xact_file_inventory.csv")
    }
    decoded_by_path: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in decode_rows:
        decoded_by_path[row["content_path"]].append(row)
    failed_by_path = {row["content_path"]: row for row in decode_failures}
    font_fnt_paths = {row["content_path"] for row in font_descriptor_rows}

    rows: list[dict[str, Any]] = []
    all_content_rows = list(content_hash_rows)
    all_content_rows.append({"AssetPath": "ContentHashes.json", "Category": "(root)", "Hash": sha256_file(content_root / "ContentHashes.json")})

    for source in all_content_rows:
        content_path = source["AssetPath"]
        category = source["Category"]
        source_path = content_root / Path(content_path)
        asset_no_ext = no_ext(content_path)
        source_type = source_type_for(category, content_path)
        final_status = "raw_local_source"
        validation_status = "pass"
        validation_detail = ""
        export_path = ""
        farmold_res_match = ""
        extractor = ""
        commit_policy = "local_only"

        if category == "Data" and asset_no_ext in data_index:
            row = data_index[asset_no_ext]
            final_status = "exported_data_reference"
            export_path = posix((exports_root / "stardew_data_exports_20260624" / row["JsonRelativePath"]).relative_to(farmold_root))
            extractor = "StardewDataExport"
            commit_policy = "local_only"
        elif category == "Strings" and asset_no_ext in strings_index:
            row = strings_index[asset_no_ext]
            final_status = "exported_string_reference"
            export_path = posix((exports_root / "stardew_strings_exports_20260624" / row["JsonRelativePath"]).relative_to(farmold_root))
            extractor = "StardewDataExport"
            commit_policy = "local_only"
        elif category == "Maps" and asset_no_ext in map_index:
            source_type = "MapBody"
            row = map_index[asset_no_ext]
            final_status = "exported_map_reference"
            export_path = posix((exports_root / "stardew_maps_20260623" / row["jsonFile"]).relative_to(farmold_root))
            extractor = "xTile map export"
            commit_policy = "local_only"
        elif content_path in decoded_by_path:
            decoded = decoded_by_path[content_path][0]
            if category == "Fonts":
                final_status = "decoded_font_reference"
            elif category == "VolcanoLayouts":
                final_status = "decoded_visual_reference"
                source_type = "DataOrLayout"
            else:
                final_status = "decoded_visual_reference"
            export_path = decoded["output_relative_path"]
            extractor = decoded.get("decoder", "xnb-js")
            commit_policy = "local_only"
        elif content_path in font_fnt_paths:
            final_status = "decoded_font_reference"
            export_path = "font_descriptor_index.csv"
            extractor = "xml.etree.ElementTree"
            commit_policy = "local_only"
        elif content_path in xact_index:
            final_status = "cataloged_audio_reference"
            export_path = "reference_indexes/xact_file_inventory.csv"
            extractor = "xact inventory"
            commit_policy = "local_only"
        elif content_path == "ContentHashes.json":
            final_status = "cataloged_runtime_reference"
            export_path = "reference_indexes/content_hashes_index.csv"
            extractor = "content hash inventory"
            commit_policy = "tracked_metadata_only"
        elif content_path.lower().endswith(".mgfxo"):
            final_status = "cataloged_runtime_reference"
            extractor = "raw file catalog"
            validation_detail = "Compiled MonoGame effect binary cataloged; not an XNB texture/data asset."
            commit_policy = "local_only"
        elif content_path in visual_index and visual_index[content_path].get("Status") == "present-in-farmold-res":
            final_status = "existing_farmold_res"
            farmold_res_match = "present-in-farmold-res"
            validation_detail = "Existing FarmOld res match from visual inventory."
            commit_policy = "tracked_asset_allowed"
        elif content_path in failed_by_path:
            final_status = "raw_local_source"
            validation_status = "blocked_with_reason"
            validation_detail = failed_by_path[content_path].get("message", "decode failed")
            extractor = failed_by_path[content_path].get("decoder", "xnb-js")
        else:
            final_status = "raw_local_source"
            validation_detail = "Local raw source cataloged; no runtime import requested."

        if not source_path.exists():
            validation_status = "blocked_with_reason"
            validation_detail = "source file missing"

        rows.append(
            {
                "content_path": content_path,
                "category": category,
                "source_type": source_type,
                "content_hash": source["Hash"],
                "source_exists": str(source_path.exists()),
                "farmold_res_match": farmold_res_match,
                "export_path": export_path,
                "final_status": final_status,
                "extractor": extractor,
                "validation_status": validation_status,
                "validation_detail": validation_detail,
                "commit_policy": commit_policy,
            }
        )

    return rows


def write_by_category(output_root: Path, manifest_rows: list[dict[str, Any]]) -> None:
    by_category_root = output_root / "by_category"
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in manifest_rows:
        grouped[str(row["category"])].append(row)
    for category, rows in sorted(grouped.items()):
        safe_name = category.replace("/", "_").replace("\\", "_").replace("(", "").replace(")", "") or "root"
        write_csv(by_category_root / f"{safe_name}.csv", rows)


def summarize_manifest(manifest_rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_category = Counter(row["category"] for row in manifest_rows)
    by_type = Counter(row["source_type"] for row in manifest_rows)
    by_status = Counter(row["final_status"] for row in manifest_rows)
    by_commit_policy = Counter(row["commit_policy"] for row in manifest_rows)
    unknown_statuses = {"unknown", "missing_unclassified", "extractor_failed_untriaged", "silent_fallback", "todo", "failed"}
    unknown_status_count = sum(1 for row in manifest_rows if str(row["final_status"]).lower() in unknown_statuses)
    missing_unclassified_count = sum(1 for row in manifest_rows if row["validation_detail"] == "source file missing")
    return {
        "manifest_rows": len(manifest_rows),
        "unknown_status_count": unknown_status_count,
        "missing_unclassified_count": missing_unclassified_count,
        "by_category": dict(sorted(by_category.items())),
        "by_type": dict(sorted(by_type.items())),
        "by_final_status": dict(sorted(by_status.items())),
        "by_commit_policy": dict(sorted(by_commit_policy.items())),
    }


def write_validation_report(output_root: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# Stardew Resource Completion Validation Report",
        "",
        f"> Generated: {summary['generated_at_local']}",
        f"> Output: `{output_root}`",
        "",
        "## Gate Results",
        "",
        "| Gate | Result |",
        "| --- | ---: |",
    ]
    gates = summary["gates"]
    for key, value in gates.items():
        lines.append(f"| `{key}` | `{value}` |")

    lines.extend(["", "## Manifest Status", "", "| Status | Count |", "| --- | ---: |"])
    for status, count in summary["manifest"]["by_final_status"].items():
        lines.append(f"| `{status}` | {count} |")

    lines.extend(["", "## Category Coverage", "", "| Category | Count |", "| --- | ---: |"])
    for category, count in summary["manifest"]["by_category"].items():
        lines.append(f"| `{category}` | {count} |")

    lines.extend(
        [
            "",
            "## Completion Conclusion",
            "",
            "The completion output is accepted when all hard gates are zero for missing, unknown, parse, and decode failure counts.",
        ]
    )
    (output_root / "validation_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    args = parse_args()
    farmold_root = Path(args.farmold_root).resolve()
    output_root = Path(args.output_root).resolve() if args.output_root else farmold_root / "_local_exports" / f"stardew_resource_completion_{OUTPUT_DATE}"
    content_root = farmold_root / "Content"
    exports_root = farmold_root / "_local_exports"
    output_root.mkdir(parents=True, exist_ok=True)

    content_hash_rows = read_csv(exports_root / "stardew_content_hashes_inventory_20260624" / "content_hashes_index.csv")
    content_hash_summary = validate_content_hashes(content_root, content_hash_rows)
    write_json(output_root / "source_integrity_report.json", content_hash_summary)

    farmold_res_summary = validate_images(farmold_root / "res")
    farmold_res_details = farmold_res_summary.pop("image_details")
    write_json(output_root / "farmold_res_image_validation.json", farmold_res_summary)
    write_csv(output_root / "farmold_res_image_details.csv", farmold_res_details)

    data_json_summary = validate_json_tree(exports_root / "stardew_data_exports_20260624" / "data_json")
    strings_json_summary = validate_json_tree(exports_root / "stardew_strings_exports_20260624" / "strings_json")

    decode_items = build_xnb_decode_input(farmold_root, output_root)
    if not args.skip_decode:
        xnb_summary = run_xnb_decoder(farmold_root, output_root)
    else:
        xnb_summary = json.loads((output_root / "xnb_decode_summary.json").read_text(encoding="utf-8"))

    decode_rows = read_csv(output_root / "xnb_decode_index.csv")
    decode_failures = read_csv(output_root / "xnb_decode_failures.csv")

    decoded_image_summary = validate_images(output_root / "decoded_visual")
    decoded_image_details = decoded_image_summary.pop("image_details")
    write_json(output_root / "decoded_visual_image_validation.json", decoded_image_summary)
    write_csv(output_root / "decoded_visual_image_details.csv", decoded_image_details)

    font_summary = parse_font_descriptors(farmold_root, output_root)
    font_descriptor_rows = read_csv(output_root / "font_descriptor_index.csv")
    reference_indexes = copy_reference_indexes(farmold_root, output_root)
    map_summary = map_tilesheet_validation(farmold_root, output_root, {row["AssetPath"] for row in content_hash_rows})
    contact_sheet_summary = build_contact_sheets(output_root, decode_rows)

    manifest_rows = build_manifest(
        farmold_root,
        output_root,
        content_hash_rows,
        decode_rows,
        decode_failures,
        font_descriptor_rows,
    )
    manifest_fields = [
        "content_path",
        "category",
        "source_type",
        "content_hash",
        "source_exists",
        "farmold_res_match",
        "export_path",
        "final_status",
        "extractor",
        "validation_status",
        "validation_detail",
        "commit_policy",
    ]
    write_csv(output_root / "resource_completion_manifest.csv", manifest_rows, manifest_fields)
    write_json(output_root / "resource_completion_manifest.json", manifest_rows)
    write_by_category(output_root, manifest_rows)

    manifest_summary = summarize_manifest(manifest_rows)
    gates = {
        "content_hash_entries": len(content_hash_rows),
        "checked_hash_files": content_hash_summary["checked_hash_files"],
        "missing_source_files": content_hash_summary["missing_source_files"],
        "hash_mismatches": content_hash_summary["hash_mismatches"],
        "farmold_res_zero_byte_files": farmold_res_summary["zero_byte_files"],
        "farmold_res_image_decode_failures": farmold_res_summary["image_decode_failures"],
        "data_json_parse_failures": data_json_summary["json_parse_failures"],
        "strings_json_parse_failures": strings_json_summary["json_parse_failures"],
        "xnb_decode_attempted_items": len(decode_items),
        "xnb_decode_failed_items": len(decode_failures),
        "decoded_visual_image_decode_failures": decoded_image_summary["image_decode_failures"],
        "font_descriptor_failures": font_summary["fnt_descriptor_failures"],
        "unknown_referenced_tilesheet_count": map_summary["unknown_referenced_tilesheet_count"],
        "unknown_status_count": manifest_summary["unknown_status_count"],
        "missing_unclassified_count": manifest_summary["missing_unclassified_count"],
        "contact_sheets_created": contact_sheet_summary["created"],
    }
    summary = {
        "schema": "farmold-stardew-resource-completion-v1",
        "generated_at_local": now_local(),
        "farmold_root": str(farmold_root),
        "content_root": str(content_root),
        "output_root": str(output_root),
        "reference_indexes": reference_indexes,
        "content_hashes": content_hash_summary,
        "farmold_res": farmold_res_summary,
        "data_json": data_json_summary,
        "strings_json": strings_json_summary,
        "xnb_decode": xnb_summary,
        "decoded_visual": decoded_image_summary,
        "fonts": font_summary,
        "maps": map_summary,
        "contact_sheets": contact_sheet_summary,
        "manifest": manifest_summary,
        "gates": gates,
    }
    write_json(output_root / "summary.json", summary)
    write_validation_report(output_root, summary)

    readme = f"""# Stardew Resource Completion Output

> Generated: {summary['generated_at_local']}
> Root: `{output_root}`

This directory is local-only output for FarmOld resource completion.

Important files:

- `resource_completion_manifest.csv`
- `resource_completion_manifest.json`
- `summary.json`
- `validation_report.md`
- `xnb_decode_index.csv`
- `xnb_decode_failures.csv`
- `font_descriptor_index.csv`
- `map_tilesheet_matrix.csv`
- `contact_sheets/`

Hard gates:

```json
{json.dumps(gates, indent=2, ensure_ascii=False)}
```
"""
    (output_root / "README.md").write_text(readme, encoding="utf-8")
    print(json.dumps({"output_root": str(output_root), "gates": gates}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
