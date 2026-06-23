# Stardew Content Reference Setup

> Date: 2026-06-24
> Status: completed local reference implementation
> Scope: FarmOld local resource reference setup

## Goal

Create a safe local reference layout so FarmOld can inspect the user's installed Stardew Valley resources without mixing raw official content into the existing `res/` folder or committing those resources to Git.

## Confirmed Inputs

- Stardew install root: `E:\soft\funSoft\steam\steamapps\common\Stardew Valley`
- Stardew raw content root: `E:\soft\funSoft\steam\steamapps\common\Stardew Valley\Content`
- FarmOld root: `E:\work\project\FarmOld`
- FarmOld current extracted visual resources: `E:\work\project\FarmOld\res`
- FarmOld local analysis outputs: `E:\work\project\FarmOld\_local_exports`

## Directory Contract

```text
FarmOld/
  Content/          raw Stardew Content mirror or junction; input source only
  res/              existing FarmOld extracted PNG/YAML resources; keep stable
  _local_exports/   derived JSON/CSV/README reports and analysis outputs
  docs/             tracked docs that describe local setup and rules
```

`Content/` is the raw input source. It should preserve Stardew's original layout:

```text
Content/Maps/*.xnb
Content/Data/*.xnb
Content/Strings/*.xnb
Content/Characters/*.xnb
Content/Buildings/*.xnb
```

`_local_exports/` is the output area for generated analysis:

```text
_local_exports/stardew_maps_20260623/
_local_exports/stardew_farmold_missing_inventory_20260624/
_local_exports/stardew_data_exports_20260624/
_local_exports/stardew_strings_exports_20260624/
_local_exports/stardew_xact_audio_inventory_20260624/
_local_exports/stardew_fonts_inventory_20260624/
_local_exports/stardew_content_hashes_inventory_20260624/
_local_exports/stardew_volcanolayouts_exports_20260624/
_local_exports/stardew_visual_resource_inventory_20260624/
```

## Non-Goals

- Do not copy raw Stardew official content into Git.
- Do not merge raw `Content` files into `res/`.
- Do not treat `res/Maps/*.png` as map body data.
- Do not put `_local_exports` data inside `Content/`.
- Do not change FarmOld code loading behavior in this setup step.

## Implementation Steps

1. Add `Content/` and `Content (unpacked)/` to FarmOld `.gitignore`.
2. Create `FarmOld/Content` as a local junction pointing to the installed Stardew `Content`.
3. Keep `_local_exports` as the only derived-data output area.
4. Validate that Git ignores `Content/`.
5. Validate that `Content/Maps/Farm.xnb`, `Content/Data/Crops.xnb`, and `Content/Strings` are readable through the FarmOld path.
6. Export map body data, data tables, and strings into JSON/CSV under `_local_exports`.
7. Inventory XACT, Fonts, ContentHashes, VolcanoLayouts, and visual resource coverage without copying official binaries into Git.
8. Document exporter boundaries and remaining extraction requirements.

## Validation Commands

```powershell
git -C E:\work\project\FarmOld check-ignore -v Content
Test-Path E:\work\project\FarmOld\Content\Maps\Farm.xnb
Test-Path E:\work\project\FarmOld\Content\Data\Crops.xnb
Test-Path E:\work\project\FarmOld\Content\Strings
Test-Path E:\work\project\FarmOld\_local_exports\stardew_visual_resource_inventory_20260624\summary.json
Test-Path E:\work\project\FarmOld\_local_exports\stardew_content_hashes_inventory_20260624\summary.json
git -C E:\work\project\FarmOld status --short --branch
```

## Follow-Up

After this setup, future tools should read in this order:

```text
FarmOld/Content          raw official input
FarmOld/_local_exports   generated analysis output
FarmOld/res              existing extracted visual reference
```

If a tool exports data from `Content`, write the generated JSON/CSV/README under `_local_exports/<tool-name-date>/`.

The local reference setup is complete when the outputs listed in this document exist and FarmOld Git status shows only tracked meta files, not raw `Content/` or `_local_exports/` payloads.

