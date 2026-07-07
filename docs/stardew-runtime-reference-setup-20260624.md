# Stardew Runtime Reference Setup

> Date: 2026-06-24
> Status: completed local build reference implementation
> Scope: FarmOld runtime and decompiled-source reference setup

## Goal

Record what FarmOld is missing besides raw resources, and keep the setup safe: FarmOld can compile against the user's installed Stardew Valley runtime files without committing official DLLs, EXEs, native libraries, or generated build output.

## Confirmed Inputs

- Stardew install root: `E:\soft\funSoft\steam\steamapps\common\Stardew Valley`
- FarmOld root: `E:\work\project\source-archives\farm-source-archive`
- FarmOld main project: `E:\work\project\source-archives\farm-source-archive\Stardew Valley\Stardew Valley.csproj`
- FarmOld GameData project: `E:\work\project\source-archives\farm-source-archive\StardewValley.GameData\StardewValley.GameData.csproj`
- Local build analysis output: `E:\work\project\source-archives\farm-source-archive\_local_exports\stardew_build_check_20260624`

## Non-Resource Gaps

FarmOld does not contain a complete Stardew runtime distribution. Compared with the installed game root, FarmOld is missing the runtime assemblies and launcher/native files needed to build or run the decompiled code as a normal .NET/MonoGame project.

The project files directly need these installed-game assemblies:

```text
MonoGame.Framework.dll
xTile.dll
SkiaSharp.dll
Steamworks.NET.dll
GalaxyCSharp.dll
Lidgren.Network.dll
System.Data.HashFunction.Interfaces.dll
System.Data.HashFunction.Core.dll
BmFont.dll
TextCopy.dll
System.Data.HashFunction.xxHash.dll
```

Validation result on 2026-06-24:

```text
In FarmOld root: false
In installed Stardew root: true
```

Those files should remain in the installed Stardew directory and be referenced locally. Do not copy them into Git.

## Local Build Contract

Tracked files:

```text
Directory.Build.props
Directory.Build.local.props.example
```

Ignored local-only file:

```text
Directory.Build.local.props
```

`Directory.Build.props` imports `Directory.Build.local.props` when present. The local file sets:

```xml
<StardewInstallDir>E:\soft\funSoft\steam\steamapps\common\Stardew Valley\</StardewInstallDir>
```

The project files resolve DLL references through:

```text
$(StardewReferenceDir)<dll-name>
```

This keeps FarmOld portable: another machine can copy `Directory.Build.local.props.example` to `Directory.Build.local.props` and point it at that machine's Stardew install.

## Decompiled Source Repairs

After adding local runtime references, `dotnet build` exposed decompiler artifacts in the C# source. These were source-recovery issues, not FarmOld gameplay design changes.

Fixed categories:

- `case 123L:` labels converted to integral switch labels accepted by C#.
- Switch-expression arms with `123L =>` converted to compatible integer arms.
- `NetInt` switch inputs in `Tree.cs` cast to `int` where the decompiler lost the intended primitive value.
- Duplicate local functions in `Game1.cs` restored to distinct names.
- Duplicate pattern/local variables in `Game1.cs` and `Object.cs` restored to distinct local names.
- Invalid decompiler assignment in `GameRunner.cs` removed.
- Pattern variable conflicts in `GameStateQuery.cs`, `HouseRenovation.cs`, `InteriorDoor.cs`, and `ItemContextTagManager.cs` repaired.
- Missing compiler-generated local function `ShowSkillMastery` in `GameLocation.MakeMapModifications` restored from installed-game IL.
- Missing `System.Data.HashFunction.Core.dll` project reference added.

The `ShowSkillMastery` recovery was based on the installed Stardew DLL IL method:

```text
GameLocation::<MakeMapModifications>g__ShowSkillMastery|162_0
```

It remains an internal reconstruction step. The source patch keeps the function local to the `MasteryCave` case so it can capture `levelsNotSpent`, matching the compiled shape.

## Validation

Build command:

```powershell
dotnet build "E:\work\project\source-archives\farm-source-archive\Stardew Valley\Stardew Valley.csproj" /t:Rebuild -v:minimal
```

Result on 2026-06-24:

```text
Exit code: 0
```

Only expected SDK warnings remained:

```text
NETSDK1138: target framework netcoreapp6.0 is out of support
```

Local evidence logs are under:

```text
_local_exports/stardew_build_check_20260624/
```

That directory is local-only and ignored by Git.

## What Not To Commit

Do not commit:

```text
Directory.Build.local.props
Content/
_local_exports/
Stardew Valley/bin/
Stardew Valley/obj/
StardewValley.GameData/bin/
StardewValley.GameData/obj/
official Stardew DLL/EXE/native runtime files
```

The correct long-term pattern is:

```text
FarmOld tracked source/docs     decompiled source and local setup docs
Installed Stardew root          official runtime DLLs and raw Content input
FarmOld/_local_exports          generated local analysis evidence
```

## Conclusion

Besides resources, FarmOld was missing the local runtime reference wiring and had several decompiler-damaged C# regions. With the local Stardew install referenced through `Directory.Build.local.props`, the main FarmOld project now compiles. FarmOld should not absorb the installed game's runtime files; it should reference them locally and document the dependency boundary.
