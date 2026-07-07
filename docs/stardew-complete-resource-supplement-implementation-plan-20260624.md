# Stardew Complete Resource Supplement Implementation Plan

> Date: 2026-06-24
> Status: completed local implementation
> Scope: use the local Stardew Valley installation to fully supplement FarmOld's Stardew resource reference coverage
> Related docs:
> - `docs/stardew-content-reference-setup-20260624.md`
> - `docs/stardew-runtime-reference-setup-20260624.md`

## 中文执行摘要

这份文档是 FarmOld 补齐 Stardew 本体资源的总实施文档。核心口径是：不能只把 `Content/` 或缺失图片复制进 `res/` 就算完成，必须建立一个总清单，把 Stardew 本体 `ContentHashes.json` 的 `3560` 个条目全部登记到 manifest 里，每一项都要有最终状态、输出位置、校验结果和是否可提交的策略。

当前证据说明：FarmOld 现有 `res/` 没发现明显损坏，Data 和 Strings 已经可以完整导出，地图体也已经导出 `190` 个；真正缺口集中在视觉资源、地图 tilesheet 关系、字体、XACT 音频和 `VolcanoLayouts`。实施顺序是先做完整 manifest 和校验器，再收口已有 Data/Strings/Maps，之后补 texture-capable XNB 解码、地形/tilesheet catalog、角色/建筑/动物等视觉 catalog，最后处理字体、音频和 VolcanoLayouts。

默认安全边界是：`Content/` 继续作为本地忽略的官方原始输入，`_local_exports/` 作为本地生成输出，`res/` 不接收未经策略确认的官方原始或解码资源。最终完成标准不是“文件存在”，而是 `unknown_status_count=0`、`missing_unclassified_count=0`、所有资源类型都有验证报告。

## Implementation Result

Status: completed as a local resource completion implementation on 2026-06-24.

Command:

```powershell
python tools/stardew_resource/run_completion_pipeline.py
```

Output:

```text
E:\work\project\source-archives\farm-source-archive\_local_exports\stardew_resource_completion_20260624
```

Tracked implementation tools:

```text
tools/stardew_resource/export_xnb_assets.mjs
tools/stardew_resource/run_completion_pipeline.py
```

Generated local artifacts:

```text
_local_exports/stardew_resource_completion_20260624/resource_completion_manifest.csv
_local_exports/stardew_resource_completion_20260624/resource_completion_manifest.json
_local_exports/stardew_resource_completion_20260624/summary.json
_local_exports/stardew_resource_completion_20260624/validation_report.md
_local_exports/stardew_resource_completion_20260624/xnb_decode_index.csv
_local_exports/stardew_resource_completion_20260624/xnb_decode_failures.csv
_local_exports/stardew_resource_completion_20260624/decoded_visual/
_local_exports/stardew_resource_completion_20260624/decoded_fonts/
_local_exports/stardew_resource_completion_20260624/decoded_volcanolayouts/
_local_exports/stardew_resource_completion_20260624/contact_sheets/
_local_exports/stardew_resource_completion_20260624/by_category/
```

Hard gate results:

| Gate | Result |
| --- | ---: |
| `content_hash_entries` | `3560` |
| `checked_hash_files` | `3560` |
| `missing_source_files` | `0` |
| `hash_mismatches` | `0` |
| `farmold_res_zero_byte_files` | `0` |
| `farmold_res_image_decode_failures` | `0` |
| `data_json_parse_failures` | `0` |
| `strings_json_parse_failures` | `0` |
| `xnb_decode_attempted_items` | `1967` |
| `xnb_decode_failed_items` | `0` |
| `decoded_visual_image_decode_failures` | `0` |
| `font_descriptor_failures` | `0` |
| `unknown_referenced_tilesheet_count` | `0` |
| `unknown_status_count` | `0` |
| `missing_unclassified_count` | `0` |
| `contact_sheets_created` | `9` |

Final manifest status:

| Final status | Count |
| --- | ---: |
| `cataloged_audio_reference` | 4 |
| `cataloged_runtime_reference` | 2 |
| `decoded_font_reference` | 55 |
| `decoded_visual_reference` | 1727 |
| `exported_data_reference` | 851 |
| `exported_map_reference` | 190 |
| `exported_string_reference` | 732 |