## Data Export Result

Status: completed on 2026-06-24.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_data_exports_20260624
```

Result:

```text
scanned_xnb: 851
exported_json: 851
failed: 0
```

Important files:

```text
_local_exports/stardew_data_exports_20260624/README.md
_local_exports/stardew_data_exports_20260624/summary.json
_local_exports/stardew_data_exports_20260624/data_export_index.csv
_local_exports/stardew_data_exports_20260624/data_export_failures.csv
_local_exports/stardew_data_exports_20260624/data_json/Data/Crops.json
_local_exports/stardew_data_exports_20260624/data_json/Data/Buildings.json
_local_exports/stardew_data_exports_20260624/data_json/Data/FarmAnimals.json
```

The exporter source lives under `_local_exports/stardew_data_exports_20260624/_tool/` and is local-only. It is not intended to be committed with official game-derived JSON output.

## Strings Export Result

Status: completed on 2026-06-24.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_strings_exports_20260624
```

Result:

```text
scanned_xnb: 732
exported_json: 732
failed: 0
```

Important files:

```text
_local_exports/stardew_strings_exports_20260624/README.md
_local_exports/stardew_strings_exports_20260624/summary.json
_local_exports/stardew_strings_exports_20260624/strings_export_index.csv
_local_exports/stardew_strings_exports_20260624/strings_export_failures.csv
_local_exports/stardew_strings_exports_20260624/strings_json/Strings/StringsFromCSFiles.json
_local_exports/stardew_strings_exports_20260624/strings_json/Strings/1_6_Strings.zh-CN.json
```

The shared local exporter now accepts a content subdirectory argument, so the same tool can export `Data`, `Strings`, and later other readable Content groups while preserving the raw-input / derived-output boundary.

## XACT Audio Inventory Result

Status: completed on 2026-06-24.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_xact_audio_inventory_20260624
```

Result:

```text
file_count: 4
total_mib: 474.687
ascii_string_count: 451
```

Important files:

```text
_local_exports/stardew_xact_audio_inventory_20260624/README.md
_local_exports/stardew_xact_audio_inventory_20260624/summary.json
_local_exports/stardew_xact_audio_inventory_20260624/xact_file_inventory.csv
_local_exports/stardew_xact_audio_inventory_20260624/xact_ascii_strings.csv
```

Boundary:

- `FarmOld/Content/XACT` remains the raw input source.
- The large `.xwb` wave banks are not copied or decoded.
- The inventory records file size, role, SHA256, and source path.
- ASCII extraction only scans the small `.xgs` and `.xsb` files for cue-like names such as `doorClose`, `coin`, `hoeHit`, `fishBite`, and `grassyStep`.

## Fonts Inventory Result

Status: completed on 2026-06-24.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_fonts_inventory_20260624
```

Result:

```text
file_count: 55
.fnt: 5
.xnb: 50
total_mib: 20.301423
```

Important files:

```text
_local_exports/stardew_fonts_inventory_20260624/README.md
_local_exports/stardew_fonts_inventory_20260624/summary.json
_local_exports/stardew_fonts_inventory_20260624/fonts_file_inventory.csv
_local_exports/stardew_fonts_inventory_20260624/fnt_descriptor_index.csv
```

Boundary:

- `FarmOld/Content/Fonts` remains the raw input source.
- The setup records descriptors, sizes, SHA256, and source paths.
- Font binaries are not copied into `res/` or Git.

## ContentHashes Inventory Result

