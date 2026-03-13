---
name: rimworld-log-check
description: Analyze RimWorld HugsLib player logs to diagnose mod conflicts, crashes, exceptions, and errors. Use this skill whenever a user pastes or links a RimWorld log, mentions mod conflicts, game crashes, or errors in RimWorld, asks "what's wrong with my mods", shares a gist.github.com/HugsLibRecordKeeper link, or is troubleshooting any RimWorld startup/runtime issue. Also trigger when a user says "my game is crashing", "I have errors after startup", or "can you check my log". This skill performs the same analysis as Orion's rw-log-check tool (https://orionFive.github.io/rw-log-check/) and goes further with mod-specific recommendations.
license: MIT
compatibility: Requires web fetch capability to retrieve HugsLib Gist URLs. Works with RimWorld 1.4+ logs (HugsLib format). RimWorld 1.6+ logs use a different mod-list format — both are supported.
metadata:
  version: "2.0"
  rimworld-versions: "1.4, 1.5, 1.6"
  hugslib-min: "12.0.0"
---

# RimWorld Log Checker Skill

Performs comprehensive analysis of RimWorld HugsLib `output_log.txt` / `player.log` files. Identifies mod conflicts, exceptions, errors, and warnings — and names the responsible mods.

---

## Input Formats

The user may provide the log as:
1. **HugsLib Gist URL** — `https://gist.github.com/HugsLibRecordKeeper/<id>` — fetch via GitHub Gist API: `https://api.github.com/gists/<id>`, then read `.files["output_log.txt"].content`
2. **Pastebin or other paste URL** — fetch the raw content
3. **Direct paste** — use as-is

> If a URL is given, always fetch the raw log content before analyzing.

---

## Analysis Pipeline

### Phase 1 — Extract Metadata

Find and extract:
- **RimWorld version**: line matching `RimWorld \d+\.\d+\.\d+`
- **HugsLib version**: line matching `\[HugsLib\] version (\S+)`
- **Mod list** (best-effort — format changed in 1.6):
  - **Pre-1.6 format**: Look for a `Loaded mods:` block. Lines follow the pattern `ModName(packageId)[mv:version]` — extract name, packageId, and version from each.
  - **1.6+ format**: No `Loaded mods:` block exists. Instead, scan for lines matching `[ModName] Loaded.`, `[ModName] version X`, or `ModName vX.X` during the init phase. Extract the bracketed mod name. These are display names only — packageIds are not available in this format.
  - **If neither format is detected**: Note "Mod list unavailable — log format not recognized" and skip the 📦 Active Mods section. This does not affect error analysis.
- **Log section boundaries**:
  - **Startup section**: from `Log file contents:` (pre-1.6) OR from `Prepatcher: Restarted` / `RimWorld \d+\.\d+` (1.6+) to first `Loading game from file` line
  - **Runtime section**: from first `Loading game from file` onward (or full log if no load marker — means the session ended before a save was loaded)

---

### Phase 2 — Parse & Classify Log Lines

Process each line. Skip lines starting with `(`, ` `, or that match Harmony patch listing patterns (`: PRE:`, `: post:`, `: TRANS:`, `Prefixes:`, `Postfixes:`, `Transpilers:`).

**Exception detection**: A line is an exception if the *next* line starts with `  at ` OR the current line contains `Exception:`. Collect the full exception block until a `(Filename:` line.

**Error/warning detection**: A line is an error/warning if the next line starts with `(`.

**Common error patterns** (treat as errors even without filename annotation):
- `Could not load reference to`
- `Could not find`
- `Could not resolve`
- `Null key while loading`
- `Config error`
- `XML error`
- `Failed to find`

**Redundancy detection** — collect into a `redundancies[]` bucket (separate from errors/warnings):