Final source type split:

| Source type | Count |
| --- | ---: |
| `AudioBank` | 4 |
| `DataConfig` | 851 |
| `DataOrLayout` | 1 |
| `Font` | 55 |
| `HashIndex` | 1 |
| `MapBody` | 190 |
| `MapTilesheetOrImage` | 373 |
| `ShaderEffectBinary` | 1 |
| `StringsText` | 732 |
| `VisualSprite` | 1353 |

All official raw and decoded assets remain local-only through `Content/` and `_local_exports/`. The tracked repository changes are the implementation document and reusable tooling; generated Stardew-derived payloads are not committed by default.

## Goal

FarmOld already has three different resource areas:

```text
FarmOld/
  Content/          local ignored mirror or junction to official Stardew Content
  res/              existing FarmOld extracted visual reference files
  _local_exports/   generated local reports, JSON, CSV, and future decoded references
```

This plan defines the work required to make FarmOld's Stardew resource reference complete.

Complete does not mean blindly copying every official asset into `res/`. Complete means every Stardew `Content` entry is accounted for in a machine-readable ledger, every gap between Stardew and FarmOld is assigned an action, every exportable reference is exported or cataloged, and no asset remains in an unknown or unverified state.

## Completion Definition

The resource supplement work is complete only when all of these are true:

1. `ContentHashes.json` is the top-level source ledger and all `3560` entries are represented in the completion manifest.
2. Every Stardew content file has exactly one final status:
   - `raw_local_source`
   - `existing_farmold_res`
   - `exported_data_reference`
   - `exported_string_reference`
   - `exported_map_reference`
   - `decoded_visual_reference`
   - `decoded_font_reference`
   - `cataloged_audio_reference`
   - `cataloged_runtime_reference`
   - `excluded_by_policy`
   - `not_needed_by_farmold`
3. Final status `unknown`, `missing_unclassified`, `extractor_failed_untriaged`, or `silent_fallback` count is `0`.
4. Existing FarmOld `res/` image files still validate with `0` zero-byte files and `0` image decode failures.
5. Data and string exports remain at `0` failed XNB exports.
6. Map bodies, tilesheets, visual sprites, fonts, audio banks, and special layout assets each have their own validation report.
7. The final report explicitly states what was kept local-only, what entered `res/`, and what cannot be committed because it is official game content.

## Policy Boundary

Default policy:

- `Content/` is raw official input and must remain local-only and ignored by Git.
- `_local_exports/` is derived local analysis output and must remain ignored by Git unless a specific small metadata file is approved for tracking.
- `res/` is the existing FarmOld extracted visual reference area. Do not dump raw Stardew `Content` files into it.
- Official DLL, EXE, native library, XNB, XWB, XSB, XGS, and decoded official art/audio files are not committed by default.

If a future decision explicitly allows tracking decoded official assets, that decision must be written down before moving generated assets from `_local_exports/` into tracked `res/`.

## Current Evidence Snapshot

The following numbers are from local outputs under `E:\work\project\source-archives\farm-source-archive\_local_exports`.

### Integrity And Existing Outputs

| Area | Current result | Meaning |
| --- | ---: | --- |
| `ContentHashes.json` entries | `3560` | Stardew official content hash ledger is readable. |
| FarmOld `res/` files | `585` | Existing FarmOld extracted reference pool. |
| FarmOld `res/` image files | `584` | Existing image reference files. |
| FarmOld `res/` zero-byte files | `0` | No obvious empty image/resource damage found. |
| FarmOld `res/` image decode failures | `0` | Existing images are readable. |
| Data XNB scanned/exported/failed | `851 / 851 / 0` | Data export is complete for current exporter. |
| Strings XNB scanned/exported/failed | `732 / 732 / 0` | Strings export is complete for current exporter. |
| Map body exports | `190` | Map body data exists in local map export output. |
| XACT audio inventory | `4` files, `474.687 MiB` | Inventory only; not decoded or copied. |
| Fonts inventory | `55` files | Inventory only for 50 XNB fonts and 5 FNT descriptors. |
| VolcanoLayouts | `1` file, `1` export failure | Needs graphics-device-capable XNB reader; not proven corrupt. |