Status: completed on 2026-06-24.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_content_hashes_inventory_20260624
```

Result:

```text
entry_count: 3560
source_sha256: 8143AA3110810E0039282AB8E9989417092388EDB84C8C3B6C0B6F23840A4349
```

Category coverage:

```text
Animals: 43
Buildings: 47
Characters: 872
Data: 851
Effects: 3
Fonts: 55
LooseSprites: 156
Maps: 563
Minigames: 53
Portraits: 101
Strings: 732
TerrainFeatures: 38
TileSheets: 41
VolcanoLayouts: 1
XACT: 4
```

Important files:

```text
_local_exports/stardew_content_hashes_inventory_20260624/README.md
_local_exports/stardew_content_hashes_inventory_20260624/summary.json
_local_exports/stardew_content_hashes_inventory_20260624/content_hashes_index.csv
```

Boundary:

- `ContentHashes.json` remains under the local `FarmOld/Content` junction.
- The CSV is a derived searchable reference, not an imported runtime asset.

## VolcanoLayouts Reference Result

Status: completed as inventory on 2026-06-24; generic JSON export attempted and failed with a documented reader boundary.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_volcanolayouts_exports_20260624
```

Result:

```text
file_count: 1
attempted_xnb_export_failures: 1
failure: No Graphics Device Service
```

Important files:

```text
_local_exports/stardew_volcanolayouts_exports_20260624/README.md
_local_exports/stardew_volcanolayouts_exports_20260624/summary.json
_local_exports/stardew_volcanolayouts_exports_20260624/volcanolayouts_file_inventory.csv
_local_exports/stardew_volcanolayouts_exports_20260624/volcanolayouts_export_failures.csv
_local_exports/stardew_volcanolayouts_exports_20260624/volcanolayouts_ascii_strings.csv
```

Boundary:

- The current generic data exporter can read table/string XNB assets, but `VolcanoLayouts/Layouts.xnb` requires a graphics-device-backed reader.
- Treat this as a local visual/layout binary reference until a texture-capable XNB extractor is introduced.
- Do not mark this asset as decoded rules data.

## Visual Resource Inventory Result

Status: completed on 2026-06-24.

Output:

```text
E:\work\project\FarmOld\_local_exports\stardew_visual_resource_inventory_20260624
```

Result:

```text
source_visual_files_scanned: 1917
present_in_farmold_res: 501
missing_from_farmold_res: 1416
excluded_map_body_assets: 190
```

Category summary:

```text
Animals: source 43, present 26, missing 17
Buildings: source 47, present 17, missing 30
Characters: source 872, present 160, missing 712
Effects: source 3, present 0, missing 3
LooseSprites: source 156, present 64, missing 92
Maps: source 563, present 129, missing 434
Minigames: source 53, present 20, missing 33
Portraits: source 101, present 45, missing 56
TerrainFeatures: source 38, present 22, missing 16
TileSheets: source 41, present 18, missing 23
```

Important files:

```text
_local_exports/stardew_visual_resource_inventory_20260624/README.md
_local_exports/stardew_visual_resource_inventory_20260624/summary.json
_local_exports/stardew_visual_resource_inventory_20260624/visual_resource_inventory.csv
_local_exports/stardew_visual_resource_inventory_20260624/visual_missing_assets.csv
_local_exports/stardew_visual_resource_inventory_20260624/visual_summary_by_category.csv
_local_exports/stardew_visual_resource_inventory_20260624/visual_missing_priority_sample.csv
```

Boundary:

- This report compares Stardew visual/resource XNB assets against FarmOld's existing extracted `res` files.
- `Maps/*.xnb` assets already exported as map body data are excluded from this visual inventory.
- The report does not decode, copy, or commit official Stardew visual assets.

## Completion Status

This implementation document is complete for the local reference setup.

Completed local outputs:

```text
stardew_maps_20260623
stardew_farmold_missing_inventory_20260624
stardew_data_exports_20260624
stardew_strings_exports_20260624
stardew_xact_audio_inventory_20260624
stardew_fonts_inventory_20260624
stardew_content_hashes_inventory_20260624
stardew_volcanolayouts_exports_20260624
stardew_visual_resource_inventory_20260624
```

Remaining implementation work is intentionally outside this setup document:

- Decide which missing visual assets FarmOld should actually adopt.
- Introduce a texture-capable XNB extractor if FarmOld needs decoded pixels from currently binary-only visual assets.
- Decode XACT wave banks only if audio replacement or cue playback research becomes necessary.
- Keep all raw official resource references local-only unless there is an explicit licensing-safe extraction policy.