*Signal 1 — NQoL Notice lines* (present when Niilo's QoL is active):
```
NQoL Notice - <ModA> | <ModB> - Have overlapping functionality! - <feature description>
```
Extract Mod A, Mod B, and the feature string. These are developer-confirmed overlaps.

*Signal 2 — Mod-authored COMPAT warnings* (emitted by mods like Job In Bar):
```
[<ModA>] [COMPAT] <ModB> [<packageId>] detected.
<next line often describes the conflict, e.g. "That mod also adds labels to the colonist bar">
```
Capture both mod names and the description line that follows if present.

*Signal 3 — Static DB cross-reference* (see Phase 3 below): after the full mod list is extracted in Phase 1, compare every active mod against the Known Redundancy Database. Any pair where both mods are present → add to `redundancies[]` with the DB's feature and recommendation fields.

---

### Phase 3 — Identify Known Issues

Match each parsed item against the classifier database below. For each match, extract the explanation and offending mod(s).

#### EXCEPTION CLASSIFIERS

| Pattern | Type | Explanation | Offending Mod |
|---|---|---|---|
| `Object reference not set to an instance of an object in %s(%s) at %s..ctor` | exception | Object of the mod could not be created. Recommend removing mod. | capture[2] (mod name) |
| `Could not execute post-long-event action. Exception: %s: %s.` | exception | Scheduled code failed to run — something that should have happened didn't. | namespaces from stack trace |
| `Exception ticking %s (at %s).` | exception | Object failed to update — causes strange behavior of that object. | namespaces from stack trace |
| `Error while instantiating a mod of type %s: System.Reflection.TargetInvocationException` | exception | Mod couldn't initialize. Recommend removing. | capture[1] (mod type) |
| `Exception in %s: System.InvalidCastException: Specified cast is not valid.` | exception | Sign of poor programming or a mod conflict. | namespaces from stack trace |
| `System.MissingFieldException: Field 'Verse.%s' not found.` | exception | Mod accessing non-existent field — RimWorld or mod is outdated. | namespaces from stack trace |
| `System.NullReferenceException: Object reference not set to an instance of an object` | exception | Very common, low-signal error. Sign of mod conflict or poor programming. | namespaces from stack trace |
| `SaveableFromNode exception: System.ArgumentException: Can't load abstract class Verse.MapComponent` | exception | Broken map component leftover from removed mod. | — |
| `%s threw exception in WorkGiver %s: %s: %s` | exception | Pawn failed to get specific work. Identify which mod relates to the WorkGiver. | — |

#### ERROR CLASSIFIERS

| Pattern | Type | Explanation | Offending Mod |
|---|---|---|---|
| `Children: Settings: Hybrid: %s %s not found!` | error | Species set by Children mod not found — mod removed or broken. Check Children settings. | Children mod |
| `Children: Settings: Species not found(%s)! (%s)` | error | Species set by Children mod not found. Check Children settings. | Children mod |
| `Could not find a type named %s.%s` | error | Mod using non-existent type — likely misconfigured or outdated. | capture[1] (namespace) |
| `Could not load reference to %s named %s` | error | Definition reference can't load — required mod missing or item removed. | capture[2] (ref name) |
| `Could not resolve cross-reference: No %s named %s found to give to %s %s` | error | Definition can't be found — required mod inactive or outdated. | — |
| `Could not resolve reference to object with loadID %s of type %s` | error | Save file may be broken — object from removed/updated mod. | capture[3] (parent) |
| `%s %s is not defined in any loaded mods.` | error | Mod using undefined definition — outdated or missing required mod. | — |
| `Failed to find any textures at %s while constructing Multi` | error | Mod can't find its own textures — may cause visual glitches. | — |
| `Tried to set ThingCount stack count to -%i. thing=%s%i` | error | Mod setting invalid stack size. | — |
| `Null key while loading dictionary of %s and %s. label=%s` | error | Mod loading dictionary with null keys — XML config error. | capture[2] namespace prefix |
| `Mod %s <packageId> (%s) is not in valid format.` | error | Mod misconfigured package ID — usually ignorable. | capture[1] (mod name) |
| `[%s] Patches on methods annotated as Obsolete were detected` | error | Mod patching old methods — likely outdated. | capture[1] (mod name) |
| `An error occurred while starting an error recover job.` | error | Check the error preceding this one — this error itself is uninformative. | — |
| `Error in %s: Specified cast is not valid.` | error | Unexpected situation — mod conflict or poor programming. | — |
| `Translation data for language %s has %i errors.` | error | Translation for language is outdated. | — |
| `Could not find type named %s.%s from node` | error | Mod using non-existent type — misconfigured or outdated. | capture[1] (namespace) |
| `Could not find class %s.%s while resolving node %s. Trying to use Verse.MapComponent instead.` | error | Map component class missing — mod removed or save file is old. | capture[1] (namespace) |
| `XML error: %s doesn't correspond to any field in type %s.` | error | Mod configured poorly, or RimWorld/mod is outdated. | — |
| `XML error: Duplicate XML node name %s in this XML block: <%s><defName>%s</defName>` | error | Mod introducing or overriding `%s` is set up incorrectly. | capture[3] (defName) |
| `XML format error: List item found with name that is not <li>` | error | Mod XML written wrong — bad modding or invalid patch (mod conflict). | — |
| `Tried to use an uninitialized DefOf of type %s. ... curParent=%s.%s+%s` | error | Mod not set up correctly. | capture[2] (namespace) |
| `Failed to find %s named %s. There are %i defs of this type loaded.` | error | Cross-reference to a named def failed — often a compat patch pointing at a def renamed or removed in an update. **Important:** The log often prints "Possible Matches" with `[Source: ModName]` lines immediately below — read those to identify which mod owns the broken reference. | def name in capture[2] |

#### WARNING CLASSIFIERS

| Pattern | Explanation |
|---|---|
| `Add a delegate to SceneManager.sceneLoaded instead` | Outdated Unity pattern — minor. |
| `(%s) burst fire shot count is same or higher than auto fire` | Weapon mod configuration issue. |
| `Capacity %s does not have any %s associated with it.` | Capacity definition issue. |
| `%s :: Tag %s is not associated with any pawnCapacity.` | Tag association missing — may be intentional. |
| `Could not resolve cross-reference to %s named %s` | Definition missing — mod or dependency absent. |
| `Couldn't find exact match for backstory` | Backstory from missing/removed mod. |
| `[HugsLib][warn] Missing enum setting labels for enum %s` | HugsLib settings label missing. |
| `Running incremental garbage collection` | Performance warning — heavy mod load. |
| `Parsed %f as int.` | Type parsing issue in a mod. |
| `Key binding conflict: %s and %s are both bound to %s.` | Two mods binding the same key. |
| `%s loaded in %s` | General load message — usually ignorable. |
| `Reached max messages limit. Stopping logging to avoid spam.` | **Important** — log was truncated. Issues may be hidden. |
| `%s %s has no thingClass.` | Misconfiguration in another mod — mod name can't be identified. |
| `Config error in %s: %s has CompProperties with null compClass.` | Null component class — mod config error. |
| `Config error in %s: defName %s should only contain letters, numbers, underscores, or dashes.` | defName formatting issue. |
| `Patched jump instruction at %i` | Harmony IL patching — usually harmless. |
| `%s pathing to destroyed thing %s` | Runtime pathing to deleted entity. |
| `ResearchPal :: Research %s does not belong to any mod` | ResearchPal tree issue. |
| `ResearchPal :: %s has a lower techlevel than its prerequisites` | ResearchPal config warning. |
| `ResearchPal :: redundant prerequisites for %s: %s` | ResearchPal tree redundancy. |
| `ResearchTree :: redundant prerequisites for %s: %s` | ResearchTree redundancy. |
| `%s started 10 jobs in 10 ticks.` | Pawn AI loop — likely mod conflict. |
| `Type %s probably needs a StaticConstructorOnStartup attribute` | Mod initialization order issue. |
| `Translation data for language English has %i errors.` | English translation outdated. |
| `Tried to discard a world pawn %s.` | World pawn management issue. |
| `TryMakePreToilReservations() returned false for a non-queued job` | Job reservation failure — mod conflict likely. |
| `Config error in %s: %s %s has 0 commonality.` | Spawn table config issue. |
| `NQoL [W] - Failed to patch: %s` | Niilo's QoL couldn't apply a grouping patch — another mod already handled that def. Usually benign; check NQoL settings. |
| `NQoL [W] - Failed to group: %s` | Niilo's QoL couldn't group a building — another mod made it stuffable or grouped it first. Cosmetic conflict. |
| `NQoL [W] - Found no storage filters to patch` | Another mod removed default storage filters before NQoL could act. May mean NQoL's filter feature is non-functional. |
| `NQoL [W] - Potentially harmful type or method detected: %s has patches: 'Prefix' (Destructive prefix)` | A mod is using a destructive Harmony prefix on a core method. Identified mods: Vanilla Expanded Framework, ReGrowth 2, Performance Optimizer. Not necessarily breaking but suppresses error logging. |
| `NQoL [W] - %s version has changed!` | Niilo's QoL detected a version change in a mod it's compatible with. Flagging for re-testing — usually safe to ignore unless issues appear. |

#### KNOWN REDUNDANCY DATABASE

Cross-reference the active mod list against this table during Phase 1 mod extraction. If **both** mods in a pair are present, add an entry to `redundancies[]`. Match on packageId when available; fall back to display name. Entries marked `(settings)` mean the overlap can be resolved in mod settings rather than requiring removal.

| Mod A (name / packageId) | Mod B (name / packageId) | Overlapping Feature | Recommendation |
|---|---|---|---|
| Niilo's QoL / `Niilo007.NiilosQoL` | No Default Shelf Storage / `FSF.NoDefaultShelfStorage` | Default storage filters on shelves | Disable shelf filter feature in NQoL settings (settings) |
| Niilo's QoL / `Niilo007.NiilosQoL` | Tech Advancing / any | Colony tech level increases with research | Disable tech level feature in NQoL settings (settings) |
| Niilo's QoL / `Niilo007.NiilosQoL` | MinifyEverything / `com.github.minifyeverything` | Allow minification of more buildings | Disable minification in NQoL settings (settings) |
| Niilo's QoL / `Niilo007.NiilosQoL` | Floors Are (Almost) Worthless / any | Floor wealth reduction / configuration | Disable floor wealth feature in NQoL settings (settings) |
| Niilo's QoL / `Niilo007.NiilosQoL` | Realistic Rooms Rewritten / `owlchemist.realisticroomsrewritten` | Room size requirements | Disable room size feature in NQoL settings (settings) |
| Niilo's QoL / `Niilo007.NiilosQoL` | FrozenSnowFox Tweaks / `FSF.FrozenSnowFoxTweaks` | Wild animal reproduction, egg deterioration fix | Disable overlapping features in NQoL or FSF Tweaks settings (settings) |
| Niilo's QoL / `Niilo007.NiilosQoL` | Tweaks Galore / `Owlchemist.TweaksGalore` | Skilled stonecutting, torch refuel, deconstruct return, and more | Systematically disable duplicates in NQoL and Tweaks Galore settings (settings) |
| Tweaks Galore / `Owlchemist.TweaksGalore` | FrozenSnowFox Tweaks / `FSF.FrozenSnowFoxTweaks` | Growable Ambrosia, growable grass, growable mushrooms, wild reproduction | Disable duplicates in one mod's settings (settings) |
| Yayo's Animation / `com.yayo.yayoAni` | Melee Animation / `co.uk.epicguru.meleeanimation` | Pawn weapon draw and melee combat animation | Use one. Melee Animation is more feature-rich; Yayo's is lighter. They can conflict on pawn renderer patches. |
| Job In Bar / `Dark.JobInBar` | Useful Marks / `Andromeda.UsefulMarks` | Labels and icons on the colonist bar | Disable bar labels in one mod's settings — both mods flag this themselves (settings) |
| ResearchPal / any | ResearchTree / any | Research tree visualizer UI | Use only one research tree visualizer. They are mutually exclusive UI replacements. |
| ResearchPal / any | Clean Research Sort / `Leo.CleanResearchSort` | Research tree layout sorting | Clean Research Sort is designed to work with ResearchPal/ResearchTree — not redundant, but check for duplicate sorting behavior if using all three. |
| Performance Optimizer / `taranchuk.performanceoptimizer` | Rim of Madness - Optimizer / any | General performance patching | Check changelogs — overlapping optimizations on the same methods can conflict. |
| Color Coded Mood Bar / `Mlie.ColorCodedMoodBar` | RimHUD / `Jaxe.RimHUD` | Mood display on colonist bar | Both modify the colonist bar mood indicator. Disable mood bar in one (settings) |
| Dubs Mint Menus / `DubsMintMenus` | Vanilla UI Expanded / `vanillaexpanded.vUIe` | Context menus and bill management UI | Overlapping UI replacements for bills/menus — test together; disable duplicate features if both active. |
| Simple Sidearms / `PeteTimesSix.SimpleSidearms` | Dual Wield / any | Carrying and switching multiple weapons | Fundamental feature overlap — choose one or confirm the two mods are explicitly designed to coexist. |

> **Note:** This database is seeded from commonly reported community conflicts and observations from NQoL's own overlap notices. It will not catch every redundancy — treat it as a starting point, not an exhaustive list. Entries are continuously improvable as new conflicts are discovered.

---

### Phase 4 — Extract Offending Mod Namespaces from Stack Traces

For unknown exceptions, scan the stack trace for `at (optional qualifiers) Namespace.Something` patterns. Filter out known vanilla namespaces:
- `System`, `Verse`, `RimWorld`, `UnityEngine`, `Unity`, `Mono`, `Microsoft`

The remaining namespaces are candidate offending mods. De-duplicate them. These are **mod IDs / namespaces**, not necessarily display names — note this to the user.

---

### Phase 5 — Produce Structured Report

Output the following format:

---

## 🛸 RimWorld Log Analysis

**RimWorld Version:** `[version]`  
**HugsLib Version:** `[version]`  
**Mods Loaded:** `[count]`  
**Log Truncated:** Yes/No *(note if `max messages limit` warning was detected)*

---

### 📦 Active Mods
List all detected mods with name and packageId. Group into:
- Vanilla / DLC
- Harmony & framework mods (HugsLib, etc.)
- Content mods

---

### 🔴 Critical — Exceptions
*Exceptions halt code execution and often cause cascading failures in unrelated mods.*

For each unique exception (deduplicated, show count if repeated):
- **[Nx]** Exception message (truncated to first meaningful line)
  - **Phase:** Startup / Runtime
  - **Explanation:** [from classifier or general guidance]
  - **Likely culprit(s):** [mod names/namespaces if identifiable]
  - **Recommendation:** [specific action]

---

### 🟠 Errors at Startup
*Errors during loading usually mean broken, outdated, or conflicting mods. Fix these before playing.*

For each unique error (deduplicated, show count):
- **[Nx]** Error message
  - **Explanation:** [from classifier]
  - **Likely culprit(s):** [mod if identified]
  - **Recommendation:** [specific action]

---

### 🟡 Errors & Warnings at Runtime
*Runtime errors appear after a save is loaded. They may corrupt save files over time.*

Same format as above.

---

### 🔁 Redundant / Overlapping Mods

*Only include this section if `redundancies[]` is non-empty. If empty, omit the section entirely.*

*Having two mods that do the same thing wastes performance, can cause unexpected behavior when both fire, and makes debugging harder. These are not errors — they won't crash your game — but cleaning them up improves stability and clarity.*

For each entry in `redundancies[]`:

| Feature | Mod A | Mod B | Source | Recommendation |
|---|---|---|---|---|
| [feature] | [mod name] | [mod name] | NQoL / COMPAT notice / Known DB | [action — settings or removal] |

Group entries by source:
- **🟡 Developer-confirmed** — flagged by NQoL notices or a mod's own COMPAT output. High confidence.
- **📋 Database match** — both mods detected from the Known Redundancy Database. High confidence.

After the table, add a short note:
> *These overlaps won't break your game but may cause double-application of effects or wasted CPU. Disable the overlapping feature in one mod's settings where possible before considering removal.*

---

### 📋 Summary & Priority Actions

Numbered list of recommended actions in priority order:
1. Most critical fixes first (exceptions > startup errors > runtime errors)
2. Group related issues (e.g., "3 errors all point to ModX being outdated")
3. Include specific mod names whenever identified
4. Note if issues are likely benign vs. save-threatening
5. If `redundancies[]` is non-empty: add a final item — "X mod pairs with overlapping functionality detected — see Redundancy section. No crash risk, but worth cleaning up."

---

### ⚠️ Important Context for Users

Always include this guidance:
- Exceptions are worse than errors — they stop code from running and can break unrelated mods
- Startup errors should be resolved before playing — they often mean missing/broken mods
- Don't save after runtime errors — the save file may become corrupted
- If you need to remove mods from an ongoing save, only remove pure QoL mods safely
- Use developer mode so the console appears on errors during play

---

## Handling Unknown Issues

If a log line doesn't match any classifier:
- Still report it if it's an exception (always report exceptions)
- For errors: report if it matches common error patterns (Could not find, XML error, etc.)
- Mark unknown items clearly so the user knows it's not in the database
- For unknown exceptions: always extract and show the offending namespaces

## Handling Large Logs

If the log is very long (>1000 lines):
- Prioritize startup errors and exceptions
- Deduplicate aggressively (count repetitions)
- Focus the report on actionable items
- Note if the log hit the message limit (content may be cut off)