### Full Missing Inventory

From `stardew_farmold_missing_inventory_20260624/summary.json`:

| Type | Stardew count | Present in FarmOld | Missing from FarmOld |
| --- | ---: | ---: | ---: |
| VisualSprite | 1354 | 305 | 1049 |
| DataConfig | 851 | 0 | 851 |
| StringsText | 732 | 0 | 732 |
| MapTilesheetOrImage | 373 | 119 | 254 |
| MapBody | 190 | 0 | 190 |
| Font | 55 | 5 | 50 |
| AudioBank | 4 | 0 | 4 |
| DataOrLayout | 1 | 0 | 1 |
| HashIndex | 1 | 0 | 1 |

By category:

| Category | Stardew count | Present in FarmOld | Missing from FarmOld |
| --- | ---: | ---: | ---: |
| Data | 851 | 0 | 851 |
| Characters | 872 | 95 | 777 |
| Strings | 732 | 0 | 732 |
| Maps | 563 | 119 | 444 |
| LooseSprites | 156 | 64 | 92 |
| Portraits | 101 | 43 | 58 |
| Fonts | 55 | 5 | 50 |
| Minigames | 53 | 20 | 33 |
| Buildings | 47 | 17 | 30 |
| TileSheets | 41 | 18 | 23 |
| Animals | 43 | 26 | 17 |
| TerrainFeatures | 38 | 22 | 16 |
| XACT | 4 | 0 | 4 |
| Effects | 3 | 0 | 3 |
| root | 1 | 0 | 1 |
| VolcanoLayouts | 1 | 0 | 1 |

### Visual Coverage

From `stardew_visual_resource_inventory_20260624/summary.json`:

| Category | Source files | Present in FarmOld `res` | Missing from FarmOld `res` |
| --- | ---: | ---: | ---: |
| Animals | 43 | 26 | 17 |
| Buildings | 47 | 17 | 30 |
| Characters | 872 | 160 | 712 |
| Effects | 3 | 0 | 3 |
| LooseSprites | 156 | 64 | 92 |
| Maps | 563 | 129 | 434 |
| Minigames | 53 | 20 | 33 |
| Portraits | 101 | 45 | 56 |
| TerrainFeatures | 38 | 22 | 16 |
| TileSheets | 41 | 18 | 23 |

Visual inventory totals:

```text
source_files: 1917
present_in_farmold_res: 501
missing_from_farmold_res: 1416
excluded_map_body_assets: 190
```

## Confirmed, Candidate, Open, Deferred

### Confirmed

- FarmOld should keep `Content/` as the raw official input source.
- FarmOld should keep `_local_exports/` as the generated local evidence area.
- Existing `res/` must not be treated as complete because `1416` visual resources are missing from it.
- Data and strings are already exportable with `0` failures, but they still need a completion manifest and final reference contract.
- XACT audio and fonts are currently inventory-only, not complete decoded/runtime references.
- `VolcanoLayouts/Layouts.xnb` needs a graphics-device-capable extractor path.

### Candidate

- Add local scripts under a new `tools/stardew_resource/` directory if this workflow should become repeatable from tracked source.
- Keep large decoded official art/audio only under `_local_exports/stardew_resource_completion_<date>/decoded_*`.
- Generate small tracked documentation summaries only, while leaving large generated payloads ignored.

### Open

- Whether decoded official assets may ever be committed into `res/`.
- Whether FarmOld should become a runnable Stardew-compatible reference build or remain a decompiled-source/reference-analysis repo.
- Whether audio completion means cue/bank catalog only or decoded playback-ready files.

### Deferred

- FarmGodot migration usage of these resources.
- Rebuilding FarmOld gameplay systems from the supplemented resources.
- Shipping official Stardew assets in a public repository.

### Rejected

