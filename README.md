Stardew Valley 1.6 decompiled for a better understanding of how the game functions under the hood, and to ease the modding process

*Note: The StardewValley.csproj does have external references which you must provide yourself. The most important, MonoGame.Framework.dll, can be found in your Stardew Valley download folder (with the .exe). Simply copy this into the same folder with the .csproj and Visual Studio should detect it OR change the reference path to be the game location.*

## Local reference exports

Local Stardew map exports live under:

```text
_local_exports/stardew_maps_20260623
```

This directory is intentionally ignored by Git. It is a local analysis source for map layers, tile indexes, tile properties, animated tiles, and draw-group behavior from the user's installed Stardew Valley `Content/Maps`.

Use it as a reference for understanding `Back / Buildings / Paths / Front / AlwaysFront` map structure. Do not commit the full exported official map data or copy it directly as runtime game content.

Complete local Stardew resource completion is documented in:

```text
docs/stardew-complete-resource-supplement-implementation-plan-20260624.md
```

The generated local completion output lives under:

```text
_local_exports/stardew_resource_completion_20260624
```

That output includes the completion manifest, XNB decode index, validation report, decoded local references, and category contact sheets. It remains ignored by Git because it is derived from the user's installed Stardew Valley content.