- Copying the whole official `Content/` tree into tracked `res/`.
- Treating current visual inventory as completion.
- Treating `VolcanoLayouts` export failure as corruption without a graphics-device-capable extractor attempt.
- Treating audio bank inventory as decoded audio completion.

## Target Artifact Layout

The next implementation should create a single completion output root:

```text
_local_exports/stardew_resource_completion_20260624/
  README.md
  resource_completion_manifest.csv
  resource_completion_manifest.json
  summary.json
  validation_report.md
  by_category/
    Data.csv
    Strings.csv
    Maps.csv
    TileSheets.csv
    Characters.csv
    Portraits.csv
    Animals.csv
    Buildings.csv
    TerrainFeatures.csv
    LooseSprites.csv
    Minigames.csv
    Effects.csv
    Fonts.csv
    XACT.csv
    VolcanoLayouts.csv
  decoded_data/
  decoded_strings/
  decoded_maps/
  decoded_visual/
  decoded_fonts/
  audio_catalog/
  tools_snapshot/
```

If tracked tools are introduced:

```text
tools/stardew_resource/
  build_completion_manifest.py
  validate_content_hashes.py
  validate_farmold_res_images.py
  export_data_and_strings.py
  export_maps.py
  export_textures.py
  export_fonts.py
  inventory_xact_audio.py
  validate_completion.py
```

If the repo should avoid adding tracked tools, keep the scripts under:

```text
_local_exports/stardew_resource_completion_20260624/_tool/
```

## Manifest Schema

Every asset row in `resource_completion_manifest.csv` must include:

| Field | Required meaning |
| --- | --- |
| `content_path` | Path relative to `FarmOld/Content`, for example `Characters/Abigail.xnb`. |
| `category` | Top-level Stardew category. |
| `source_type` | `DataConfig`, `StringsText`, `MapBody`, `MapTilesheetOrImage`, `VisualSprite`, `Font`, `AudioBank`, `DataOrLayout`, `HashIndex`, `ShaderEffectBinary`. |
| `content_hash` | Hash from `ContentHashes.json` when available. |
| `source_exists` | Whether the local `Content/` file exists. |
| `farmold_res_match` | Existing `res/` match path, if any. |
| `export_path` | Generated local export path, if any. |
| `final_status` | One of the approved completion statuses. |
| `extractor` | Tool path or method used. |
| `validation_status` | `pass`, `policy_excluded`, `not_needed`, or `blocked_with_reason`. |
| `validation_detail` | Exact reason, not free-floating guesswork. |
| `commit_policy` | `tracked_metadata_only`, `local_only`, or `tracked_asset_allowed`. |

Forbidden final values:

```text
unknown
missing_unclassified
todo
fallback
failed
```

If an asset cannot be decoded because of a real technical boundary, the row must be explicit:

```text
final_status=raw_local_source
validation_status=blocked_with_reason
validation_detail=requires_graphics_device_xnb_reader
commit_policy=local_only
```

## Workstreams

### WS0 Source And Integrity Gate

Goal: prove the raw source and existing FarmOld reference pool are readable before any import.

Required actions:

1. Verify `FarmOld/Content` points to the installed Stardew `Content`.
2. Verify every `ContentHashes.json` row resolves to an existing local file or a documented non-file ledger entry.
3. Verify no current `res/` file is zero-byte.
4. Verify all current `res/` images decode.
5. Write `source_integrity_report.json`.

Acceptance:

```text
content_hash_entries: 3560
missing_source_files: 0
farmold_res_zero_byte_files: 0
farmold_res_image_decode_failures: 0
```

### WS1 Canonical Completion Manifest

Goal: merge all existing reports into one ledger.

Inputs:

- `stardew_content_hashes_inventory_20260624/content_hashes_index.csv`
- `stardew_farmold_missing_inventory_20260624/summary.json`
- `stardew_visual_resource_inventory_20260624/visual_resource_inventory.csv`
- `stardew_maps_20260623/map_summary.csv`
- `stardew_data_exports_20260624/data_export_index.csv`
- `stardew_strings_exports_20260624/strings_export_index.csv`
- `stardew_xact_audio_inventory_20260624/xact_file_inventory.csv`
- `stardew_fonts_inventory_20260624/fonts_file_inventory.csv`
- `stardew_volcanolayouts_exports_20260624/volcanolayouts_file_inventory.csv`

Outputs:

- `resource_completion_manifest.csv`
- `resource_completion_manifest.json`
- `summary.json`

Acceptance:

```text
manifest_rows >= 3560
unknown_status_count: 0
duplicate_content_path_count: 0
```

### WS2 Data And Strings Completion

Goal: turn already successful exports into a formal completion lane.

Required actions:

1. Copy or reference the existing `851` data exports under the completion root.
2. Copy or reference the existing `732` string exports under the completion root.
3. Record original .NET object type for typed data rows where available.
4. Add a validation pass that opens every exported JSON file.
5. Mark data rows as `exported_data_reference` and string rows as `exported_string_reference`.

Acceptance:

```text
data_scanned: 851
data_exported: 851
data_failed: 0
strings_scanned: 732
strings_exported: 732
strings_failed: 0
json_parse_failures: 0
```

### WS3 Map Body And Tilesheet Closure

Goal: make map data usable as reference, not just counted.

Required actions:

1. Keep the existing `190` exported map bodies as `exported_map_reference`.
2. For every map, record:
   - map name
   - size
   - layers
   - tilesheet references
   - tile properties
   - map properties
   - animated tile references if detected
3. Cross-check all referenced tilesheets against `TileSheets` and `Maps` visual files.
4. Generate a missing-tilesheet report.
5. Render or summarize at least representative maps: farm, farmhouse, town, mine, volcano, festival.

Acceptance:

```text
map_body_count: 190
map_parse_failures: 0
tilesheet_reference_unknown_count: 0
representative_map_reports_created: true
```

### WS4 Texture-Capable XNB Visual Export

Goal: close the largest gap: visual resources missing from `res`.

Required actions:

1. Introduce or localize a texture-capable XNB extractor that can decode Stardew XNB textures.
2. Export visual assets into `_local_exports/stardew_resource_completion_20260624/decoded_visual/`.
3. Preserve original category and relative path.
4. Record width, height, pixel format, SHA256, and decode status.
5. Validate every decoded image with an image decoder.
6. Generate category contact sheets for review.

Priority order:

1. `TileSheets`
2. `Maps` tilesheet or image assets
3. `TerrainFeatures`
4. `Buildings`
5. `Animals`
6. `Characters`
7. `Portraits`
8. `LooseSprites`
9. `Minigames`
10. `Effects`

Acceptance:

```text
visual_source_files: 1917
visual_excluded_map_body_assets: 190
visual_decode_unknown_count: 0
visual_image_decode_failures: 0
```

If a visual asset is intentionally not decoded, it must have `final_status=excluded_by_policy` or `not_needed_by_farmold`; it cannot remain missing without classification.

### WS5 Terrain, TileSheet, And Map Visual Catalog

Goal: make terrain-related resources understandable for FarmOld map and terrain analysis.

Required actions:

1. Build a catalog for every decoded tilesheet:
   - source content path
   - decoded path
   - tile size if inferable
   - sheet dimensions
   - referenced maps
   - known tile properties from map exports
2. Produce a map-to-tilesheet matrix.
3. Produce a tilesheet-to-tile-property matrix.
4. Identify sheets that are images but not tile grids.
5. Keep this as data, not hand-written visual assumptions.

Acceptance:

```text
tilesheet_catalog_created: true
map_to_tilesheet_matrix_created: true
unknown_referenced_tilesheet_count: 0
```

### WS6 Character, Portrait, Animal, Building, And Object Visual Catalog

Goal: make visual assets searchable by category and source path.

Required actions:

1. Build category catalogs for:
   - Characters
   - Portraits
   - Animals
   - Buildings
   - LooseSprites
   - Minigames
   - Effects
   - TerrainFeatures
2. Record frame dimensions only when inferable from Stardew source code, map metadata, or known regular sheet dimensions.
3. Do not invent animation semantics from image shape alone.
4. Generate category contact sheets for manual inspection.

Acceptance:

```text
category_catalogs_created: true
contact_sheets_created: true
unclassified_visual_assets: 0
```

### WS7 Fonts Completion

Goal: move fonts from inventory-only to classified reference completion.

Required actions:

1. Parse the `5` `.fnt` descriptor files.
2. Link descriptor pages to local source files when possible.
3. Attempt XNB font export with a compatible reader.
4. If XNB font export is not technically supported, classify each row as `raw_local_source` with `validation_detail=font_xnb_reader_required`.

Acceptance:

```text
font_files: 55
fnt_descriptors_parsed: 5
font_unknown_count: 0
```

### WS8 XACT Audio Completion

Goal: make audio reference complete without pretending the banks are decoded.

Required actions:

1. Keep `4` XACT files as raw local source.
2. Preserve SHA256, size, role, and source path.
3. Extract cue-like names from `.xgs` and `.xsb`.
4. Link `Data/AudioChanges` and other audio-related data exports to known cue names where possible.
5. Decide whether completion means catalog-only or decoded playback-ready files.

Default acceptance for catalog-only completion:

```text
xact_files: 4
audio_catalog_created: true
audio_unknown_count: 0
decoded_audio_required: false
```

If decoded audio becomes required, add a separate implementation document because XACT extraction changes tooling, storage, and licensing risk.

### WS9 VolcanoLayouts Completion

Goal: turn the current single exporter failure into an explicit supported or unsupported status.

Required actions:

1. Attempt export with a graphics-device-capable XNB reader.
2. If export succeeds, save decoded layout JSON and validate it.
3. If export still fails, record exact exception, tool version, and reason.
4. The final manifest row cannot say only `failed`; it must state the technical boundary.

Acceptance:

```text
volcanolayout_files: 1
volcanolayout_unknown_count: 0
volcanolayout_failure_untriaged_count: 0
```

### WS10 Final Validation And Report

Goal: prove the supplement is complete.

Required actions:

1. Run all validators.
2. Generate `validation_report.md`.
3. Generate final summary counts by category, type, final status, and commit policy.
4. Update this document with completion evidence or create a completion report beside it.

Acceptance:

```text
unknown_status_count: 0
missing_unclassified_count: 0
image_decode_failures: 0
json_parse_failures: 0
manifest_duplicate_count: 0
validation_report_created: true
```

## Work Packages

### WP-A: Completion Manifest And Validators

Status: ready

Goal:

- Create the single manifest and final validation command.

Inputs:

- Existing `_local_exports/stardew_*_20260624` outputs.
- `FarmOld/Content/ContentHashes.json`.
- `FarmOld/res`.

Outputs:

- `resource_completion_manifest.csv`
- `resource_completion_manifest.json`
- `summary.json`
- `validation_report.md`

Allowed modifications:

- Local ignored `_local_exports/stardew_resource_completion_20260624/`
- Optional tracked `tools/stardew_resource/`
- Optional tracked docs under `docs/`

Acceptance:

```text
manifest_rows >= 3560
unknown_status_count: 0
duplicate_content_path_count: 0
```

### WP-B: Existing Data, Strings, And Map Export Closure

Status: ready

Goal:

- Reclassify the already successful exports as formal completion outputs.

Inputs:

- `stardew_data_exports_20260624`
- `stardew_strings_exports_20260624`
- `stardew_maps_20260623`

Outputs:

- Completion-root copies or references.
- Parse validation report.
- Map-to-tilesheet matrix.

Acceptance:

```text
data_failed: 0
strings_failed: 0
map_body_count: 190
map_reference_unknown_count: 0
```

### WP-C: Texture XNB Export Pipeline

Status: ready, tool-dependent

Goal:

- Decode visual XNB assets into local reference images.

Inputs:

- `FarmOld/Content`
- `visual_resource_inventory.csv`

Outputs:

- `decoded_visual/`
- visual dimensions report
- contact sheets

Acceptance:

```text
visual_decode_unknown_count: 0
visual_image_decode_failures: 0
```

### WP-D: Terrain And Tilesheet Catalog

Status: depends on WP-C

Goal:

- Make Stardew's terrain/map tilesheet resource relationships queryable.

Inputs:

- Decoded tilesheets.
- Map exports.
- Tile properties from map data.

Outputs:

- `tilesheet_catalog.csv`
- `map_tilesheet_matrix.csv`
- `tile_property_matrix.csv`

Acceptance:

```text
unknown_referenced_tilesheet_count: 0
tilesheet_catalog_created: true
```

### WP-E: Visual Category Catalogs

Status: depends on WP-C

Goal:

- Make non-map visual resources searchable and inspectable.

Inputs:

- Decoded visual outputs.

Outputs:

- category CSV files
- contact sheets

Acceptance:

```text
unclassified_visual_assets: 0
contact_sheets_created: true
```

### WP-F: Fonts, Audio, And VolcanoLayouts Closure

Status: ready, tool-dependent

Goal:

- Close the current inventory-only lanes.

Inputs:

- `stardew_fonts_inventory_20260624`
- `stardew_xact_audio_inventory_20260624`
- `stardew_volcanolayouts_exports_20260624`

Outputs:

- font descriptor report
- audio cue catalog
- VolcanoLayouts decode or classified boundary report

Acceptance:

```text
font_unknown_count: 0
audio_unknown_count: 0
volcanolayout_unknown_count: 0
```

### WP-G: Final Closeout

Status: depends on WP-A through WP-F

Goal:

- Produce the final evidence report and update tracked docs.

Outputs:

- final `validation_report.md`
- updated docs summary
- Git status showing only intended tracked doc/tool changes

Acceptance:

```text
unknown_status_count: 0
missing_unclassified_count: 0
validation_report_created: true
```

## Suggested Execution Order

1. Run WS0 and create source integrity report.
2. Implement WP-A manifest builder and validator.
3. Close WP-B using existing data, string, and map outputs.
4. Implement WP-C texture export, then run WP-D and WP-E.
5. Close WP-F fonts, audio, and VolcanoLayouts.
6. Run WS10 final validator.
7. Update docs with exact final counts and known policy exclusions.

## Validation Commands

Expected future commands:

```powershell
python tools/stardew_resource/validate_content_hashes.py
python tools/stardew_resource/validate_farmold_res_images.py
python tools/stardew_resource/build_completion_manifest.py
python tools/stardew_resource/validate_completion.py
```

If tools remain local-only:

```powershell
python _local_exports/stardew_resource_completion_20260624/_tool/validate_content_hashes.py
python _local_exports/stardew_resource_completion_20260624/_tool/validate_farmold_res_images.py
python _local_exports/stardew_resource_completion_20260624/_tool/build_completion_manifest.py
python _local_exports/stardew_resource_completion_20260624/_tool/validate_completion.py
```

Tracked doc validation:

```powershell
git -C E:\work\project\source-archives\farm-source-archive diff --check -- docs/stardew-complete-resource-supplement-implementation-plan-20260624.md
git -C E:\work\project\source-archives\farm-source-archive status --short
```

## Final Checklist

- [x] `ContentHashes.json` entries all represented in the completion manifest.
- [x] `Content/` raw source files remain local-only.
- [x] Existing `res/` image validation remains clean.
- [x] Data exports are validated and classified.
- [x] String exports are validated and classified.
- [x] All `190` map bodies are validated and classified.
- [x] Map tilesheet references have no unknown targets.
- [x] Visual resources have no unclassified missing rows.
- [x] Texture-capable XNB extraction is implemented or each unsupported row has a specific technical reason.
- [x] Fonts are parsed, decoded, or explicitly classified.
- [x] XACT audio has a cue/bank catalog.
- [x] `VolcanoLayouts/Layouts.xnb` is decoded.
- [x] Final manifest has `0` unknown statuses.
- [x] Final validation report is generated.
- [x] Tracked docs explain which artifacts are local-only and why.

## Implementation Rule

Do not mark this effort complete because a file exists in `Content/`.

For each asset, completion requires a row in the manifest, a final status, an output or reason, and a validator result. This is the only way to make FarmOld's missing resource coverage auditable instead of relying on scattered folders and one-off exports.
